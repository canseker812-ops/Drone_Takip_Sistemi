import serial
import time

import cv2
from ultralytics import YOLO

# 1. BAŞLANGIÇ AYARLARI
model = YOLO(r"C:\Users\Gebisis\Desktop\DroneTakip\Target-Tracking-Challenge\runs\detect\pars_v2_yolo11n_e50\weights\best.pt") # Modeli RAM'e yükle
kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Kamerayı başlat

if not kamera.isOpened():
    print("Kamera açılamadı.")
    exit()

try:
    mikrodenetleyici =serial.Serial("COM8",9600,timeout=1)
    time.sleep(2)
    print("Mikrodeneyleyiciye bağlantı kuruldu.")
except:
    print("Mikrodenetleyici Bulunamadı!Kabloyu ve portu kontrol et.")

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
        print("Durum : TAKİP") # Hedef bulundu, takip moduna geç
        cv2.putText(cizili, "Durum: TAKİP", (20,40),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2)
        cv2.putText(cizili, f"Hata X: {hata_x} | Hata Y: {hata_y}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 5. HATA HESAPLAMA
        for kutu in sonuc[0].boxes:
            x1, y1, x2, y2 = map(int, kutu.xyxy[0]) # Bulunan hedefin köşe piksellerini al
            cx = (x1 + x2) // 2 # Hedefin kendi X merkezini bul
            cy = (y1 + y2) // 2 # Hedefin kendi Y merkezini bul

            cv2.circle(cizili, (cx, cy), 5, (0, 0, 255), -1) # Hedefin tam ortasına KIRMIZI nokta koy

            hata_x = cx - ekran_cx # Kırmızı nokta mavi noktadan sağa/sola ne kadar uzak hesapla
            hata_y = cy - ekran_cy # Kırmızı nokta mavi noktadan yukarı/aşağı ne kadar uzak hesapla
            
            # 6. ÖLÜ BÖLGE (DEADZONE)
            olu_bolge = 30 # Motorların titremesini önlemek için 30 piksellik tolerans tanı
            if abs(hata_x) < olu_bolge: # Eğer X hatası -30 ile +30 arasındaysa...
                hata_x = 0 # ...hatayı 0 kabul et (motor X dönmesin)
            if abs(hata_y) < olu_bolge: # Eğer Y hatası -30 ile +30 arasındaysa...
                hata_y = 0 # ...hatayı 0 kabul et (motor Y dönmesin)

            hata_paketi = f"<{hata_x},{hata_y}>" # Hataları terminalde göster
            print(hata_paketi)
            try:
                mikrodenetleyici.write(hata_paketi.encode('utf-8'))
            except:
                pass
    else:
        # 7. ARAMA DURUMU
        print("Durum : ARANIYOR") # Hedef yok, arama moduna geç
        cv2.putText(cizili, "Durum: ARANIYOR", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        hata_x = 999 # Arduino'nun "hedef yok" durumunu anlaması için şifreli X hatası
        hata_y = 999 # Arduino'nun "hedef yok" durumunu anlaması için şifreli Y hatası
        durum_paketi = f"<{hata_x},{hata_y}>"
        print(durum_paketi)

        try:
            mikrodenetleyici.write(durum_paketi.encode('utf-8'))
        except:
            pass

    # 8. EKRANDA GÖSTERME VE ÇIKIŞ
    cv2.imshow("YOLO", cizili) # Üzerinde çizimler olan son fotoğrafı ekranda pencere olarak aç

    if cv2.waitKey(1) & 0xFF == ord("q"): # Eğer klavyeden 'q' tuşuna basılırsa...
        break # ...sonsuz döngüyü kır ve aşağı in

# 9. TEMİZLİK
kamera.release() # Kamerayı başka programlar da kullanabilsin diye serbest bırak
cv2.destroyAllWindows() # Açılan YOLO penceresini kapat