import config


class Tespitci:
    """YOLO modelini yükler ve bir karedeki en güvenli drone'u bulur."""

    def __init__(self):
        if not config.MODEL_YOLU.exists():
            raise FileNotFoundError(f"Model dosyası yok: {config.MODEL_YOLU}")
        from ultralytics import YOLO  # ağır kütüphane, burada yüklenir
        self.model = YOLO(str(config.MODEL_YOLU))

    def bul(self, kare):
        """(kutular çizilmiş kare, hedef) döndürür.
        hedef = (cx, cy) piksel konumu, drone yoksa None."""
        sonuc = self.model(kare, conf=config.CONF_ESIGI,
                           classes=[config.SINIF_DRONE], verbose=False)
        cizili = sonuc[0].plot()
        kutular = sonuc[0].boxes
        if len(kutular) == 0:
            return cizili, None

        # Birden fazla kutu varsa en güvenlisini seç
        kutu = kutular[int(kutular.conf.argmax())]
        x1, y1, x2, y2 = map(int, kutu.xyxy[0])
        return cizili, ((x1 + x2) // 2, (y1 + y2) // 2)