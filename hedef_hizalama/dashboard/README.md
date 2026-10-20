\# 🖥️ Görev Kontrol Merkezi (Dashboard)



Operatörün otonom sistemi izlemesi ve yönetmesi için Streamlit tabanlı, düşük gecikmeli Web-UI arayüzüdür.



\## ✨ Özellikler

\- \*\*Gerçek Zamanlı Görüntü (HUD):\*\* Hedefin OpenCV ile işaretlendiği, 30 FPS canlı kamera beslemesi.

\- \*\*Dinamik Telemetri:\*\* PID hedef hatalarını (Yaw, Pitch) ve Motor çıktı adımlarını gösteren siber-temalı metrik kartları.

\- \*\*Durumsal Farkındalık:\*\* Sistemin durumunu (ARANIYOR, TAKİPTE, ACİL DURDURMA) renk kodlarıyla anlık gösteren bildirim rozeti.

\- \*\*Kontrol Paneli:\*\* ISO standartlarına uygun renk kodlamalı Başlat, Durdur, Sıfırla ve anlık kesme (Interrupt) sağlayan Acil Durdurma komutları.



\*\*Kullanım:\*\* `streamlit run dashboard/app.py`

