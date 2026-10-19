import time


class PID:
    """Basit PID kontrolcü. Girdi: piksel hatası. Çıktı: adım sayısı."""

    def __init__(self, kp, ki=0.0, kd=0.0, cikis_siniri=20, integral_siniri=100.0, turev_filtre=0.3):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.cikis_siniri = cikis_siniri        # çıkış -sınır ile +sınır arasında kalır
        self.integral_siniri = integral_siniri  # anti-windup: integral şişmesin
        self.turev_filtre = turev_filtre        # 0-1 arası, küçük = daha yumuşak türev
        self.sifirla()

    def sifirla(self):
        """Hedef kaybı, durdurma ve acil durdurmada çağrılır."""
        self.integral = 0.0
        self.onceki_hata = 0.0
        self.onceki_zaman = None
        self.turev = 0.0

    def hesapla(self, hata, dt=None):
        # dt verilmezse gerçek zamandan hesapla (simülasyonda elle verilir)
        simdi = time.perf_counter()
        if dt is None and self.onceki_zaman is not None:
            dt = simdi - self.onceki_zaman

        oran = self.kp * hata
        integral_terimi = 0.0
        turev_terimi = 0.0

        # İlk çağrıda dt yok, çok küçük dt ise türev patlar: ikisinde de atla
        if dt is not None and dt > 1e-3:
            self.integral += hata * dt
            self.integral = max(-self.integral_siniri, min(self.integral_siniri, self.integral))
            ham_turev = (hata - self.onceki_hata) / dt
            self.turev = (1 - self.turev_filtre) * self.turev + self.turev_filtre * ham_turev
            integral_terimi = self.ki * self.integral
            turev_terimi = self.kd * self.turev

        cikis = oran + integral_terimi + turev_terimi
        cikis = max(-self.cikis_siniri, min(self.cikis_siniri, cikis))

        self.onceki_hata = hata
        self.onceki_zaman = simdi
        return cikis