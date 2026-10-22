import time

class PID:
    """NEMA 17 motorların hedefe ani zıplamalar yapmadan, pürüzsüz (yumuşak) gitmesini sağlayan kontrolcü."""
    
    def __init__(self, kp, ki, kd, cikis_siniri=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.cikis_siniri = cikis_siniri
        self.onceki_hata = 0
        self.integral = 0
        self.son_zaman = time.perf_counter()

    def hesapla(self, hata):
        # Döngüler arası geçen süreyi (dt) buluyoruz, böylece FPS düşse bile D (Türev) sapıtmıyor
        simdi = time.perf_counter()
        dt = simdi - self.son_zaman
        if dt <= 0.0:
            dt = 1e-4 # Sıfıra bölme hatasından kaçınmak için mikro bir sapma payı
            
        self.son_zaman = simdi

        # P (Proportional) - Anlık hata orantısı
        p_cikis = self.kp * hata
        
        # I (Integral) - Zamanla biriken hata (Windup korumalı kurgulandı)
        self.integral += hata * dt
        i_cikis = self.ki * self.integral
        
        # D (Derivative) - Hatanın değişim hızı (Hedefe yaklaşırken motoru frenler)
        turev = (hata - self.onceki_hata) / dt
        d_cikis = self.kd * turev
        
        self.onceki_hata = hata

        cikis = p_cikis + i_cikis + d_cikis

        # Mekanik sınırlandırma: Motorun bir turda atabileceği maksimum adımı (Step) kırpıyoruz
        if self.cikis_siniri is not None:
            cikis = max(-self.cikis_siniri, min(self.cikis_siniri, cikis))
            
        return cikis

    def sifirla(self):
        """
        Sistem ARANIYOR moduna düştüğünde veya ölü bölgedeyken (hedef kilitliyken) çağrılır.
        Bu sayede I (Integral) şişmez ve hedef aniden hareket ettiğinde motorlar sarsılmaz.
        """
        self.onceki_hata = 0
        self.integral = 0
        self.son_zaman = time.perf_counter()