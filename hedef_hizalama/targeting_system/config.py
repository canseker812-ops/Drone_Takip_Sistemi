from pathlib import Path

# Proje: hedef_hizalama/ klasörü (bu dosyanın bir üst klasörü)
KOK = Path(__file__).resolve().parent.parent

# ---- Model ----
MODEL_YOLU = KOK / "yolo" / "models" / "best.pt"
CONF_ESIGI = 0.4        # bu güvenin altındaki tespitler atılır
SINIF_DRONE = 0         # data.yaml: 0 = drone

# ---- Kamera ve seri port ----
KAMERA_INDEKSI = 0      # laptop kamerası 0, harici C270 genelde 1
SERI_PORT = "COM8"      # Aygıt Yöneticisi'nden bak
BAUD = 9600             # mcu.ino'daki Serial.begin ile aynı olmalı
GONDERIM_ARALIGI = 0.05 # saniye, en fazla saniyede 20 paket

# ---- Takip davranışı ----
OLU_BOLGE = 30          # piksel, bunun içinde motor oynamaz
KAYIP_ESIGI = 15        # bu kadar kare hedef yoksa ARANIYOR'a geç

# ---- PID ve motor ----
KP, KI, KD = 0.05, 0.0, 0.003
MAX_ADIM = 20           # mcu.ino'daki MAX_ADIM ile aynı olmalı
YAW_YONU = 1            # donanımda yön ters çıkarsa -1 yap
PITCH_YONU = 1