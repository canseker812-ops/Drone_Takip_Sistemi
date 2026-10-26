import sys
import os
import time
import cv2
import streamlit as st

# Targeting dizinini bulup yola ekliyoruz ki import patlamasın
mevcut_dizin = os.path.dirname(os.path.abspath(__file__))
ust_dizin    = os.path.abspath(os.path.join(mevcut_dizin, '..'))

hedefleme_dizini = os.path.join(ust_dizin, 'targeting_system')
if hedefleme_dizini not in sys.path:
    sys.path.insert(0, hedefleme_dizini)

from takip_sistemi import TakipSistemi
import config as _cfg

# ------------------------------------------------------------------ #
#  Sayfa Yapılandırması                                              #
# ------------------------------------------------------------------ #
st.set_page_config(
    page_title="Marmara Rover | Görev Kontrol",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------ #
#  Global CSS                                                        #
# ------------------------------------------------------------------ #
st.markdown("""
<style>
/* ── Streamlit chrome'u tamamen gizle ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]        { display: none !important; }

/* ── Sayfa zeminini tam kapla, scroll yok ── */
html, body, .stApp {
    height: 100vh !important;
    overflow: hidden !important;
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Ana içerik bloğu: scrollsuz, sıkı padding ── */
.main .block-container {
    padding: 0.4rem 0.8rem 0 0.8rem !important;
    max-width: 100% !important;
    height: calc(100vh - 0px) !important;
    overflow: hidden !important;
}

/* ── Kamera görselini tam olarak viewport'a sığdır ── */
[data-testid="stImage"] {
    line-height: 0 !important;
    display: block !important;
}
[data-testid="stImage"] img {
    width: 100% !important;
    max-height: calc(100vh - 55px) !important;
    object-fit: contain !important;
    border-radius: 8px !important;
    background: #000 !important;
    display: block !important;
}

/* ── Sidebar: sabit genişlik, tam yükseklik, scroll içinde ── */
section[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #30363d !important;
    min-width: 290px !important;
    max-width: 290px !important;
    height: 100vh !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
section[data-testid="stSidebar"] .block-container {
    padding: 1rem 0.8rem 1.5rem 0.8rem !important;
    overflow: visible !important;
    height: auto !important;
}

/* ── Sidebar logo ── */
.sidebar-logo {
    text-align: center;
    padding: 4px 0 14px 0;
    border-bottom: 1px solid #30363d;
    margin-bottom: 12px;
}
.sidebar-logo .logo-title { font-size: 17px; font-weight: 800; color: #e6edf3; letter-spacing: 2px; }
.sidebar-logo .logo-sub   { font-size: 10px; color: #8b949e; letter-spacing: 1px; margin-top: 2px; }

/* ── Durum badge ── */
.status-box {
    padding: 10px 8px;
    border-radius: 8px;
    text-align: center;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 12px;
    box-shadow: inset 0 0 16px rgba(0,0,0,0.4);
}
.status-TAKIP       { background: rgba(46,160,67,0.12);  color:#3fb950; border:2px solid #3fb950; }
.status-HIZALI      { background: rgba(46,160,67,0.20);  color:#56d364; border:2px solid #56d364; }
.status-ARANIYOR    { background: rgba(210,153,34,0.12); color:#d29922; border:2px solid #d29922; }
.status-BEKLEMEDE   { background: rgba(139,148,158,0.10);color:#8b949e; border:2px solid #30363d; }
.status-ACIL_DURDUR { background: rgba(248,81,73,0.15);  color:#f85149; border:2px solid #f85149; }
.status-HATA        { background: rgba(248,81,73,0.15);  color:#f85149; border:2px solid #f85149; }

/* ── Metrik kartları ── */
[data-testid="metric-container"],
[data-testid="stMetric"] {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    padding: 8px 10px !important;
    border-radius: 7px !important;
}
[data-testid="stMetricLabel"] {
    color: #8b949e !important; font-size: 10px !important; font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #e6edf3 !important; font-size: 18px !important; font-weight: 700 !important;
}

/* ── Bölüm başlıkları ── */
.section-label {
    color: #8b949e;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 12px 0 6px 0;
    padding-bottom: 3px;
    border-bottom: 1px solid #21262d;
}

/* ── Butonlar ── */
[data-testid="stButton"] > button {
    height: 40px !important;
    border-radius: 7px !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    transition: all 0.15s ease !important;
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    width: 100% !important;
}
[data-testid="stButton"] > button:hover {
    border-color: #58a6ff !important;
    background-color: #1f3451 !important;
    color: #ffffff !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background-color: #b91c1c !important;
    color: #ffffff !important;
    border: 1px solid #f85149 !important;
    font-size: 13px !important;
    height: 46px !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background-color: #991b1b !important;
    box-shadow: 0 0 10px rgba(248,81,73,0.4) !important;
}

/* ── Hareket vektörü kartı ── */
.vector-card {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 7px;
    padding: 9px 12px;
    margin-bottom: 10px;
}
.vector-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    font-size: 12px;
}
.vector-label { color: #8b949e; font-weight: 500; }

/* ── MCU log ── */
.mcu-box {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 9px;
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: #3fb950;
    min-height: 24px;
    word-break: break-all;
}

/* ── Kamera başlığı etiketi ── */
.cam-label {
    color: #8b949e;
    font-size: 10px;
    letter-spacing: 1px;
    margin: 0 0 3px 2px;
    font-weight: 600;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ #
#  Yardımcı fonksiyon: Kareyi görüntüleme için boyutlandır             #
# ------------------------------------------------------------------ #
def goruntu_boyutlandir(img_rgb):
    max_y = getattr(_cfg, 'GORUNTU_MAX_Y', 0)
    if max_y <= 0:
        return img_rgb
    h, w = img_rgb.shape[:2]
    if h <= max_y:
        return img_rgb
    oran  = max_y / h
    yeni_w = int(w * oran)
    return cv2.resize(img_rgb, (yeni_w, max_y), interpolation=cv2.INTER_AREA)

# ------------------------------------------------------------------ #
#  Session State                                                     #
# ------------------------------------------------------------------ #
if 'sistem' not in st.session_state:
    st.session_state.sistem = TakipSistemi()

# ------------------------------------------------------------------ #
#  Durum sabitleri                                                   #
# ------------------------------------------------------------------ #
DURUM_ISIMLERI = {
    "BEKLEMEDE":   "⏸  SİSTEM BEKLEMEDE",
    "ARANIYOR":    "🔍  HEDEF ARANIYOR",
    "TAKIP":       "🎯  HEDEF TAKİPTE",
    "HIZALI":      "✅  HEDEF HİZALI",
    "ACIL_DURDUR": "🛑  ACİL DURDURMA!",
    "HATA":        "❌  SİSTEM HATASI",
}

def durum_css(durum):
    return {
        "TAKIP":       "status-TAKIP",
        "HIZALI":      "status-HIZALI",
        "ARANIYOR":    "status-ARANIYOR",
        "ACIL_DURDUR": "status-ACIL_DURDUR",
        "HATA":        "status-ACIL_DURDUR",
    }.get(durum, "status-BEKLEMEDE")

# ------------------------------------------------------------------ #
#  SIDEBAR                                                           #
# ------------------------------------------------------------------ #
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="logo-title">🎯 MARMARA ROVER</div>
        <div class="logo-sub">OTONOM TAKİP KONSOLU</div>
    </div>
    """, unsafe_allow_html=True)

    durum_alani = st.empty()

    # Kontrol Butonları
    st.markdown("<div class='section-label'>🕹️ Sistem Kontrolü</div>", unsafe_allow_html=True)
    col_s, col_d = st.columns(2)
    btn_baslat = col_s.button("▶  START", use_container_width=True)
    btn_durdur = col_d.button("⏸  STOP",  use_container_width=True)
    st.markdown("<div style='margin:4px 0'></div>", unsafe_allow_html=True)
    btn_reset = st.button("🔄  Sıfırla (Reset)", use_container_width=True)
    st.markdown("<div style='margin:3px 0'></div>", unsafe_allow_html=True)
    btn_acil  = st.button("🛑  ACİL DURDURMA (E-STOP)", type="primary", use_container_width=True)

    # Buton olayları
    if btn_baslat: st.session_state.sistem.baslat()
    if btn_durdur: st.session_state.sistem.durdur()
    if btn_reset:  st.session_state.sistem.reset()
    if btn_acil:   st.session_state.sistem.acil_durdur()

    # ── JOG: Manuel Eksen Kontrolü (Sabit Adımlı) ──
    st.markdown("<div class='section-label'>🎮 JOG KONTROLÜ (X:10 | Y:5)</div>", unsafe_allow_html=True)

    # Yukarı: Y (5 adım yukarı / -Y)
    bos1, yukari, bos2 = st.columns(3)
    with yukari:
        if st.button("⬆️\n+Y", key="jog_yukari", use_container_width=True):
            if hasattr(st.session_state.sistem, 'seri') and st.session_state.sistem.seri.bagli:
                st.session_state.sistem.seri.gonder("<0,-5>")

    # Sol: -X (10 adım) | Sağ: +X (10 adım)
    sol, bos3, sag = st.columns(3)
    with sol:
        if st.button("⬅️\n+X", key="jog_sol", use_container_width=True):
            if hasattr(st.session_state.sistem, 'seri') and st.session_state.sistem.seri.bagli:
                st.session_state.sistem.seri.gonder("<10,0>")
    with sag:
        if st.button("➡️\n-X", key="jog_sag", use_container_width=True):
            if hasattr(st.session_state.sistem, 'seri') and st.session_state.sistem.seri.bagli:
                st.session_state.sistem.seri.gonder("<-10,0>")

    # Aşağı: Y (5 adım aşağı / +Y)
    bos4, asagi, bos5 = st.columns(3)
    with asagi:
        if st.button("⬇️\n-Y", key="jog_asagi", use_container_width=True):
            if hasattr(st.session_state.sistem, 'seri') and st.session_state.sistem.seri.bagli:
                st.session_state.sistem.seri.gonder("<0,5>")

    # PID & Motor Metrikleri
    st.markdown("<div class='section-label'>📊 PID & Motor Verileri</div>", unsafe_allow_html=True)
    ma, mb = st.columns(2)
    m_hata_x = ma.empty()
    m_hata_y = mb.empty()
    mc, md = st.columns(2)
    m_adim_x = mc.empty()
    m_adim_y = md.empty()

    # Sinyal durumu
    st.markdown("<div class='section-label'>📡 Hedef Sinyal</div>", unsafe_allow_html=True)
    kayip_bar = st.empty()

    # Hareket Vektörü
    st.markdown("<div class='section-label'>📍 Hareket Vektörü</div>", unsafe_allow_html=True)
    yon_alani = st.empty()

    # MCU Log
    st.markdown("<div class='section-label'>🔌 MCU Bağlantısı</div>", unsafe_allow_html=True)
    seri_durum = st.empty()
    mcu_log    = st.empty()

# ------------------------------------------------------------------ #
#  ANA ALAN — sadece kamera                                          #
# ------------------------------------------------------------------ #
st.markdown("<div class='cam-label'>Canlı Kamera Akışı</div>", unsafe_allow_html=True)
kamera_alani = st.empty()

# ------------------------------------------------------------------ #
#  Ana Döngü                                                         #
# ------------------------------------------------------------------ #
sayac          = 0
son_durum      = ""
dondurulmus_kare = None

while True:
    kare, bilgi = st.session_state.sistem.adim()

    if kare is None:
        kamera_alani.error(
            f"⚠️ Kamera koptu veya başlatılamadı. "
            f"Hata: **{bilgi.get('hata_mesaji', 'Bilinmiyor')}**"
        )
        time.sleep(0.5)
        break

    mevcut_durum = bilgi["durum"]

    # ── Kamera Görüntüsü ──────────────────────────────────────────
    if mevcut_durum == "ACIL_DURDUR":
        if dondurulmus_kare is None:
            dondurulmus_kare = goruntu_boyutlandir(
                cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            )
        gosterilecek = dondurulmus_kare.copy()
        overlay = gosterilecek.copy()
        h_g, w_g = overlay.shape[:2]
        cv2.rectangle(overlay, (0, 0), (w_g, 52), (30, 0, 0), -1)
        cv2.addWeighted(overlay, 0.75, gosterilecek, 0.25, 0, gosterilecek)
        cv2.putText(gosterilecek, "!! ACIL DURDURMA AKTIF - KILITLI !!",
                    (10, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 70, 70), 2)
        kamera_alani.image(gosterilecek, channels="RGB", use_container_width=True)
    else:
        kare_rgb = goruntu_boyutlandir(cv2.cvtColor(kare, cv2.COLOR_BGR2RGB))
        dondurulmus_kare = None
        kamera_alani.image(kare_rgb, channels="RGB", use_container_width=True)

    # ── Durum Badge ────────────────────────────────────────────────
    if mevcut_durum != son_durum or mevcut_durum in ("ACIL_DURDUR", "HATA"):
        metin = DURUM_ISIMLERI.get(mevcut_durum, mevcut_durum)
        durum_alani.markdown(
            f"<div class='status-box {durum_css(mevcut_durum)}'>{metin}</div>",
            unsafe_allow_html=True
        )
        son_durum = mevcut_durum

    # ── Sidebar metrikleri (her 3 karede bir) ─────────────────────
    if sayac % 3 == 0 or mevcut_durum in ("ACIL_DURDUR", "HATA"):

        m_hata_x.metric("Hata X (Yaw)",  f"{bilgi['hata_x']:+d} px")
        m_hata_y.metric("Hata Y (Pitch)", f"{bilgi['hata_y']:+d} px")
        m_adim_x.metric("Adım X",         f"{bilgi['adim_x']:+d}")
        m_adim_y.metric("Adım Y",         f"{bilgi['adim_y']:+d}")

        # Kayıp sayacı
        kayip = bilgi.get('kayip_sayaci', 0)
        esik  = getattr(_cfg, 'KAYIP_ESIGI', 15)
        if mevcut_durum == "ARANIYOR":
            kayip_bar.markdown(
                f"<div style='font-size:11px;color:#d29922;margin-bottom:2px;'>"
                f"Sinyal Kaybı: {kayip} / {esik} kare</div>",
                unsafe_allow_html=True
            )
        elif mevcut_durum in ("TAKIP", "HIZALI"):
            kayip_bar.markdown(
                "<div style='font-size:11px;color:#3fb950;margin-bottom:2px;'>"
                "✔ Hedef Kilitli</div>", unsafe_allow_html=True
            )
        else:
            kayip_bar.markdown(
                "<div style='font-size:11px;color:#8b949e;margin-bottom:2px;'>"
                "—</div>", unsafe_allow_html=True
            )

        # Yön göstergesi
        if mevcut_durum == "ARANIYOR":
            x_yon = "<span style='color:#d29922;'>Hedef Aranıyor 🔍</span>"
            y_yon = "<span style='color:#d29922;'>Hedef Aranıyor 🔍</span>"
        elif mevcut_durum == "ACIL_DURDUR":
            x_yon = "<span style='color:#f85149;'>Sistem Kilitli 🛑</span>"
            y_yon = "<span style='color:#f85149;'>Sistem Kilitli 🛑</span>"
        elif mevcut_durum == "BEKLEMEDE":
            x_yon = "<span style='color:#8b949e;'>—</span>"
            y_yon = "<span style='color:#8b949e;'>—</span>"
        else:
            x_yon = (
                "<span style='color:#3fb950;'>➡️ +X Sağ</span>"    if bilgi['adim_x'] > 0 else
                "<span style='color:#f85149;'>⬅️ -X Sol</span>"    if bilgi['adim_x'] < 0 else
                "<span style='color:#58a6ff;'>🟢 Merkezde</span>"
            )
            y_yon = (
                "<span style='color:#d29922;'>⬇️ -Y Aşağı</span>"  if bilgi['adim_y'] > 0 else
                "<span style='color:#58a6ff;'>⬆️ +Y Yukarı</span>" if bilgi['adim_y'] < 0 else
                "<span style='color:#58a6ff;'>🟢 Merkezde</span>"
            )

        yon_alani.markdown(f"""
        <div class="vector-card">
            <div class="vector-row">
                <span class="vector-label">Yatay (Yaw)</span>
                <span style="font-weight:700">{x_yon}</span>
            </div>
            <div style="border-top:1px solid #21262d;margin:3px 0"></div>
            <div class="vector-row">
                <span class="vector-label">Dikey (Pitch)</span>
                <span style="font-weight:700">{y_yon}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # MCU
        seri_renk  = "#3fb950" if bilgi["seri_bagli"] else "#f85149"
        seri_metin = "🟢 BAĞLI" if bilgi["seri_bagli"] else "🔴 BAĞLI DEĞİL"
        seri_durum.markdown(
            f"<div style='font-size:11px;color:{seri_renk};font-weight:700;"
            f"margin-bottom:3px;'>{seri_metin}</div>", unsafe_allow_html=True
        )
        mcu_log.markdown(
            f"<div class='mcu-box'>▶ {bilgi.get('mcu_cevap', '') or '—'}</div>",
            unsafe_allow_html=True
        )

    sayac += 1
    time.sleep(0.03)