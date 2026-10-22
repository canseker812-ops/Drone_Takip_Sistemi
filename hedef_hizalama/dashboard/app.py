import sys
import os
import time
import cv2
import streamlit as st

# Targeting dizinini bulup yola ekliyoruz ki import patlamasın
mevcut_dizin = os.path.dirname(os.path.abspath(__file__))
ust_dizin = os.path.abspath(os.path.join(mevcut_dizin, '..'))

if os.path.basename(ust_dizin) == "targeting_system":
    sys.path.append(ust_dizin)
else:
    sys.path.append(os.path.join(ust_dizin, 'targeting_system'))

from takip_sistemi import TakipSistemi

st.set_page_config(page_title="Marmara Rover | Görev Kontrol", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; font-family: 'Inter', 'Segoe UI', sans-serif; }
    .block-container { max-width: 1400px; padding-top: 2rem !important; }
    
    [data-testid="metric-container"], [data-testid="stMetric"] {
        background-color: #161b22 !important; 
        border: 1px solid #30363d !important;
        padding: 15px 20px !important; 
        border-radius: 8px !important; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 14px !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 28px !important; font-weight: 700 !important; }
    
    hr { border-color: #30363d; margin: 1.5rem 0; }
    
    .status-box {
        padding: 18px; border-radius: 8px; text-align: center; font-size: 22px; font-weight: 800;
        letter-spacing: 2px; margin-bottom: 15px; text-transform: uppercase;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    .status-TAKIP { background-color: rgba(46, 160, 67, 0.1); color: #3fb950; border: 2px solid #3fb950; }
    .status-ARANIYOR { background-color: rgba(210, 153, 34, 0.1); color: #d29922; border: 2px solid #d29922; }
    .status-ACIL_DURDUR { background-color: rgba(248, 81, 73, 0.1); color: #f85149; border: 2px solid #f85149; }
    .status-BEKLEMEDE { background-color: rgba(139, 148, 158, 0.1); color: #8b949e; border: 2px solid #8b949e; }
    
    [data-testid="stButton"] > button { 
        height: 60px !important; 
        border-radius: 8px !important; 
        font-weight: 700 !important; 
        font-size: 18px !important; 
        transition: 0.2s !important;
        background-color: #21262d !important; 
        color: #c9d1d9 !important; 
        border: 1px solid #30363d !important;
    }
    [data-testid="stButton"] > button:hover { border-color: #8b949e !important; background-color: #30363d !important; color: #ffffff !important; }
    
    [data-testid="stButton"] > button[kind="primary"] { background-color: #da3633 !important; color: white !important; border: none !important; }
    [data-testid="stButton"] > button[kind="primary"]:hover { background-color: #b62324 !important; }
    </style>
""", unsafe_allow_html=True)

if 'sistem' not in st.session_state:
    st.session_state.sistem = TakipSistemi()
    st.session_state.sistem.baslat()

st.markdown("<h2 style='color: #ffffff; font-weight: 600;'>MARMARA ROVER <span style='color: #8b949e;'>// OTONOM TAKİP KONSOLU</span></h2>", unsafe_allow_html=True)
st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

t1, t2, t3, t4 = st.columns(4)
m_hata_x = t1.empty()
m_hata_y = t2.empty()
m_adim_x = t3.empty()
m_adim_y = t4.empty()

st.markdown("<hr style='margin-top: 15px; margin-bottom: 15px;'>", unsafe_allow_html=True)

cam_col, panel_col = st.columns([7, 3])

with cam_col:
    kamera_alani = st.empty()

with panel_col:
    durum_alani = st.empty() 
    yon_tablosu = st.empty() 
    
    c1, c2 = st.columns(2)
    btn_baslat = c1.button("▶ Start", use_container_width=True)
    btn_durdur = c2.button("⏸ Stop", use_container_width=True)
    
    st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    btn_reset = c3.button("🔄 Reset", use_container_width=True)
    btn_acil = c4.button("🛑 Emergency Stop", type="primary", use_container_width=True)

    # st.rerun() kullanmıyoruz, butona çift basmayı yutuyordu
    if btn_baslat: st.session_state.sistem.baslat()
    if btn_durdur: st.session_state.sistem.durdur()
    if btn_reset: st.session_state.sistem.reset()
    if btn_acil: st.session_state.sistem.acil_durdur()

DURUM_ISIMLERI = {
    "BEKLEMEDE": "SİSTEM BEKLEMEDE",
    "ARANIYOR": "HEDEF ARANIYOR",
    "TAKIP": "HEDEF TAKİPTE",
    "HIZALI": "HEDEF HİZALI",
    "ACIL_DURDUR": "ACİL DURDURMA!",
    "HATA": "SİSTEM HATASI"
}

sayac = 0 
son_durum = "" 
dondurulmus_kare = None 

while True:
    kare, bilgi = st.session_state.sistem.adim()
    
    if kare is None:
        kamera_alani.error("Kamera koptu veya başlatılamadı.")
        break

    mevcut_durum = bilgi["durum"]

    # E-stop'a basılırsa kamerayı kapatmıyoruz, sadece son kareyi ekranda donduruyoruz
    if mevcut_durum == "ACIL_DURDUR":
        if dondurulmus_kare is None:
            dondurulmus_kare = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            
        gosterilecek_kare = dondurulmus_kare.copy()
        cv2.putText(gosterilecek_kare, "ACIL DURDURMA AKTIF - KILITLI", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        kamera_alani.image(gosterilecek_kare, channels="RGB")
    else:
        # Normal akış
        kare_rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
        dondurulmus_kare = None 
        kamera_alani.image(kare_rgb, channels="RGB")
    
    # Durum paneli güncellemeleri
    if mevcut_durum != son_durum or mevcut_durum == "ACIL_DURDUR":
        gosterilecek_metin = DURUM_ISIMLERI.get(mevcut_durum, mevcut_durum)
        
        css_class = "status-BEKLEMEDE"
        if mevcut_durum in ["TAKIP", "HIZALI"]: css_class = "status-TAKIP"
        elif mevcut_durum == "ARANIYOR": css_class = "status-ARANIYOR"
        elif mevcut_durum in ["ACIL_DURDUR", "HATA"]: css_class = "status-ACIL_DURDUR"
        
        durum_alani.markdown(f"<div class='status-box {css_class}'>{gosterilecek_metin}</div>", unsafe_allow_html=True)
        son_durum = mevcut_durum  
        
    # Arayüz kasmaması için UI güncellemelerini her 3 karede bir yapıyoruz
    if sayac % 3 == 0 or mevcut_durum == "ACIL_DURDUR":
        m_hata_x.metric(label="PİD Error (Yaw X)", value=f"{bilgi['hata_x']} px")
        m_hata_y.metric(label="PİD Error (Pitch Y)", value=f"{bilgi['hata_y']} px")
        m_adim_x.metric(label="Step Motor Data (X)", value=f"{bilgi['adim_x']}")
        m_adim_y.metric(label="Step Motor Data (Y)", value=f"{bilgi['adim_y']}")

        if mevcut_durum == "ARANIYOR":
            x_yon = "<span style='color:#d29922;'>Hedef Aranıyor 🔍</span>"
            y_yon = "<span style='color:#d29922;'>Hedef Aranıyor 🔍</span>"
        elif mevcut_durum == "ACIL_DURDUR":
            x_yon = "<span style='color:#f85149;'>Sistem Kilitli 🛑</span>"
            y_yon = "<span style='color:#f85149;'>Sistem Kilitli 🛑</span>"
        else:
            if bilgi['adim_x'] > 0: x_yon = "<span style='color:#3fb950;'>+X Yönünde ➡️</span>"
            elif bilgi['adim_x'] < 0: x_yon = "<span style='color:#f85149;'>-X Yönünde ⬅️</span>"
            else: x_yon = "<span style='color:#8b949e;'>Merkezde 🟢</span>"

            if bilgi['adim_y'] > 0: y_yon = "<span style='color:#d29922;'>-Y Yönünde ⬇️</span>"
            elif bilgi['adim_y'] < 0: y_yon = "<span style='color:#58a6ff;'>+Y Yönünde ⬆️</span>"
            else: y_yon = "<span style='color:#8b949e;'>Merkezde 🟢</span>"

        tablo_html = f"""
        <div style='background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);'>
            <div style='color: #8b949e; font-size: 13px; font-weight: 700; margin-bottom: 12px; letter-spacing: 1px;'>📍 HEDEF HAREKET VEKTÖRÜ</div>
            <div style='display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px;'>
                <span style='color: #c9d1d9; font-weight: 600;'>Yatay Eksen (Yaw):</span>
                <span style='font-weight: 700;'>{x_yon}</span>
            </div>
            <div style='display: flex; justify-content: space-between; font-size: 16px;'>
                <span style='color: #c9d1d9; font-weight: 600;'>Dikey Eksen (Pitch):</span>
                <span style='font-weight: 700;'>{y_yon}</span>
            </div>
        </div>
        """
        yon_tablosu.markdown(tablo_html, unsafe_allow_html=True)
        
    sayac += 1
    
    # Streamlit ve OpenCV'nin CPU'yu boğmaması için ufak bir bekleme ekliyoruz, yoksa UI kitlenir
    cv2.waitKey(1)
    time.sleep(0.03)