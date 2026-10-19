import cv2

from takip_sistemi import TakipSistemi

RENKLER = {
    "BEKLEMEDE": (200, 200, 200),
    "ARANIYOR": (0, 165, 255),
    "TAKIP": (0, 255, 0),
    "HIZALI": (0, 255, 0),
    "ACIL_DURDUR": (0, 0, 255),
    "HATA": (0, 0, 255),
}


def main():
    sistem = TakipSistemi()
    sistem.baslat()  # dashboard'suz testte hemen aramaya başla
    try:
        while True:
            kare, bilgi = sistem.adim()
            if kare is None:
                print("Durum:", bilgi["durum"], bilgi["hata_mesaji"])
                break

            renk = RENKLER.get(bilgi["durum"], (255, 255, 255))
            # OpenCV Türkçe harf çizemez, bu yüzden durum adları ASCII
            cv2.putText(kare, f"Durum: {bilgi['durum']}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, renk, 2)
            cv2.putText(kare, f"Hata X:{bilgi['hata_x']} Y:{bilgi['hata_y']}  "
                              f"Adim X:{bilgi['adim_x']} Y:{bilgi['adim_y']}",
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, renk, 2)
            cv2.putText(kare, "q:cik b:baslat d:durdur e:ACIL r:reset",
                        (20, kare.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 1)
            cv2.imshow("Hedef Takip", kare)

            tus = cv2.waitKey(1) & 0xFF
            if tus == ord("q"):
                break
            elif tus == ord("b"):
                sistem.baslat()
            elif tus == ord("d"):
                sistem.durdur()
            elif tus == ord("e"):
                sistem.acil_durdur()
            elif tus == ord("r"):
                sistem.reset()
    finally:
        sistem.kapat()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()