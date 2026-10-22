import cv2
from ultralytics import YOLO
import config

class Tespitci:
    """YOLO11n modelini yükleyip kare üzerindeki hedefleri bounding box ile çıkarır."""
    
    def __init__(self):
        # Model yüklenirken konsola gereksiz log basmasın diye verbose=False yapıyoruz
        self.model = YOLO(str(config.MODEL_YOLU), task="detect", verbose=False)

    def bul(self, kare):
        """
        Kareyi alır, işler ve (cizili_kare, hedef_merkezi_tuple) döndürür.
        Eğer hedef yoksa hedef_merkezi None döner.
        """
        # YOLO inference işlemi (Performans için conf eşiğini config'den alıyoruz)
        sonuclar = self.model(kare, conf=config.CONF_ESIGI, verbose=False)
        cizili = kare.copy()
        hedef_merkez = None

        if len(sonuclar) > 0:
            kutu_verileri = sonuclar[0].boxes
            if len(kutu_verileri) > 0:
                # Birden fazla hedef varsa her zaman en yüksek güven skoruna (conf) sahip olanı ilk alır
                kutu = kutu_verileri[0]
                
                # Model farklı classlar görse bile sadece kendi hedefimizi (SINIF_DRONE) ciddiye al
                if int(kutu.cls[0].item()) == config.SINIF_DRONE:
                    x1, y1, x2, y2 = map(int, kutu.xyxy[0].tolist())
                    
                    # Hedefin tam merkez koordinatını hesapla (Motorlar buraya hizalanacak)
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    hedef_merkez = (cx, cy)
                    
                    # Arayüzde görmek için hedefin etrafına yeşil bir kutu çiz
                    cv2.rectangle(cizili, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
        return cizili, hedef_merkez