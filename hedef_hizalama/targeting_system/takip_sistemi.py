import time
import cv2
import config
from pid import PID
from serial_link import SeriBaglanti

# Sistem Durumları
BEKLEMEDE = "BEKLEMEDE"
ARANIYOR = "ARANIYOR"
TAKIP = "TAKIP"
HIZALI = "HIZALI"
ACIL_DURDUR = "ACIL_DURDUR"
HATA = "HATA"

class TakipSistemi:
    def __init__(self, tespitci=None, kamera=None, seri=None):
        self.durum = BEKLEMEDE
        self.hata_mesaji = ""
        self.kayip = config.KAYIP_ESIGI
        self.son_gonderim = 0.0
        self.hata_x = self.hata_y = 0
        self.adim_x = self.adim_y = 0
        self.mcu_cevap = ""
        
        self.pid_x = PID(config.KP, config.KI, config.KD, cikis_siniri=config.MAX_ADIM)
        self.pid_y = PID(config.KP, config.KI, config.KD, cikis_siniri=config.MAX_ADIM)

        self.tespitci = tespitci
        if self.tespitci is None:
            try:
                from detector import Tespitci
                self.tespitci = Tespitci()
            except Exception as hata:
                self._hata(f"Model yüklenemedi: {hata}")

        self.kamera = kamera
        if self.kamera is None:
            self.kamera = cv2.VideoCapture(config.KAMERA_INDEKSI, cv2.CAP_DSHOW)
        if not self.kamera.isOpened():
            self._hata("Kamera açılamadı")

        self.seri = seri if seri is not None else SeriBaglanti()

    def baslat(self):
        if self.durum == BEKLEMEDE:
            self.kayip = config.KAYIP_ESIGI
            self.durum = ARANIYOR
            # Başlatıldığı an hedef kadrajda yoksa boş durmasın, taramaya başlasın
            self._gonder("<999,999>", zorla=True)

    def durdur(self):
        if self.durum in (ARANIYOR, TAKIP, HIZALI):
            self._pid_sifirla()
            self._gonder("<0,0>", zorla=True)
            self.durum = BEKLEMEDE

    def acil_durdur(self):
        # Sensörü kapatmıyoruz, sadece aktüatörleri acil kilitliyoruz
        self._pid_sifirla()
        self._gonder("<E>", zorla=True)
        self.durum = ACIL_DURDUR

    def reset(self):
        if self.durum == ACIL_DURDUR:
            self._gonder("<R>", zorla=True)
            self.durum = BEKLEMEDE

    def kapat(self):
        self._gonder("<0,0>", zorla=True)
        self.seri.kapat()
        if self.kamera is not None:
            self.kamera.release()

    def adim(self):
        if self.durum == HATA:
            return None, self._bilgi()

        ok, kare = self.kamera.read()
        if not ok:
            if self.durum != ACIL_DURDUR:
                self._hata("Kamera karesi okunamadı")
            return None, self._bilgi()

        yukseklik, genislik = kare.shape[:2]
        ekran_cx, ekran_cy = genislik // 2, yukseklik // 2
        cizili = kare.copy()
        
        self.hata_x = self.hata_y = self.adim_x = self.adim_y = 0

        if self.durum in (ARANIYOR, TAKIP, HIZALI):
            cizili, hedef = self.tespitci.bul(kare)
            if hedef is not None:
                self._hedefi_takip_et(hedef, ekran_cx, ekran_cy, cizili)
            else:
                self._hedef_kayboldu()

        cv2.circle(cizili, (ekran_cx, ekran_cy), 5, (255, 0, 0), -1)

        for satir in self.seri.oku():
            self.mcu_cevap = satir
            
        return cizili, self._bilgi()

    def _hedefi_takip_et(self, hedef, ekran_cx, ekran_cy, cizili):
        self.kayip = 0
        cx, cy = hedef
        cv2.circle(cizili, (cx, cy), 5, (0, 0, 255), -1)

        hata_x = cx - ekran_cx
        hata_y = cy - ekran_cy

        # PID windup olmasın diye hedef ölü bölgedeyse integral hesabını sıfırlıyoruz
        if abs(hata_x) < config.OLU_BOLGE:
            hata_x = 0
            self.pid_x.sifirla()
            
        if abs(hata_y) < config.OLU_BOLGE:
            hata_y = 0
            self.pid_y.sifirla()

        self.hata_x = hata_x
        self.hata_y = hata_y

        self.adim_x = int(round(config.YAW_YONU * self.pid_x.hesapla(self.hata_x)))
        self.adim_y = int(round(config.PITCH_YONU * self.pid_y.hesapla(self.hata_y)))

        yeni_durum = HIZALI if (self.adim_x == 0 and self.adim_y == 0) else TAKIP
        
        # Hedefe kilitlendiysek (HIZALI), timeout süresini beklemeden dur komutunu basıyoruz
        gonderim_zorunlu = (yeni_durum == HIZALI and self.durum == TAKIP)
        self.durum = yeni_durum
        
        self._gonder(f"<{self.adim_x},{self.adim_y}>", zorla=gonderim_zorunlu)

    def _hedef_kayboldu(self):
        self.kayip = min(self.kayip + 1, config.KAYIP_ESIGI)
        if self.kayip >= config.KAYIP_ESIGI:
            if self.durum != ARANIYOR:
                self._pid_sifirla()
                self.durum = ARANIYOR
                # Paket kaybı (drop) yaşanmaması için zorla gönderiliyor
                self._gonder("<999,999>", zorla=True)

    def _gonder(self, paket, zorla=False):
        simdi = time.perf_counter()
        if not zorla and (simdi - self.son_gonderim) < config.GONDERIM_ARALIGI:
            return
        self.seri.gonder(paket)
        self.son_gonderim = simdi

    def _pid_sifirla(self):
        self.pid_x.sifirla()
        self.pid_y.sifirla()

    def _hata(self, mesaj):
        print("SİSTEM HATASI:", mesaj)
        self.hata_mesaji = mesaj
        self.durum = HATA

    def _bilgi(self):
        return {
            "durum": self.durum,
            "hata_x": self.hata_x,
            "hata_y": self.hata_y,
            "adim_x": self.adim_x,
            "adim_y": self.adim_y,
            "seri_bagli": self.seri.bagli,
            "mcu_cevap": self.mcu_cevap,
            "hata_mesaji": self.hata_mesaji,
        }