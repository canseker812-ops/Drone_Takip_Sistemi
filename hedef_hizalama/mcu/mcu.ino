#define STEP_X 2
#define DIR_X 3
#define STEP_Y 4
#define DIR_Y 5

bool acilDurum = false;

// Step motor delay'i (Takırtısız ve pürüzsüz takip için)
const int motorBekleme = 900; 

// ================= ÇOK SOFT ARAMA VE AÇI AYARLARI =================
const long ADIM_15 = 150; 

const unsigned int ARAMA_YAVAS = 9000;   
const unsigned int ARAMA_HIZLI = 4500;   
const long RAMP_ADIM = 80;               

const long Y_YARIM_PENCERE = 100; 
long mevcutYKonumu = 0; 
int yYon = 1;          

int taramaKatmani = 1;      
long xKalanAdim = 0;        
long xToplamAdim = 0;       
int xYon = 1;               

long taramaRampSayac = 0;

const long YON_ESIK = 40;                     
const unsigned long SON_YON_SURE = 2000;      
const unsigned int SON_YON_BEKLEME = 4000;      
const unsigned long KAYIP_TIMEOUT = 500;      
// ===================================================

enum Mod { BEKLEMEDE, TAKIP, SON_YON, TARAMA };
Mod mod = BEKLEMEDE; 

bool pcBaglandi = false;                 
unsigned long sonPaketZamani = 0;

int sonYonX = 0;                         
int sonYonY = 0;
int sonCikisYonX = 0;                    
int sonCikisYonY = 0;

unsigned long sonYonBaslangic = 0;
unsigned long sonAdimZamani = 0;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(20);
  
  pinMode(STEP_X, OUTPUT);
  pinMode(DIR_X, OUTPUT);
  pinMode(STEP_Y, OUTPUT);
  pinMode(DIR_Y, OUTPUT);
  
  digitalWrite(STEP_X, LOW);
  digitalWrite(DIR_Y, LOW);

  mod = BEKLEMEDE;
  pcBaglandi = false;
  acilDurum = false;
  mevcutYKonumu = 0; 
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '<') {
      String paket = Serial.readStringUntil('>');
      komutIsle(paket);
    }
  }

  // Yalnızca TAKIP modundayken hedef koparsa arama/son yön başlar. BEKLEMEDE modunda asla arama yapmaz!
  if (!acilDurum && mod == TAKIP) {
    if (pcBaglandi && (millis() - sonPaketZamani > KAYIP_TIMEOUT)) {
      hedefKayboldu();
    }
  }

  if (!acilDurum && mod != BEKLEMEDE) {
    if (mod == SON_YON) {
      sonYonAdimi();
    } else if (mod == TARAMA) {
      genisleyenYatayTaramaAdimi();
    }
  }
}

void komutIsle(String paket) {
  paket.trim();

  // E-stop (Acil Durum)
  if (paket == "E") {
    acilDurum = true;
    mod = BEKLEMEDE;
    pcBaglandi = false;
    
    while (Serial.available() > 0) {
      Serial.read();
    }
    return;
  }
  
  // Reset komutu
  if (paket == "R") {
    acilDurum = false;
    mod = BEKLEMEDE;
    pcBaglandi = false;
    mevcutYKonumu = 0; 
    
    while (Serial.available() > 0) {
      Serial.read();
    }
    return;
  }
  
  // ACIL DURUM BASILIYKEN ASLA HAREKET ETME / JOG YAPMA
  if (acilDurum) return; 

  int virgulIndex = paket.indexOf(',');
  if (virgulIndex > 0) {
    long adimX = paket.substring(0, virgulIndex).toInt();
    long adimY = paket.substring(virgulIndex + 1).toInt();

    pcBaglandi = true;
    sonPaketZamani = millis();

    // Python tarafı <999,999> gönderdiğinde (Start basılıp hedef aranırken)
    if (adimX == 999 && adimY == 999) {
      if (mod == BEKLEMEDE) {
        baslatGenisleyenTarama(); // Sadece Start basıldığında aramayı başlat
      }
    } 
    // Stop komutu (<0,0>) geldiğinde: Sadece BEKLEMEDE moduna al, taramaya GİRME!
    else if (adimX == 0 && adimY == 0) {
      mod = BEKLEMEDE;
      pcBaglandi = false;
    }
    else {
      // BEKLEMEDE (Stop) modundayken veya TAKIP modundayken JOG komutları ya da hedef takibi işlenir
      if (mod == BEKLEMEDE) {
        // Stop modundayken bile manuel Jog yapılabilmesi için vektör sürüşe izin veriyoruz
        hassasVektorSurus(adimX, adimY);
      } else {
        mod = TAKIP;                         

        sonYonX = (labs(adimX) >= YON_ESIK) ? (adimX > 0 ? 1 : -1) : 0;
        sonYonY = (labs(adimY) >= YON_ESIK) ? (adimY > 0 ? 1 : -1) : 0;

        if (sonYonX != 0 || sonYonY != 0) {
          sonCikisYonX = sonYonX;
          sonCikisYonY = sonYonY;
        }

        if (adimY != 0) {
          if (adimY < 0 && mevcutYKonumu < Y_YARIM_PENCERE) mevcutYKonumu++;
          else if (adimY > 0 && mevcutYKonumu > -Y_YARIM_PENCERE) mevcutYKonumu--;
        }

        if (adimX != 0 || adimY != 0) {
          hassasVektorSurus(adimX, adimY);
        }
      }
    }
  }
}

void hedefKayboldu() {
  if (mod != TAKIP) return;

  sonAdimZamani = micros();

  if (sonCikisYonX != 0 || sonCikisYonY != 0) {
    sonYonX = sonCikisYonX;
    sonYonY = sonCikisYonY;
    mod = SON_YON;
    sonYonBaslangic = millis();
  } else {
    baslatGenisleyenTarama();
  }
}

void baslatGenisleyenTarama() {
  mod = TARAMA;
  taramaKatmani = 1;
  xKalanAdim = ADIM_15 * taramaKatmani;
  xToplamAdim = xKalanAdim;
  taramaRampSayac = 0;
  xYon = (sonCikisYonX != 0) ? sonCikisYonX : 1;
  
  digitalWrite(DIR_X, xYon > 0 ? HIGH : LOW);
  sonAdimZamani = micros();
}

void sonYonAdimi() {
  if (acilDurum) return; 
  
  if (millis() - sonYonBaslangic >= SON_YON_SURE) {
    baslatGenisleyenTarama();
    return;
  }

  unsigned long simdi = micros();
  if (simdi - sonAdimZamani >= SON_YON_BEKLEME) {
    sonAdimZamani = simdi;

    if (sonYonX != 0) digitalWrite(DIR_X, sonYonX > 0 ? HIGH : LOW);
    
    if (sonYonY != 0) {
      if (sonYonY < 0 && mevcutYKonumu >= Y_YARIM_PENCERE) sonYonY = 0;
      else if (sonYonY > 0 && mevcutYKonumu <= -Y_YARIM_PENCERE) sonYonY = 0;
      
      digitalWrite(DIR_Y, sonYonY > 0 ? HIGH : LOW);
    }

    if (sonYonX != 0) digitalWrite(STEP_X, HIGH);
    if (sonYonY != 0) {
      digitalWrite(STEP_Y, HIGH);
      if (sonYonY < 0) mevcutYKonumu++;
      else mevcutYKonumu--;
    }

    delayMicroseconds(5);
    digitalWrite(STEP_X, LOW);
    digitalWrite(STEP_Y, LOW);
  }
}

void genisleyenYatayTaramaAdimi() {
  if (acilDurum) return; 

  long rampBirim = taramaRampSayac;
  long inisKalan = xKalanAdim;
  if (rampBirim > inisKalan) rampBirim = inisKalan;
  if (rampBirim > RAMP_ADIM) rampBirim = RAMP_ADIM;

  unsigned long aramaHiziDinamik = ARAMA_YAVAS - ((long)(ARAMA_YAVAS - ARAMA_HIZLI) * rampBirim) / RAMP_ADIM;

  unsigned long simdi = micros();
  if (simdi - sonAdimZamani >= aramaHiziDinamik) {
    sonAdimZamani = simdi;

    digitalWrite(DIR_X, xYon > 0 ? HIGH : LOW);
    digitalWrite(STEP_X, HIGH);
    delayMicroseconds(5);
    digitalWrite(STEP_X, LOW);

    if (yYon > 0) {
      if (mevcutYKonumu < Y_YARIM_PENCERE) {
        digitalWrite(DIR_Y, LOW); 
        digitalWrite(STEP_Y, HIGH);
        delayMicroseconds(5);
        digitalWrite(STEP_Y, LOW);
        mevcutYKonumu++;
      } else {
        yYon = -1; 
      }
    } else {
      if (mevcutYKonumu > -Y_YARIM_PENCERE) {
        digitalWrite(DIR_Y, HIGH); 
        digitalWrite(STEP_Y, HIGH);
        delayMicroseconds(5);
        digitalWrite(STEP_Y, LOW);
        mevcutYKonumu--;
      } else {
        yYon = 1; 
      }
    }

    xKalanAdim--;
    taramaRampSayac++;

    if (xKalanAdim <= 0) {
      xYon = -xYon; 
      taramaKatmani++; 
      xKalanAdim = ADIM_15 * taramaKatmani; 
      xToplamAdim = xKalanAdim;
      taramaRampSayac = 0; 
    }
  }
}

void hassasVektorSurus(long adimX, long adimY) {
  long dx = labs(adimX); 
  long dy = labs(adimY); 
  long sx = (adimX > 0) ? 1 : -1;
  long sy = (adimY > 0) ? 1 : -1;

  if (sy < 0 && mevcutYKonumu >= Y_YARIM_PENCERE) sy = 0;
  if (sy > 0 && mevcutYKonumu <= -Y_YARIM_PENCERE) sy = 0;

  digitalWrite(DIR_X, sx > 0 ? HIGH : LOW);
  digitalWrite(DIR_Y, sy > 0 ? HIGH : LOW);

  long err = (dx > dy ? dx : -dy) / 2;
  long e2;
  
  long currentX = 0;
  long currentY = 0;

  while (currentX < dx || currentY < dy) {
    if (acilDurum) break;

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
      
      if (!((sy < 0 && mevcutYKonumu >= Y_YARIM_PENCERE) || (sy > 0 && mevcutYKonumu <= -Y_YARIM_PENCERE))) {
        digitalWrite(STEP_Y, HIGH);
        if (sy < 0) mevcutYKonumu++;
        else mevcutYKonumu--;
      }
      
      currentY++;
    }

    delayMicroseconds(5); 
    
    digitalWrite(STEP_X, LOW);
    digitalWrite(STEP_Y, LOW);
    
    delayMicroseconds(motorBekleme); 
  }
}