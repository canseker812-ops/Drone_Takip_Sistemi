import time

import serial

import config


class SeriBaglanti:
    """Arduino ile UART haberleşmesi. Hata olursa program çökmez, bagli=False olur."""

    def __init__(self, port=None, baud=None):
        self.port = None
        port = port or config.SERI_PORT
        baud = baud or config.BAUD
        try:
            self.port = serial.Serial(port, baud, timeout=0.01)
            time.sleep(2)  # UNO port açılınca resetlenir, bekle
            print(f"Mikrodenetleyiciye bağlandı ({port}).")
        except serial.SerialException as hata:
            print(f"Seri port açılamadı ({port}): {hata}")

    @property
    def bagli(self):
        return self.port is not None

    def gonder(self, paket):
        """Paketi satır sonuyla gönderir. Başarılıysa True."""
        if self.port is None:
            return False
        try:
            self.port.write((paket + "\n").encode("utf-8"))
            return True
        except serial.SerialException as hata:
            print(f"Seri yazma hatası, bağlantı koptu: {hata}")
            self.port = None
            return False

    def oku(self):
        """Arduino'dan gelen satırları liste olarak döndürür (ESTOP, OK, ERR)."""
        satirlar = []
        if self.port is None:
            return satirlar
        try:
            while self.port.in_waiting > 0:
                satir = self.port.readline().decode("utf-8", errors="ignore").strip()
                if satir:
                    satirlar.append(satir)
        except serial.SerialException:
            self.port = None
        return satirlar

    def kapat(self):
        if self.port is not None:
            try:
                self.port.close()
            except serial.SerialException:
                pass
            self.port = None