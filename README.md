# Marmara Rover – Otonom Hedef Tespit ve Hizalama

Kamera görüntüsünde kırmızı renkli, 3B yazıcıyla üretilmiş drone modelini **YOLO** ile tespit eden, iki eksenli (yaw/pitch) **NEMA 17** step motor sistemini **UART** üzerinden Arduino UNO'ya komut göndererek hedefe otonom olarak hizalayan sistem.

![Hedef drone modeli](hedef-drone.jpeg)

## İçindekiler

- [Demo Videosu](#demo-videosu)
- [Sistem Özeti](#sistem-özeti)
- [Dosya Hiyerarşisi](#dosya-hiyerarşisi)
- [Donanım ve Bağlantılar](#donanım-ve-bağlantılar)
- [Kurulum ve Çalıştırma Adımları](#kurulum-ve-çalıştırma-adımları)
- [Haberleşme Protokolü (UART)](#haberleşme-protokolü-uart)
- [Arama Modu](#arama-modu)
- [Güvenlik ve Hata Yönetimi](#güvenlik-ve-hata-yönetimi)
- [Ayar ve Kalibrasyon](#ayar-ve-kalibrasyon)
- [YOLO Modeli ve Veri Seti](#yolo-modeli-ve-veri-seti)
- [Karşılaşılan Problemler ve Çözümler](#karşılaşılan-problemler-ve-çözümler)
- [Kullanılan Teknolojiler](#kullanılan-teknolojiler)

## Demo Videosu

[Demo videosunu izle](VIDEO_LINKI_BURAYA)

Videoda gösterilenler:
1. Sistem açılışı ve canlı kamera görüntüsü
2. Hedef yokken arama modu
3. Hedefin tespiti ve merkeze hizalanması
4. Hedef kadrajdan hızlı çıkınca son yöne doğru arama
5. Dashboard üzerinden acil durdurma (E-stop) ve yeniden başlatma

## Sistem Özeti

```
┌────────────┐   görüntü   ┌─────────────────────┐   UART (115200)   ┌─────────────┐   STEP/DIR   ┌──────────────┐
│ Logitech   │ ──────────► │ Laptop (Python)     │ ────────────────► │ Arduino UNO │ ───────────► │ TMC2209 +    │
│ C270       │             │ YOLO + hesaplama    │   <x,y>  <E> <R>  │ (mcu)       │              │ NEMA 17 x2   │
└────────────┘             │ + Dashboard         │                   └─────────────┘              │ (yaw, pitch) │
                           └─────────────────────┘                                                └──────────────┘
```

**Çalışma mantığı:**

1. Laptop, kameradan aldığı karede YOLO ile drone'u tespit eder.
2. Hedefin merkezinin görüntü merkezine olan X/Y farkından step sayısı hesaplanır.
3. Hesaplanan vektör `<x,y>` paketi olarak Arduino'ya gönderilir.
4. Arduino, Bresenham algoritmasıyla iki ekseni birlikte sürer (çapraz hareket merdiven yapmaz).
5. Hedef yoksa PC `<999,999>` gönderir ve Arduino arama moduna girer.

## Dosya Hiyerarşisi

```
Target-Tracking-Challenge/
├── hedef-drone.jpeg                # Hedef drone modeli fotoğrafı
├── hedef_hizalama/
│   ├── targeting_system/           # Laptop tarafı (Python)
│   │   ├── main.py                 # Ana döngü: kamera, tespit, hesaplama, UART
│   │   ├── requirements.txt        # Python bağımlılıkları
│   │   └── ...
│   ├── dashboard/                  # Arayüz
│   │   └── ...                     # Canlı görüntü, durum, E-stop butonu
│   ├── mcu/                        # Arduino UNO yazılımı
│   │   └── motor_kontrol/
│   │       └── motor_kontrol.ino   # STEP/DIR sürüşü, arama modu, E-stop
│   └── yolo/
│       ├── dataset/
│       │   └── README.md           # Veri seti bağlantıları ve sürüm bilgisi
│       ├── best.pt                 # Eğitilmiş YOLO modeli
│       └── results/                # Eğitim sonuçları (grafikler, metrikler)
└── README.md
```

| Klasör | Görevi |
|---|---|
| `targeting_system/` | Hedef tespiti, konum hesabı, otonom hizalama, UART haberleşmesi |
| `dashboard/` | Canlı kamera görüntüsü, sistem durumu, durdurma kontrolü |
| `mcu/` | Seri paket ayrıştırma, STEP/DIR motor kontrolü, arama modu, acil durum |
| `yolo/` | Veri seti bilgisi, eğitim sonuçları, model dosyası |

## Donanım ve Bağlantılar

| Parça | Detay |
|---|---|
| Kamera | Logitech C270 |
| MCU | Arduino UNO |
| Motorlar | 2 × NEMA 17 (yaw ve pitch) |
| Sürücüler | TMC2209 (mikroadım) |
| Haberleşme | UART, 115200 baud |

**Arduino pin eşleşmesi:**

| Arduino Pin | Görev |
|---|---|
| D2 | STEP_X (yaw) |
| D3 | DIR_X (yaw) |
| D4 | STEP_Y (pitch) |
| D5 | DIR_Y (pitch) |

> Sürücü ve Arduino GND'leri ortak olmalı. TMC2209 **EN** pini LOW'a çekilmeli. Motor beslemesi sürücünün izin verdiği aralıkta olmalı ve Vref akım ayarı motora göre yapılmalıdır.

## Kurulum ve Çalıştırma Adımları

### 1. Repoyu klonla

```bash
git clone <repo-url>
cd Target-Tracking-Challenge
```

### 2. Arduino yazılımını yükle

1. Arduino IDE'yi aç, `hedef_hizalama/mcu/motor_kontrol/motor_kontrol.ino` dosyasını aç.
2. Kart olarak **Arduino UNO**, doğru **COM portunu** seç.
3. **Yükle**'ye bas.
4. Yükleme bittikten sonra Serial Monitor'ü **kapat** (portu başka program kullanamaz).

> **Önemli:** Dosyanın başındaki `ADIM_15` sabitini kendi sisteminize göre ayarlayın (bkz. [Ayar ve Kalibrasyon](#ayar-ve-kalibrasyon)).

### 3. Python ortamını hazırla

```bash
cd hedef_hizalama/targeting_system
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Ayarları yap

- Arduino'nun **COM portunu** gir (örn. `COM3`).
- Kamera indeksini ayarla (genelde `0`, harici C270 için `1` olabilir).
- YOLO model yolunu ayarla: `hedef_hizalama/yolo/best.pt`.

### 5. Sistemi başlat

```bash
python main.py
```

Dashboard açılır, canlı görüntü gelir. **Start** ile sistem aktif olur, **Stop / E-stop** ile durdurulur.

### 6. Durdurma

Dashboard'daki **E-stop** butonu Arduino'ya `<E>` gönderir. Motorlar anında durur. Yeniden başlatmak için **Reset/Start** ile `<R>` gönderilir.

## Haberleşme Protokolü (UART)

Seri port: **115200 baud**. Paketler `<` ile başlar ve `>` ile biter.

| Paket | Anlamı |
|---|---|
| `<x,y>` | Hedefe hizalanmak için X ve Y eksenlerinde gidilecek **adım** sayısı (işaret yönü belirler) |
| `<0,0>` | Hedef merkezde, hareket yok |
| `<999,999>` | Hedef görünmüyor → arama modu |
| `<E>` | Acil durdurma (E-stop) |
| `<R>` | Acil durumu sıfırla, hareketi tekrar aç |

Örnek: `<-35,12>` → X ekseninde 35 adım sola, Y ekseninde 12 adım yukarı.

## Arama Modu

Hedef kaybında veya sistem başladığında hedef görünmüyorsa Arduino üç aşamalı arama yapar:

1. **Takip:** Hedef görünüyorsa vektörü izler. Son vektörün yönünü hatırlar.
2. **Son yön araması:** Hedef hızlı bir şekilde kadrajın kenarından çıktıysa, motor yaklaşık 2 saniye boyunca hedefin çıktığı yöne yavaşça dönmeye devam eder.
3. **Standart tarama:** Bulamazsa (veya hedef hiç görülmediyse) X ve Y eksenlerinde başlangıç noktası etrafında **±15°** kare tarama yapar:
   - 15° sağa + 15° yukarı (çapraz)
   - 30° sola → 30° aşağı → 30° sağa → 30° yukarı → tekrar

Hedef görüldüğü anda arama bırakılır ve takip başlar. Hız değişimleri yumuşak (rampalı) yapılır, ani başlangıç/duruş yoktur.

## Güvenlik ve Hata Yönetimi

- **E-stop:** `<E>` paketi gelince tüm hareket ve arama anında durur. `<R>` gelene kadar hareket komutları yok sayılır.
- **Uzun harekette kesme:** Hareket sürerken yeni paket (`<` karakteri) gelirse mevcut hareket kesilir, sıradaki komut hemen işlenir. Acil durum bu sayede gecikmesiz çalışır.
- **Paket zaman aşımı:** PC 400 ms boyunca paket göndermezse hedef kayıp sayılır ve arama başlar. (PC bağlanmadan motor kendi kendine hareket etmez.)
- **Bozuk paket koruması:** Paket başı/sonu kontrol edilir, boşluk ve satır sonu karakterleri temizlenir, geçersiz paketler yok sayılır.
- **Seri okuma zaman aşımı:** 20 ms. Paket ortadan bölünürse sistem kilitlenmez.

## Ayar ve Kalibrasyon

`motor_kontrol.ino` başındaki parametreler:

| Parametre | Açıklama | Varsayılan |
|---|---|---|
| `ADIM_15` | 15° dönüş için step sayısı | `133` |
| `motorBekleme` | Takip sırasında adımlar arası bekleme (µs) | `600` |
| `ARAMA_YAVAS` / `ARAMA_HIZLI` | Tarama hız aralığı (µs, büyük = yavaş) | `5000` / `3000` |
| `RAMP_ADIM` | Hızlanma/yavaşlama adım sayısı | `50` |
| `YON_ESIK` | Son vektör bundan büyükse "kenardan çıktı" sayılır | `40` |
| `SON_YON_SURE` | Son yöne dönme süresi (ms) | `2000` |
| `KAYIP_TIMEOUT` | Paket gelmezse hedef kayıp sayma süresi (ms) | `400` |

**`ADIM_15` hesabı:**

```
ADIM_15 = (motor tur başı adım × mikroadım × dişli oranı) / 24
Örnek: 200 × 16 = 3200 adım/tur  →  3200 / 24 ≈ 133
```

Motor gerçekte 15°'den fazla veya az dönüyorsa değeri orantılı olarak değiştirin. Yön ters ise `LEG_X` / `LEG_Y` dizilerindeki işaretleri çevirin.

## YOLO Modeli ve Veri Seti

Eğitim, görev kapsamında sağlanan iki Roboflow veri seti ile yapılmıştır:

1. [PARS Dataset V2](https://universe.roboflow.com/new-workspace-maa2l/pars-dataset-v2/browse?queryText=class%3ADrone&pageSize=100&startingIndex=1100&browseQuery=true)
2. [PARS](https://universe.roboflow.com/hasans-workspace-lnuhg/pars-9yaon/browse?queryText=class%3ADrone&pageSize=100&startingIndex=100&browseQuery=true)

Veri seti bağlantıları, sürüm bilgisi ve eğitim sonuçları `hedef_hizalama/yolo/` altında belgelenmiştir. Ayrıntılar için [dataset açıklamasına](hedef_hizalama/yolo/dataset/README.md) bakın.

| Bilgi | Değer |
|---|---|
| Model | YOLOv? (örn. YOLOv8n) |
| Epoch | ? |
| Görüntü boyutu | ? |
| mAP@50 | ? |
| Precision / Recall | ? / ? |

## Karşılaşılan Problemler ve Çözümler

| Problem | Sebep | Çözüm |
|---|---|---|
| Hedef yokken motor sürekli sağa dönüyordu | Arama komutu (`<999,999>`) her seferinde sabit adım atıyor, bitince durmuyor veya sürekli tekrarlıyordu | Aramayı bloklayan döngüden çıkarıp `loop()` içinde durum makinesine (takip / son yön / tarama) çevirdik |
| Arama hedef bulunsa da devam ediyordu | `<0,0>` paketi arama bayrağını kapatmıyordu | `<999,999>` dışındaki her geçerli paket aramayı durduruyor |
| Acil durum hareket sırasında geç fark ediliyordu | Bayrak yalnızca ana döngüde güncelleniyor, hareket sırasında okunmuyordu | Hareket döngüsünde seri port kontrolü, yeni `<` görülünce hareketi kesme |
| Ani başlangıçta adım kaçırma ve sarsıntı | Motor sıfırdan tam hıza çıkıyordu | Hız rampası (yavaş başla, hızlan, yavaşla) eklendi |
| Paketler bozuk/kırpık okunuyordu | Çok kısa seri zaman aşımı (5 ms) | Zaman aşımı 20 ms yapıldı, `trim()` ile paket temizlendi |
| Hedef kadrajdan çıkınca arama yönü bilinmiyordu | Son konum saklanmıyordu | Son vektörün yönü hatırlanıp önce o yöne arama yapılıyor |

## Kullanılan Teknolojiler

- **Python 3** – laptop yazılımı
- **YOLO (Ultralytics)** – nesne tespiti
- **OpenCV** – kamera ve görüntü işleme
- **PySerial** – UART haberleşmesi
- **Arduino C++** – mikrodenetleyici yazılımı (Bresenham tabanlı iki eksenli STEP/DIR sürüşü)
- **TMC2209 + NEMA 17** – motor kontrolü
- **GitHub** – sürüm kontrolü ve Pull Request ile teslim
