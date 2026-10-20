// --- MARMARA ROVER: YÜKSEK HASSASİYETLİ OTONOM TAKİP SİSTEMİ ---
// Geliştirici: Şeker Can Şeker & AI Copilot
// Algoritma: Bresenham Linear Interpolation & Non-blocking UART

#define STEP_X 2
#define DIR_X 3
#define STEP_Y 4
#define DIR_Y 5

bool acilDurum = false;

// Motor hızı (Mikrosaniye). TMC2209 mikroadım (1/16 veya 1/32) modundaysa 
// bu değeri 200-400 aralığına kadar düşürüp inanılmaz pürüzsüz hızlar elde edebilirsin.
const int motorBekleme = 600; 

void setup() {
  Serial.begin(115200);
  
  // PROFESYONEL DOKUNUŞ: Varsayılan 1000ms (1 saniye) UART bekleme süresini 5ms'ye düşürüyoruz.
  // Bu sayede koptuktan veya bozuk paket geldikten sonra sistem "donup kalmaz", anında toparlar.
  Serial.setTimeout(5);
  
  pinMode(STEP_X, OUTPUT);
  pinMode(DIR_X, OUTPUT);
  pinMode(STEP_Y, OUTPUT);
  pinMode(DIR_Y, OUTPUT);
  
  digitalWrite(STEP_X, LOW);
  digitalWrite(STEP_Y, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '<') {
      String paket = Serial.readStringUntil('>');
      komutIsle(paket);
    }
  }
}

void komutIsle(String paket) {
  // 1. GÜVENLİK (INTERRUPT) KONTROLLERİ
  if (paket == "E") {
    acilDurum = true;
    return;
  }
  if (paket == "R") {
    acilDurum = false;
    return;
  }
  if (acilDurum) return; // Sistem kilitliyse paketleri görmezden gel

  // 2. PAKET ÇÖZÜMLEME (PARSING)
  int virgulIndex = paket.indexOf(',');
  if (virgulIndex > 0) {
    long adimX = paket.substring(0, virgulIndex).toInt();
    long adimY = paket.substring(virgulIndex + 1).toInt();

    if (adimX == 999 && adimY == 999) {
      aramaHareketiniYap();
    } 
    else if (adimX != 0 || adimY != 0) {
      hassasVektorSurus(adimX, adimY);
    }
  }
}

// -------------------------------------------------------------------------
// BRESENHAM ÇİZGİ ALGORİTMASI İLE KUSURSUZ (TİTREŞİMSİZ) VEKTÖREL HAREKET
// -------------------------------------------------------------------------
void hassasVektorSurus(long adimX, long adimY) {
  // Yönleri ayarla ve sayıları mutlak (pozitif) değere çevir
  long dx = abs(adimX);
  long dy = abs(adimY);
  long sx = (adimX > 0) ? 1 : -1;
  long sy = (adimY > 0) ? 1 : -1;

  digitalWrite(DIR_X, sx > 0 ? HIGH : LOW);
  digitalWrite(DIR_Y, sy > 0 ? HIGH : LOW);

  // Bresenham hata payı hesaplayıcısı
  long err = (dx > dy ? dx : -dy) / 2;
  long e2;
  
  long currentX = 0;
  long currentY = 0;

  // Motorlar hedef adımlarına ulaşana kadar döngü çalışır
  while (currentX < dx || currentY < dy) {
    
    // Güvenlik: Hareket halindeyken Acil Durdurma paketi geldiyse fren yap!
    if (Serial.available() > 0 && Serial.peek() == '<') {
      break; 
    }

    // Hangi motorun adım atması gerektiğine hata payına (err) göre karar verilir.
    // Bu sayede motorlar "merdiven" gibi değil, "dümdüz bir çizgi" (diagonal) şeklinde hedefe gider.
    e2 = err;
    if (e2 > -dx && currentX < dx) {
      err -= dy;
      digitalWrite(STEP_X, HIGH);
      currentX++;
    }
    if (e2 < dy && currentY < dy) {
      err += dx;
      digitalWrite(STEP_Y, HIGH);
      currentY++;
    }

    // TMC2209 için gerekli minimum HIGH pals süresi (Çok kısa olmalı)
    delayMicroseconds(5); 
    
    digitalWrite(STEP_X, LOW);
    digitalWrite(STEP_Y, LOW);
    
    // Hareketin hızını belirleyen ana bekleme süresi
    delayMicroseconds(motorBekleme); 
  }
}

// -------------------------------------------------------------------------
// HEDEF KAYIPKEN YUMUŞAK TARAMA MODU
// -------------------------------------------------------------------------
void aramaHareketiniYap() {
  digitalWrite(DIR_X, HIGH);
  for(int i = 0; i < 30; i++) {
    digitalWrite(STEP_X, HIGH);
    delayMicroseconds(5);
    digitalWrite(STEP_X, LOW);
    delayMicroseconds(motorBekleme * 2); // Aramayı daha sarsıntısız ve yavaş yap
  }
}