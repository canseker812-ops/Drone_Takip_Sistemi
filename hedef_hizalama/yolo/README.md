# 👁️ YOLO Algılayıcı (Detector) Modülü

Bu modül, Marmara Rover Otonom Takip Sistemi'nin görsel algılama yeteneğini oluşturur. 

## 📌 Teknik Detaylar
- **Model Mimarisi:** YOLO11n (Nano)
- **Kullanılan Veri Seti:** PARS Dataset V2
- **Başarı Metriği:** 0.992 mAP50
- **Ağırlık Dosyası:** `best.pt`

## 🚀 Çalışma Mantığı
Kameradan alınan anlık BGR formatındaki görüntü kareleri modele beslenir. Model, hedef nesnenin görüntü üzerindeki koordinatlarını (Bounding Box - Merkez X, Merkez Y) milisaniyeler içinde çıkararak Targeting System'e (Hedefleme Sistemine) aktarır.
