import cv2
from takip_sistemi import TakipSistemi

# Geliştirici: Şeker Can Şeker
# NOT: Streamlit dashboard olmadan sadece saf donanım ve model testi yapmak isterseniz
# sistemi bu dosyadan hızlıca ayağa kaldırabilirsiniz. (Sıfır UI yükü)

PENCERE_ADI = "Marmara Rover - Raw Test"

def overlay_bilgi(kare, bilgi):
    """Kare üzerine anlık durum bilgisini yazar (geliştirici modunda kullanılır)."""
    durum_renk = {
        "TAKIP":       (0, 255, 0),
        "HIZALI":      (0, 200, 255),
        "ARANIYOR":    (0, 200, 255),
        "BEKLEMEDE":   (180, 180, 180),
        "ACIL_DURDUR": (0, 0, 255),
        "HATA":        (0, 0, 255),
    }
    renk = durum_renk.get(bilgi["durum"], (200, 200, 200))
    metin = (
        f"Durum: {bilgi['durum']}  "
        f"Hata: ({bilgi['hata_x']:+d}, {bilgi['hata_y']:+d})  "
        f"Adim: ({bilgi['adim_x']:+d}, {bilgi['adim_y']:+d})"
    )
    cv2.putText(kare, metin, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, renk, 2)


def main():
    sistem = TakipSistemi()
    sistem.baslat()

    print("Marmara Rover Otonom Takip - Geliştirici Modu Başladı.")
    print("Çıkmak için kameradayken 'q', Acil Durdurma için 'e', Reset için 'r' tuşuna basın.")

    try:
        while True:
            kare, bilgi = sistem.adim()

            if kare is None:
                print("Kamera akışı koptu veya sistem hataya düştü. Çıkılıyor...")
                break

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

            # Acil durdurma ekrana kırmızı uyarı yazdırır
            if bilgi["durum"] == "ACIL_DURDUR":
                cv2.putText(
                    kare, "ACIL DURDURMA AKTIF!", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3
                )
            else:
                overlay_bilgi(kare, bilgi)

            cv2.imshow(PENCERE_ADI, kare)

    except KeyboardInterrupt:
        print("\nKlavye kesintisi (Ctrl+C) algılandı.")
    finally:
        sistem.kapat()
        cv2.destroyAllWindows()
        print("Sistem güvenle kapatıldı.")


if __name__ == "__main__":
    main()
