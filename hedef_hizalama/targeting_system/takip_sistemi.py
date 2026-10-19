import time

import cv2

import config
from pid import PID
from serial_link import SeriBaglanti

# Durumlar
BEKLEMEDE = "BEKLEMEDE"      # açılış, Durdur sonrası: motor oynamaz
ARANIYOR = "ARANIYOR"        # hedef yok: yaw'da tarama paketi
TAKIP = "TAKIP"              # hedef görülüyor, motor hizalıyor
HIZALI = "HIZALI"            # hedef ölü bölgede, motor duruyor
ACIL_DURDUR = "ACIL_DURDUR"  # her şey durdu, sadece reset çıkarır
HATA = "HATA"                # kamera/model sorunu, hata_mesaji'na bak


class TakipSistemi:
    """Kamera + YOLO + PID + UART. Dashboard ve main.py bu sınıfı kullanır.
    Her adim() çağrısı BİR kare işler."""

    def __init__(self, tespitci=None, kamera=None, seri=None):
        self.durum = BEKLEMEDE
        self.hata_mesaji = ""
        self.kayip = config.KAYIP_ESIGI   # başlangıçta hedef yok sayılır
        self.son_gonderim = 0.0
        self.hata_x = self.hata_y = 0
        self.adim_x = self.adim_y = 0
        self.mcu_cevap = ""
        self.pid_x = PID(config.KP, config.KI, config.KD, cikis_siniri=config.MAX_ADIM)
        self.pid_y = PID(config.KP, config.KI, config.KD, cikis_siniri=config.MAX_ADIM)

        # Model
        self.tespitci = tespitci
        if self.tespitci is None:
            try:
                from detector import Tespitci
                self.tespitci = Tespitci()
            except Exception as hata:
                self._hata(f"Model yüklenemedi: {hata}")

        # Kamera
        self.kamera = kamera
        if self.kamera is None:
            self.kamera = cv2.VideoCapture(config.KAMERA_INDEKSI, cv2.CAP_DSHOW)
        if not self.kamera.isOpened():
            self._hata("Kamera açılamadı")

        # Seri port (bağlanamazsa sistem kamera modunda çalışmaya devam eder)
        self.seri = seri if seri is not None else SeriBaglanti()

    # ---------- Dışarıdan çağrılan kontroller ----------
    def baslat(self):
        if self.durum == BEKLEMEDE:
            self.kayip = config.KAYIP_ESIGI   # hemen arama moduna gir
            self.durum = ARANIYOR

    def durdur(self):
        if self.durum in (ARANIYOR, TAKIP, HIZALI):
            self._pid_sifirla()
            self._gonder("<0,0>", zorla=True)
            self.durum = BEKLEMEDE

    def acil_durdur(self):
        """Her durumda çalışır: takip biter, motor serbest bırakılır."""
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

    # ---------- Ana işlem: bir kare ----------
    def adim(self):
        """(çizilmiş kare, bilgi sözlüğü) döndürür. Kare okunamazsa kare None olur."""
        if self.durum == HATA:
            return None, self._bilgi()

        ok, kare = self.kamera.read()
        if not ok:
            if self.durum != ACIL_DURDUR:
                self._hata("Kare okunamadı")
            return None, self._bilgi()

        yukseklik, genislik = kare.shape[:2]
        ekran_cx, ekran_cy = genislik // 2, yukseklik // 2
        cizili = kare.copy()
        self.hata_x = self.hata_y = self.adim_x = self.adim_y = 0

        # Sadece çalışan durumlarda tespit yapılır
        if self.durum in (ARANIYOR, TAKIP, HIZALI):
            cizili, hedef = self.tespitci.bul(kare)
            if hedef is not None:
                self._hedefi_takip_et(hedef, ekran_cx, ekran_cy, cizili)
            else:
                self._hedef_kayboldu()

        cv2.circle(cizili, (ekran_cx, ekran_cy), 5, (255, 0, 0), -1)  # mavi: ekran merkezi

        for satir in self.seri.oku():
            self.mcu_cevap = satir
        return cizili, self._bilgi()

    # ---------- İç işler ----------
    def _hedefi_takip_et(self, hedef, ekran_cx, ekran_cy, cizili):
        self.kayip = 0
        cx, cy = hedef
        cv2.circle(cizili, (cx, cy), 5, (0, 0, 255), -1)  # kırmızı: hedef merkezi

        self.hata_x = cx - ekran_cx
        self.hata_y = cy - ekran_cy

        # PID ham hata ile çalışır, ölü bölge sadece çıkışa uygulanır
        adim_x = config.YAW_YONU * self.pid_x.hesapla(self.hata_x)
        adim_y = config.PITCH_YONU * self.pid_y.hesapla(self.hata_y)
        if abs(self.hata_x) < config.OLU_BOLGE:
            adim_x = 0
            self.pid_x.integral = 0
        if abs(self.hata_y) < config.OLU_BOLGE:
            adim_y = 0
            self.pid_y.integral = 0
        self.adim_x = int(round(adim_x))
        self.adim_y = int(round(adim_y))

        self.durum = HIZALI if (self.adim_x == 0 and self.adim_y == 0) else TAKIP
        self._gonder(f"<{self.adim_x},{self.adim_y}>")

    def _hedef_kayboldu(self):
        self.kayip = min(self.kayip + 1, config.KAYIP_ESIGI)
        if self.kayip >= config.KAYIP_ESIGI:
            if self.durum != ARANIYOR:
                self._pid_sifirla()
            self.durum = ARANIYOR
            self._gonder("<999,999>")

    def _gonder(self, paket, zorla=False):
        """zorla=False ise en fazla GONDERIM_ARALIGI'nda bir paket gider."""
        simdi = time.perf_counter()
        if not zorla and (simdi - self.son_gonderim) < config.GONDERIM_ARALIGI:
            return
        self.seri.gonder(paket)
        self.son_gonderim = simdi

    def _pid_sifirla(self):
        self.pid_x.sifirla()
        self.pid_y.sifirla()

    def _hata(self, mesaj):
        print("HATA:", mesaj)
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