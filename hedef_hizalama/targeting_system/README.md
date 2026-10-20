\# 🧠 Hedefleme ve Kontrol Sistemi (Targeting System)



Bu modül, görüntü işleme verilerini eyleyici (motor) komutlarına dönüştüren ana kontrolcüdür. Tamamen Nesne Yönelimli (OOP) mimaride tasarlanmıştır.



\## 📁 Alt Modüller

\- \*\*`detector.py`:\*\* YOLO çıkarım motorunu (Inference) çalıştırır.

\- \*\*`pid.py`:\*\* Hata (Pixel Error) değerini yumuşatıp motor adım komutlarına çeviren Anti-Windup destekli PID kontrolcüsü.



\- \*\*`serial\\\_link.py`:\*\* Güvenli UART haberleşme protokolü. Paket yapısı: `<AdımX,AdımY>`. İstisnai durum paketleri: `<999,999>` (Arama) ve `<E>` (Acil Durdurma).



\- \*\*`takip\\\_sistemi.py`:\*\* Tüm modülleri orkestre eden, sistemin mevcut durumunu (TAKIP, ARANIYOR vb.) belirleyen State Machine (Durum Makinesi).



Sistem, Deadzone (Ölü Bölge) optimizasyonuna sahiptir; hedef merkezde belli bir tolerans içindeyse motorlar titreme yapmaması için durdurulur.

