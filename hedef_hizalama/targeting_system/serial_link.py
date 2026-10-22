import serial
import time
import config

class SeriBaglanti:
    """Python ile Arduino UNO arasındaki yüksek hızlı (115200 Baud) paket haberleşmesini yönetir."""
    
    def __init__(self):
        self.port = None
        self.bagli = False
        
        try:
            # timeout=0 komutu non-blocking çalışmasını sağlar, yani Arduino'dan cevap gelmezse Python kodunu dondurmaz
            self.port = serial.Serial(config.SERI_PORT, config.BAUD, timeout=0)
            self.bagli = True
            time.sleep(2) # Arduino'nun seri port açılırken attığı boot restart'ını bekliyoruz
            self.port.reset_input_buffer()
        except Exception as e:
            # Kablo koptuğunda veya port yanlış girildiğinde kod çökmesin, sadece konsola hata bassın
            print(f"UYARI: Arduino'ya bağlanılamadı ({config.SERI_PORT}). Hata: {e}")
            self.bagli = False

    def gonder(self, mesaj):
        """String paketi (örn: <15,-5> veya <E>) bytelara çevirip UART hattına sürer."""
        if not self.bagli:
            return
            
        try:
            self.port.write(mesaj.encode('utf-8'))
        except Exception:
            self.bagli = False # Gönderim anında kablo çıkarsa durumu güncelle

    def oku(self):
        """Arduino'dan dönen telemetry veya ACK loglarını toplar. (Dashboard'da göstermek için)"""
        satirlar = []
        if self.bagli and self.port.in_waiting > 0:
            try:
                # Buffer'da bekleyen tüm satırları temizleyene kadar oku
                okunan = self.port.readlines()
                for satir in okunan:
                    satirlar.append(satir.decode('utf-8', errors='ignore').strip())
            except Exception:
                pass
        return satirlar

    def kapat(self):
        # İşletim sistemi portu kilitli bırakmasın diye çıkışta güvenli kapatma
        if self.bagli and self.port.is_open:
            self.port.close()
            self.bagli = False