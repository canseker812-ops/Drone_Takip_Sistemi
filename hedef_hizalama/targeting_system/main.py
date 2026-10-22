import cv2
from takip_sistemi import TakipSistemi

# Geliştirici: Şeker Can Şeker
# NOT: Streamlit dashboard olmadan sadece saf donanım ve model testi yapmak isterseniz 
# sistemi bu dosyadan hızlıca ayağa kaldırabilirsiniz. (Sıfır UI yükü)

def main():
    sistem = TakipSistemi()
    sistem.baslat()
    
    print("Marmara Rover Otonom Takip - Geliştirici Modu Başladı.")
    print("Çıkmak için kameradayken 'q', Acil Durdurma için 'e', Reset için 'r' tuşuna basın.")

    try:
        while True:
            # İşlemciyi serbest bırakmak ve OpenCV pencere tamponunu boşaltmak için
            tus = cv2.waitKey(1) & 0xFF
            
            if tus == ord('q'):
                break
            elif tus == ord('e'):
                sistem.acil_durdur()
                print(">>> E-STOP TETİKLENDİ! Motorlar kilitlendi.")
            elif tus == ord('r'):
                sistem.reset()
                sistem.baslat()
                print(">>> SİSTEM SIFIRLANDI. Taramaya geçiliyor.")

            kare, bilgi = sistem.adim()
            
            if kare is None:
                print("Kamera akışı koptu, çıkılıyor...")
                break

            # Sadece hedef varken veya arıyorken normal çerçeveyi göster
            if bilgi["durum"] != "ACIL_DURDUR":
                cv2.imshow("Marmara Rover - Raw Test", kare)
            else:
                # Acil durdurmada ekranı kırmızı kilitli uyarı ile ez
                kilitli = kare.copy()
                cv2.putText(kilitli, "ACIL DURDURMA AKTIF!", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                cv2.imshow("Marmara Rover - Raw Test", kilitli)

    except KeyboardInterrupt:
        print("\nKlavye kesintisi (Ctrl+C) algılandı.")
    finally:
        sistem.kapat()
        cv2.destroyAllWindows()
        print("Sistem güvenle kapatıldı.")

if __name__ == "__main__":
    main()