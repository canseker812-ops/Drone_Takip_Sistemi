#define STEP_X 2
#define DIR_X 3
#define STEP_Y 4
#define DIR_Y 5

bool acilDurum = false;

// Step motor delay'i (TMC2209 mikroadım için 200-400 arası pürüzsüz sonuç veriyor)
const int motorBekleme = 600; 

void setup() {
  Serial.begin(115200);
  
  // Veri akışı koparsa veya bozulursa Arduino'nun kilitlenmemesi için timeout süresini kısalttık
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
  // E-stop ve Reset kesmeleri
  if (paket == "E") {
    acilDurum = true;
    return;
  }
  if (paket == "R") {
    acilDurum = false;
    return;
  }
  
  // Sistem kilitliyse motor hareket komutlarını atla
  if (acilDurum) return; 

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

// X ve Y eksenlerinin merdiven (step) yapmadan çapraz gidebilmesi için Bresenham mantığı kullanıldı
void hassasVektorSurus(long adimX, long adimY) {
  long dx = abs(adimX);
  long dy = abs(adimY);
  long sx = (adimX > 0) ? 1 : -1;
  long sy = (adimY > 0) ? 1 : -1;

  digitalWrite(DIR_X, sx > 0 ? HIGH : LOW);
  digitalWrite(DIR_Y, sy > 0 ? HIGH : LOW);

  long err = (dx > dy ? dx : -dy) / 2;
  long e2;
  
  long currentX = 0;
  long currentY = 0;

  while (currentX < dx || currentY < dy) {
    // Uzun hareket esnasında araya acil durum girerse kör gitmesin diye buffer'a peek atıyoruz
    if (Serial.available() > 0 && Serial.peek() == '<') {
      break; 
    }

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

    delayMicroseconds(5); 
    
    digitalWrite(STEP_X, LOW);
    digitalWrite(STEP_Y, LOW);
    
    delayMicroseconds(motorBekleme); 
  }
}

void aramaHareketiniYap() {
  // Hedef kadrajda yokken yavaşça sağa dön
  digitalWrite(DIR_X, HIGH);
  for(int i = 0; i < 30; i++) {
    digitalWrite(STEP_X, HIGH);
    delayMicroseconds(5);
    digitalWrite(STEP_X, LOW);
    delayMicroseconds(motorBekleme * 2); // Arama hızı normalden daha yavaş
  }
}