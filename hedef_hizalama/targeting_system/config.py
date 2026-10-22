from pathlib import Path

# --- PROJE YOLLARI ---
# Script nereden çalışırsa çalışsın kök dizini (hedef_hizalama) otomatik bulur
KOK = Path(__file__).resolve().parent.parent

# --- YOLO MODEL AYARLARI ---
MODEL_YOLU = KOK / "yolo" / "models" / "best.pt"
CONF_ESIGI = 0.4        # Bu güven skorunun altındaki hayalet tespitleri yoksayıyoruz
SINIF_DRONE = 0         # Dataset'te dron/hedef class ID'miz (data.yaml'a göre)

# --- DONANIM VE HABERLEŞME (UART) ---
KAMERA_INDEKSI = 0      # Harici C270 bağlarsan 1 yap
SERI_PORT = "COM8"      # Sahaya çıkmadan önce Aygıt Yöneticisi'nden kesin kontrol et!
BAUD = 115200           # mcu.ino'daki Serial.begin ile aynı olmak zorunda, hızı artırdık
GONDERIM_ARALIGI = 0.05 # Saniyede en fazla 20 paket gönderilir (Arduino buffer'ı şişmesin diye)

# --- KONTROL VE HASSASİYET ---
OLU_BOLGE = 30          # Hedef bu piksel aralığındayken motorlara komut gitmez (Titremeyi/Jitter'ı önler)
KAYIP_ESIGI = 15        # Hedef bu kadar kare üst üste bulunamazsa sistem ARANIYOR moduna geçer

# --- PİD VE EKSEN (NEMA 17) AYARLARI ---
# İhtiyaca göre sahada test ederek ince ayar çekilecek (P, I, D)
KP, KI, KD = 0.05, 0.0, 0.003 
MAX_ADIM = 20           # PID'nin bir seferde çıkarabileceği maksimum step sayısı
YAW_YONU = 1            # Pan (X) ekseni ters hareket ediyorsa bunu -1 yap
PITCH_YONU = 1          # Tilt (Y) ekseni ters hareket ediyorsa bunu -1 yap