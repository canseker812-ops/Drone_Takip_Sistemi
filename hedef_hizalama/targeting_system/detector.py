import cv2
from ultralytics import YOLO
import config

class Tespitci:
    """YOLO11n modelini yükleyip kare üzerindeki hedefleri bounding box ile çıkarır."""
    
    def __init__(self):
        # Model dosyasının varlığını önceden kontrol et
        if not config.MODEL_YOLU.exists():
            raise FileNotFoundError(
                f"YOLO model dosyası bulunamadı: {config.MODEL_YOLU}\n"
                "Lütfen 'best.pt' dosyasını doğru konuma kopyalayın."
            )
        # Model yüklenirken konsola gereksiz log basmasın diye verbose=False yapıyoruz
        self.model = YOLO(str(config.MODEL_YOLU), task="detect", verbose=False)

    def bul(self, kare):
        """
        Kareyi alır, işler ve (cizili_kare, hedef_merkezi_tuple) döndürür.
        Eğer hedef yoksa hedef_merkezi None döner.
        Birden fazla hedef varsa en yüksek güven skoruna sahip olanı seçilir.
        """
        if kare is None:
            return None, None

        # YOLO inference işlemi (Performans için conf eşiğini config'den alıyoruz)
        sonuclar = self.model(kare, conf=config.CONF_ESIGI, verbose=False)
        cizili = kare.copy()
        hedef_merkez = None

        if len(sonuclar) > 0:
            kutu_verileri = sonuclar[0].boxes
            if kutu_verileri is not None and len(kutu_verileri) > 0:
                # Sadece SINIF_DRONE sınıfına ait kutuları filtrele
                drone_kutulari = [
                    kutu for kutu in kutu_verileri
                    if int(kutu.cls[0].item()) == config.SINIF_DRONE
                ]

                if drone_kutulari:
                    # Birden fazla hedef varsa her zaman en yüksek güven skoruna (conf) sahip olanı seç
                    en_iyi_kutu = max(drone_kutulari, key=lambda k: k.conf[0].item())

                    x1, y1, x2, y2 = map(int, en_iyi_kutu.xyxy[0].tolist())

                    # Koordinatların görüntü sınırları içinde olduğundan emin ol
                    yukseklik, genislik = kare.shape[:2]
                    x1 = max(0, min(x1, genislik - 1))
                    y1 = max(0, min(y1, yukseklik - 1))
                    x2 = max(0, min(x2, genislik - 1))
                    y2 = max(0, min(y2, yukseklik - 1))

                    # Hedefin tam merkez koordinatını hesapla (Motorlar buraya hizalanacak)
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    hedef_merkez = (cx, cy)

                    # Güven skoru ve sınıf etiketini ekrana yaz
                    guven = en_iyi_kutu.conf[0].item()
                    etiket = f"Drone {guven:.2f}"

                    # Arayüzde görmek için hedefin etrafına yeşil bir kutu çiz
                    cv2.rectangle(cizili, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        cizili, etiket, (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2
                    )

        return cizili, hedef_merkez
