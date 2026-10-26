import time
import config

class PID:
    """NEMA 17 motorların hedefe ani zıplamalar yapmadan, pürüzsüz (yumuşak) gitmesini sağlayan kontrolcü."""
    
    def __init__(self, kp, ki, kd, cikis_siniri=None, integral_limit=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.cikis_siniri = cikis_siniri
        # Integral windup sınırını config'den al, parametre ile geçersiz kılınabilir
        self.integral_limit = integral_limit if integral_limit is not None else getattr(config, 'INTEGRAL_LIMIT', 100.0)
        self.onceki_hata = 0.0
        self.integral = 0.0
        self.son_zaman = time.perf_counter()

    def hesapla(self, hata):
        """
        Verilen hata değerine göre PID çıkışını hesaplar.
        Döngüler arası gerçek zaman farkı (dt) kullanılarak FPS bağımsız çalışır.
        """
        simdi = time.perf_counter()
        dt = simdi - self.son_zaman

        # Aşırı büyük dt değerleri (sistem duraksadığında) türev patlamasına yol açar
        # dt'yi makul bir üst sınırla kırpıyoruz
        if dt <= 0.0:
            dt = 1e-4  # Sıfıra bölme hatasından kaçınmak için mikro bir sapma payı
        elif dt > 0.5:
            dt = 0.5   # 500ms üzerindeki duraklamalarda türev çılgına dönmesin

        self.son_zaman = simdi

        # P (Proportional) - Anlık hata orantısı
        p_cikis = self.kp * hata
        
        # I (Integral) - Zamanla biriken hata (Anti-windup ile korumalı)
        self.integral += hata * dt
        # Integral windup'ı önlemek için integralı sınırlıyoruz
        if self.integral_limit is not None:
            self.integral = max(-self.integral_limit, min(self.integral_limit, self.integral))
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
        self.onceki_hata = 0.0
        self.integral = 0.0
        self.son_zaman = time.perf_counter()
