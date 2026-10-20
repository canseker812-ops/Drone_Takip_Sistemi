# ⚙️ Mikrodenetleyici (MCU) Modülü ve Donanım Mimarisi

Bu modül, Python tabanlı Görev Kontrol Merkezi'nden (Dashboard) gelen telemetri verilerini fiziksel hareketlere dönüştüren gömülü yazılımı (`mcu.ino`) içerir. Sistem, yüksek hassasiyetli hedef takibi için sessiz ve pürüzsüz çalışan TMC2209 step motor sürücüleriyle donatılmıştır.

## 📌 Donanım Bileşenleri
- **Ana Kontrolcü:** Arduino UNO (ATmega328P)
- **Motor Sürücüler:** 2 x TMC2209 V1.2 (Standalone STEP/DIR Modunda)
- **Eyleyiciler:** 2 x NEMA 17 Bipolar Step Motor (Pan ve Tilt eksenleri için)
- **Güç Kaynağı:** Motorlar için harici 12V/24V, Lojik devreler için 5V

---

## 🔌 Pin Bağlantı Haritası (Pinout)

Sistemin donanımsal kurulumu aşağıdaki şemaya göre yapılmalıdır:

### 1. X Ekseni Motor Sürücüsü (Pan / Yaw) - TMC2209
- **STEP Pini:** Arduino `D2`
- **DIR (Yön) Pini:** Arduino `D3`
- **EN (Enable) Pini:** `GND` (Sistemin sürekli aktif olması ve tutunma torku sağlaması için doğrudan toprağa çekilmiştir)
- **VMOT & GND:** Harici 12V/24V Güç Kaynağı (+ ve -)
- **VDD & GND:** Arduino `5V` ve `GND` (Lojik besleme)
- **A1, A2, B1, B2:** NEMA 17 X-Ekseni Motor Bobinleri

### 2. Y Ekseni Motor Sürücüsü (Tilt / Pitch) - TMC2209
- **STEP Pini:** Arduino `D4`
- **DIR (Yön) Pini:** Arduino `D5`
- **EN (Enable) Pini:** `GND` 
- **VMOT & GND:** Harici 12V/24V Güç Kaynağı (+ ve -)
- **VDD & GND:** Arduino `5V` ve `GND`
- **A1, A2, B1, B2:** NEMA 17 Y-Ekseni Motor Bobinleri

> **⚠️ Güvenlik Uyarısı:** TMC2209 sürücülerini VREF ayarı (Akım Sınırlandırması) yapmadan ve motorlar bağlı değilken ASLA güç vermeyin. Motorlar çalışırken bağlantı kablolarını sökmek sürücüleri yakacaktır.

---

## 📡 Haberleşme Protokolü ve Veri Paketi Yapısı

Arduino, ana bilgisayar (Python/Streamlit) ile UART üzerinden **115200 Baud Rate** hızında haberleşir. Veri bütünlüğünü sağlamak için mesajlar `<` ve `>` karakterleri arasına kapsüllenir (Encapsulation).

### Tanımlı Komut Seti:
1. `<X_ADIM,Y_ADIM>` : **Hareket Komutu.** Örn: `<15,-5>` (X ekseninde 15 adım sağa, Y ekseninde 5 adım aşağı).
2. `<999,999>` : **Arama Komutu (Sweep Modu).** Hedef kameradan çıkarsa sistem bu paketi alır ve etrafı taramak için otomatik Pan/Tilt rotinini başlatır.
3. `<E>` : **Acil Durdurma (E-Stop).** Tüm motor adımlarını anında sıfırlar ve güvenlik kilidini açana kadar yeni komutları reddeder.
4. `<R>` : **Reset Komutu.** Acil durum kilidini açar ve motorları tekrar komut dinlemeye hazır hale getirir.
5. `<0,0>` : **Stabil Mod.** Hedef merkezde (ölü bölgede) tutulduğunda gönderilir. Motorlar konumunu korur.