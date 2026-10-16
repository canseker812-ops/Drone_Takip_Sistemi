import serial
import time
import cv2
from ultralytics import YOLO

# ==========================================
# PID KONTROLCÜ SINIFI
# ==========================================
class PID:
    """Basit PID kontrolcü. Girdi: piksel hatası. Çıktı: adım sayısı."""
    def __init__(self, kp, ki=0.0, kd=0.0, cikis_siniri=20, integral_siniri=100.0, turev_filtre=0.3):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.cikis_siniri = cikis_siniri        # çıkış -sınır ile +sınır arasında kalır
        self.integral_siniri = integral_siniri  # anti-windup: integral şişmesin
        self.turev_filtre = turev_filtre        # 0-1 arası, küçük = daha yumuşak türev
        self.sifirla()

    def sifirla(self):
        """Hedef kaybı, durdurma ve acil durdurmada çağrılır."""
        self.integral = 0.0
        self.onceki_hata = 0.0
        self.onceki_zaman = None
        self.turev = 0.0

    def hesapla(self, hata, dt=None):
        # dt verilmezse gerçek zamandan hesapla
        simdi = time.perf_counter()
        if dt is None and self.onceki_zaman is not None:
            dt = simdi - self.onceki_zaman

        oran = self.kp * hata
        integral_terimi = 0.0
        turev_terimi = 0.0

        # İlk çağrıda dt yok, çok küçük dt ise türev patlar: ikisinde de atla
        if dt is not None and dt > 1e-3:
            self.integral += hata * dt
            self.integral = max(-self.integral_siniri, min(self.integral_siniri, self.integral))
            ham_turev = (hata - self.onceki_hata) / dt
            self.turev = (1 - self.turev_filtre) * self.turev + self.turev_filtre * ham_turev
            integral_terimi = self.ki * self.integral
            turev_terimi = self.kd * self.turev

        cikis = oran + integral_terimi + turev_terimi
        cikis = max(-self.cikis_siniri, min(self.cikis_siniri, cikis))

        self.onceki_hata = hata
        self.onceki_zaman = simdi
        return cikis
# ==========================================

# 1. BAŞLANGIÇ AYARLARI
model = YOLO(r"C:\Users\Gebisis\Desktop\DroneTakip\Target-Tracking-Challenge\runs\detect\pars_v2_yolo11n_e50\weights\best.pt")
kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Kamerayı başlat

# X ve Y eksenleri için iki ayrı PID "beyni" oluşturuyoruz
pid_x = PID(kp=0.5, ki=0.01, kd=0.1, cikis_siniri=50)
pid_y = PID(kp=0.5, ki=0.01, kd=0.1, cikis_siniri=50)

if not kamera.isOpened():
    print("Kamera açılamadı.")
    exit()

try:
    mikrodenetleyici = serial.Serial("COM8", 9600, timeout=1)
    time.sleep(2)
    print("Mikrodenetleyiciye bağlantı kuruldu.")
except:
    print("Mikrodenetleyici Bulunamadı! Kabloyu ve portu kontrol et.")

# 2. ANA DÖNGÜ
while True:
    ok, frame = kamera.read() # Kameradan anlık 1 kare fotoğraf al
    if not ok:
        print("Kare okunamadı.")
        break
        
    # 3. YOLO ANALİZİ VE ÇİZİM
    sonuc = model(frame, conf=0.05, verbose=False) # Fotoğrafı yapay zekaya ver ve hedefleri bul
    cizili = sonuc[0].plot() # Hedeflerin etrafına kutu çizilmiş haliyle fotoğrafı geri al

    yukseklik, genislik, renk = frame.shape # Fotoğrafın piksel boyutlarını öğren
    ekran_cx = genislik // 2 # Ekranın X (sağ-sol) merkezini hesapla
    ekran_cy = yukseklik // 2 # Ekranın Y (yukarı-aşağı) merkezini hesapla
    cv2.circle(cizili, (ekran_cx, ekran_cy), 5, (255, 0, 0), -1) # Ekranın tam ortasına MAVİ nokta koy

    # 4. DURUM KONTROLÜ
    kutu_sayisi = len(sonuc[0].boxes) # Ekranda kaç tane hedef (kutu) var say

    if kutu_sayisi > 0:
        # 5. HATA HESAPLAMA
        for kutu in sonuc[0].boxes:
            x1, y1, x2, y2 = map(int, kutu.xyxy[0]) # Bulunan hedefin köşe piksellerini al
            cx = (x1 + x2) // 2 # Hedefin kendi X merkezini bul
            cy = (y1 + y2) // 2 # Hedefin kendi Y merkezini bul

            cv2.circle(cizili, (cx, cy), 5, (0, 0, 255), -1) # Hedefin tam ortasına KIRMIZI nokta koy

            hata_x = cx - ekran_cx # Kırmızı nokta mavi noktadan sağa/sola ne kadar uzak hesapla
            hata_y = cy - ekran_cy # Kırmızı nokta mavi noktadan yukarı/aşağı ne kadar uzak hesapla
                    
            # 6. ÖLÜ BÖLGE VE PID HESABI
            olu_bolge = 30 # Motorların titremesini önlemek için 30 piksellik tolerans tanı
            
            if abs(hata_x) < olu_bolge: # Eğer X hatası -30 ile +30 arasındaysa...
                hata_x = 0
                pid_x.sifirla() # Hedef merkezdeyse PID hafızasını temizle
                adim_x = 0
            else:
                adim_x = int(pid_x.hesapla(hata_x)) # Hata varsa PID ile atılacak adımı hesapla

            if abs(hata_y) < olu_bolge: # Eğer Y hatası -30 ile +30 arasındaysa...
                hata_y = 0
                pid_y.sifirla()
                adim_y = 0
            else:
                adim_y = int(pid_y.hesapla(hata_y))

            # Ekrana yazıları ekle
            cv2.putText(cizili, "Durum: TAKIP", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(cizili, f"Adim X: {adim_x} | Adim Y: {adim_y}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # 7. ARDUINO'YA VERİ GÖNDERME
            veri_paketi = f"<{adim_x},{adim_y}>" # Artık "hata" değil "adım sayısı" yolluyoruz
            print(f"Durum: TAKİP | Gönderilen: {veri_paketi}")
            try:
                mikrodenetleyici.write(veri_paketi.encode('utf-8'))
            except:
                pass
    else:
        # 8. ARAMA DURUMU
        cv2.putText(cizili, "Durum: ARANIYOR", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Hedef kaybolduysa PID'lerin hafızasını sıfırla ki motorlar saçmalamasın
        pid_x.sifirla()
        pid_y.sifirla()
        
        durum_paketi = "<999,999>"
        print(f"Durum: ARANIYOR | Gönderilen: {durum_paketi}")

        try:
            mikrodenetleyici.write(durum_paketi.encode('utf-8'))
        except:
            pass

    # 9. EKRANDA GÖSTERME VE ÇIKIŞ
    cv2.imshow("YOLO", cizili) # Üzerinde çizimler olan son fotoğrafı ekranda pencere olarak aç

    if cv2.waitKey(1) & 0xFF == ord("q"): # Eğer klavyeden 'q' tuşuna basılırsa...
        break # ...sonsuz döngüyü kır ve aşağı in

# 10. TEMİZLİK
kamera.release() # Kamerayı başka programlar da kullanabilsin diye serbest bırak
cv2.destroyAllWindows() # Açılan YOLO penceresini kapat