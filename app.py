import os
import time
import random
import math
import pandas as pd
import streamlit as st
from datetime import datetime
from google import genai
from google.genai import types

st.set_page_config(page_title="LearnSphere AI Hub", layout="wide", initial_sidebar_state="expanded")

# --- Müasir Slate Dark & Indigo Palitrası ---
st.markdown(
    """
    <style>
    /* 1. Ümumi Fonlar: Əsas Sağ Fon #0F172A */
    .stApp {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    header[data-testid="stHeader"] button {
        color: #F8FAFC !important;
        background-color: rgba(30, 41, 59, 0.6) !important;
        border-radius: 50% !important;
    }
    header[data-testid="stHeader"] svg {
        fill: #F8FAFC !important;
    }

    /* Sol Sidebar Fonu: #1E1B4B */
    section[data-testid="stSidebar"] {
        background-color: #1E1B4B !important;
        border-right: 1px solid #312E81 !important;
    }

    section[data-testid="stSidebar"] button[kind="header"] {
        color: #E0E7FF !important;
    }
    section[data-testid="stSidebar"] button[kind="header"] svg {
        fill: #E0E7FF !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #E0E7FF !important;
        font-weight: 700 !important;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label span {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {
        border-color: #6366F1 !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
        background-color: #0F172A !important;
        border: 1px solid #312E81 !important;
        border-radius: 8px !important;
    }

    section[data-testid="stSidebar"] input {
        color: #F1F5F9 !important;
        background-color: transparent !important;
    }

    section[data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #F1F5F9 !important;
    }

    section[data-testid="stSidebar"] button[tabindex="-1"] {
        color: #94A3B8 !important;
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] button[tabindex="-1"]:hover {
        color: #FFFFFF !important;
    }

    /* Düymələr */
    .start-btn button {
        background-color: #10B981 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .start-btn button:hover {
        background-color: #059669 !important;
    }

    .stop-btn button {
        background-color: #EF4444 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stop-btn button:hover {
        background-color: #DC2626 !important;
    }

    /* Başlıqlar */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #FFFFFF !important;
        text-shadow: 0 0 20px rgba(99, 102, 241, 0.6), 0 0 40px rgba(56, 189, 248, 0.4);
        margin-bottom: 4px;
    }
    .hero-subtitle {
        color: #64748B !important;
        font-size: 0.95rem;
        margin-bottom: 24px;
    }
    .section-title {
        color: #F8FAFC !important;
        font-size: 1.3rem;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 16px;
    }

    /* Metrika Kartları */
    div[data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
    }

    /* Mentor Bloku */
    .mentor-container {
        background-color: #1E1B4B;
        border: 1px solid #312E81;
        border-left: 4px solid #6366F1;
        border-radius: 12px;
        padding: 18px 24px;
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }
    .mentor-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .mentor-header-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .mentor-title-left {
        font-size: 1.3rem;
        font-weight: 700;
        color: #A5B4FC !important;
        margin: 0;
    }
    .compact-timer-tag {
        font-size: 0.95rem;
        font-weight: 700;
        color: #FCD34D !important;
        background-color: #312E81;
        padding: 4px 14px;
        border-radius: 8px;
        border: 1px solid #4338CA;
    }
    .status-badge-online {
        font-size: 0.8rem;
        font-weight: 600;
        color: #34D399;
        background-color: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(52, 211, 153, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
    }
    .status-badge-offline {
        font-size: 0.8rem;
        font-weight: 600;
        color: #FBBF24;
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(251, 191, 36, 0.3);
        padding: 4px 10px;
        border-radius: 20px;
    }
    .mentor-msg-text {
        font-size: 1rem;
        color: #CBD5E1 !important;
        line-height: 1.6;
        margin: 0;
    }

    .clear-btn button {
        background-color: #334155 !important;
        color: #E2E8F0 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .clear-btn button:hover {
        background-color: #475569 !important;
        color: #FFFFFF !important;
    }

    .empty-history-box {
        background-color: #1E293B;
        border: 1px dashed #475569;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: #94A3B8;
        font-size: 0.95rem;
    }

    div[data-testid="stDataFrame"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 8px !important;
    }

    div.stAlert {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        color: #CBD5E1 !important;
        border-radius: 10px !important;
    }
    div.stAlert p {
        color: #CBD5E1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="hero-title">LearnSphere</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">STEAM Layihəsi | Fizioloji Metabolizm, Akustik Analitika & Sessiya Keyfiyyəti</div>', unsafe_allow_html=True)

# API Müştərisi
api_key = st.secrets.get("GEMINI_API_KEY", None)
client = genai.Client(api_key=api_key) if api_key else None

# --- Sessiya Yaddaşı ---
if "focus_history" not in st.session_state:
    st.session_state.focus_history = []
if "session_running" not in st.session_state:
    st.session_state.session_running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "last_report" not in st.session_state:
    st.session_state.last_report = None
if "data_history" not in st.session_state:
    st.session_state.data_history = []
if "session_penalty" not in st.session_state:
    st.session_state.session_penalty = 0.0

# 3 Saniyəlik Hədd İzləmə Yaddaşı
if "trigger_timers" not in st.session_state:
    st.session_state.trigger_timers = {"co2": 0, "sound": 0, "temp": 0, "light": 0}
if "cached_ai_response" not in st.session_state:
    st.session_state.cached_ai_response = None
if "last_active_factor" not in st.session_state:
    st.session_state.last_active_factor = None

# --- Sol Panel Parametrləri ---
st.sidebar.markdown("### ⚙️ Mühit Parametrləri")

# ƏLLƏ SEÇİLƏN SİSTEM REJİMİ
system_mode = st.sidebar.radio(
    "Mentor Rejimi:",
    ["🟢 Onlayn (Gemini AI)", "🟡 Oflayn (Lokal Qaydalar)"],
    index=0
)
is_offline_manual = (system_mode == "🟡 Oflayn (Lokal Qaydalar)")

st.sidebar.markdown("---")
mode = st.sidebar.radio("Otaq Formatı:", ["👤 Fərdi Kabinə (1 nəfər)", "👥 Qrup Otağı (Çox nəfərlik)"])

if mode == "👤 Fərdi Kabinə (1 nəfər)":
    gender = st.sidebar.selectbox("Cins:", ["Kişi", "Qadın"])
    weight = st.sidebar.number_input("Çəki (kq)", 40, 130, 75)
    men_count = 1 if gender == "Kişi" else 0
    women_count = 1 if gender == "Qadın" else 0
    men_avg_weight = weight if men_count else 0
    women_avg_weight = weight if women_count else 0
    default_vol = 8
else:
    col_m, col_w = st.sidebar.columns(2)
    with col_m:
        men_count = st.number_input("Kişi sayı", 0, 30, 2)
        men_avg_weight = st.number_input("Kişi orta çəki", 40, 120, 75)
    with col_w:
        women_count = st.number_input("Qadın sayı", 0, 30, 2)
        women_avg_weight = st.number_input("Qadın orta çəki", 40, 120, 60)
    default_vol = 25

total_people = max(men_count + women_count, 1)
room_vol = st.sidebar.number_input("Otaq Həcmi (m³)", 3, 300, default_vol)

st.sidebar.markdown("---")

# --- 1. Təbii Ventilyasiyalı və Dinamik Bioloji Hesablama ---
def calculate_advanced_bio(men_count, men_weight, women_count, women_weight, room_volume_m3, elapsed_minutes):
    o2_men = (men_count * men_weight * 3.5) / 1000
    o2_women = (women_count * women_weight * 3.2) / 1000
    co2_rate_per_min = (o2_men + o2_women) * 0.85

    # Təbii hava infiltrasiyası (saatda 0.4 hava dəyişimi)
    ach = 0.40 / 60.0

    # Tarazlıq modeli (CO2 sonsuz artmır, otaq həcmi ilə sabitləşir)
    net_rise = (co2_rate_per_min / (room_volume_m3 * 1000 * ach)) * (1 - math.exp(-ach * elapsed_minutes)) * 1_000_000

    # Təbii sensor titrəməsi (±5 ppm)
    noise = random.uniform(-5.0, 5.0)
    current_co2 = round(420.0 + net_rise + noise, 1)

    o2_drop = (net_rise / 1_000_000) * 100 * 1.15
    current_o2 = round(max(20.95 - o2_drop, 18.5), 2)

    return max(current_co2, 415.0), current_o2

# --- 2. Oflayn Qayda Əsaslı Məsləhət Bankı ---
OFFLINE_EXPERT_RULES = {
    "co2": "ASHRAE 62.1 həddi aşıldı (>1000 ppm). Karbon qazı beyin qan dövranında oksigeni azaldır. Dərhal pəncərəni açaraq təmiz hava axını yaradın.",
    "sound": "Akustik küy həddi aşıldı (>70 dB). Qəfil səs partlayışları riyazi və analitik diqqəti 40% zəiflədir. Səs izolyasiyası təmin edin.",
    "temp": "Termal komfort pozuldu (≥26°C, Məqalə 8). İstilik artımı zehni yorğunluğu sürətləndirir. Otaq temperaturunu 24°C səviyyəsinə salın.",
    "light": "Vizual işıqlanma qeyri-kafidir (<500 Lux, Məqalə 11). Göz büllurunun gərginliyini azaltmaq üçün masanın işıqlandırmasını artırın."
}

# --- 3. Məsləhət Generatoru (Manual Rejimə Əsaslanan) ---
def get_smart_advice(factor, value, force_offline):
    if force_offline or not client:
        return OFFLINE_EXPERT_RULES.get(factor, "Mühit normativləri pozuldu. Parametrləri tənzimləyin.")

    prompts = {
        "co2": f"Otaqda CO2 konsentrasiyası {value} ppm oldu və 3 saniyədir yüksəkdir (ASHRAE 62.1 norması 1000 ppm). Tələbəyə dərhal tətbiq edəcəyi 1 cümləlik akademik tövsiyə yaz.",
        "sound": f"Dərs otağında səs küyü {value} dB oldu və 3 saniyədir davam edir (Norma <= 70 dB). Diqqəti bərpa etmək üçün 1 cümləlik qısa tövsiyə yaz.",
        "temp": f"Otaq temperaturu {value} °C oldu və 3 saniyədir yüksəkdir (24°C ideal, ≥26°C koqnitiv ləngimə). Tələbəyə 1 cümləlik sərinlənmə tövsiyəsi ver.",
        "light": f"İş masasında işıq {value} Lux oldu və 3 saniyədir zəifdir (Optimal: 500-1000 Lux). Vizual yorğunluğu önləmək üçün 1 cümləlik tövsiyə ver."
    }

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompts.get(factor, "Mühit normadan kənara çıxdı. Qısa tövsiyə ver."),
            config=types.GenerateContentConfig(temperature=0.7)
        )
        return res.text.strip() if res.text else OFFLINE_EXPERT_RULES.get(factor)
    except Exception:
        return OFFLINE_EXPERT_RULES.get(factor, "Mühit normativləri pozuldu. Otaq şəraitini tənzimləyin.")

# --- 4. Sessiya Sonu Yekun Hesabat Rəyi ---
def get_session_summary(duration_str, score, avg_co2, max_db, avg_lux, avg_temp, total_people, force_offline):
    offline_summary = (
        f"Sessiya {score}/100 fokus balı ilə başa çatdı ({duration_str}). "
        f"Orta göstəricilər: {avg_co2} ppm CO₂, {avg_temp} °C temperatur və {avg_lux} Lux işıq. "
        f"Zehni məhsuldarlığı qorumaq üçün ASHRAE 62.1 standartına uyğun təmiz hava dövranını təmin edin."
    )

    if force_offline or not client:
        return offline_summary

    prompt = f"""
    Sən fərdi dərs mentorusan. Sessiya yenicə bitdi.
    Müddət: {duration_str}, Fokus Balı: {score}/100, Orta CO2: {avg_co2} ppm, Maks Küy: {max_db} dB, İşıq: {avg_lux} lx, Temp: {avg_temp} °C.
    Tələbəyə qısa, motivasiyaedici və 1 elmi erqonomik tövsiyə verən maksimum 2 cümlə yaz.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.7)
        )
        return response.text.strip() if response.text else offline_summary
    except Exception:
        return offline_summary

# Düymə İdarəetməsi
if not st.session_state.session_running:
    st.sidebar.markdown('<div class="start-btn">', unsafe_allow_html=True)
    if st.sidebar.button("🟢 Sessiyanı Başlat", use_container_width=True):
        st.session_state.session_running = True
        st.session_state.start_time = time.time()
        st.session_state.last_report = None
        st.session_state.session_penalty = 0.0
        st.session_state.data_history = []
        st.session_state.trigger_timers = {"co2": 0, "sound": 0, "temp": 0, "light": 0}
        st.session_state.cached_ai_response = None
        st.session_state.last_active_factor = None
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="stop-btn">', unsafe_allow_html=True)
    if st.sidebar.button("🔴 Sessiyanı Bitir", use_container_width=True):
        st.session_state.session_running = False
        
        elapsed_sec = max(int(time.time() - (st.session_state.start_time or time.time())), 1)
        mins, secs = divmod(elapsed_sec, 60)
        total_time_str = f"{mins:02d} dəq {secs:02d} san"

        if st.session_state.data_history:
            df_final = pd.DataFrame(st.session_state.data_history)
            avg_co2 = int(df_final["CO2 (ppm)"].mean())
            max_db = int(df_final["Səs (dB)"].max())
            avg_lux = int(df_final["İşıq (Lux)"].mean())
            avg_temp = round(df_final["Temperatur (°C)"].mean(), 1)
            last_co2 = df_final["CO2 (ppm)"].iloc[-1]
        else:
            avg_co2 = 420
            max_db = 40
            avg_lux = 500
            avg_temp = 24.0
            last_co2 = 420.0

        final_score = int(max(100 - st.session_state.session_penalty, 40))
        ai_final_feedback = get_session_summary(total_time_str, final_score, avg_co2, max_db, avg_lux, avg_temp, total_people, is_offline_manual)

        st.session_state.focus_history.append({
            "Tarix": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Rejim": mode,
            "İştirakçı": total_people,
            "Müddət": total_time_str,
            "Skor": f"{final_score}/100 ⭐",
            "Son CO₂": f"{last_co2} ppm",
            "Ort. Temp": f"{avg_temp} °C"
        })

        st.session_state.last_report = {
            "score": final_score,
            "time": total_time_str,
            "feedback": ai_final_feedback
        }

        st.session_state.start_time = None
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

# --- CANLI PANEL ---
@st.fragment(run_every=1.0 if st.session_state.session_running else None)
def render_live_dashboard():
    st.markdown(f'<div class="section-title">📊 Canlı Göstəricilər ({total_people} Nəfər)</div>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)

    if st.session_state.session_running:
        step = len(st.session_state.data_history) + 1
        
        # Real keçən zaman üzərindən dinamika (test üçün 1 san = 4 san miqyasında sürətləndirilir)
        elapsed_total_sec = max(int(time.time() - (st.session_state.start_time or time.time())), 1)
        simulated_minutes = (elapsed_total_sec * 4) / 60.0

        cur_co2, cur_o2 = calculate_advanced_bio(
            men_count, men_avg_weight, women_count, women_avg_weight, room_vol, simulated_minutes
        )

        cur_db = random.randint(75, 85) if (8 <= step % 20 <= 12) else random.randint(38, 44)
        cur_lux = random.randint(430, 480) if (14 <= step % 25 <= 17) else random.randint(580, 680)
        cur_temp = round(23.8 + (step * 0.02) + random.uniform(-0.1, 0.1), 1)

        # 3 Saniyəlik Hədd İzləmə (Debounce)
        tt = st.session_state.trigger_timers

        if cur_co2 > 1000:
            tt["co2"] += 1
            st.session_state.session_penalty += 1.0
        else:
            tt["co2"] = 0

        if cur_db > 70:
            tt["sound"] += 1
            st.session_state.session_penalty += 1.0
        else:
            tt["sound"] = 0

        if cur_temp >= 26.0:
            tt["temp"] += 1
            st.session_state.session_penalty += 0.8
        else:
            tt["temp"] = 0

        if cur_lux < 500:
            tt["light"] += 1
            st.session_state.session_penalty += 0.5
        else:
            tt["light"] = 0

        st.session_state.data_history.append({
            "Saniyə": step, 
            "CO2 (ppm)": cur_co2, 
            "Səs (dB)": cur_db, 
            "İşıq (Lux)": cur_lux,
            "Temperatur (°C)": cur_temp
        })
        df_live = pd.DataFrame(st.session_state.data_history)

        k1.metric("CO₂ Səviyyəsi", f"{cur_co2} ppm", delta=f"{round(cur_co2 - 420.0, 1)}")
        k2.metric("O₂ Balansı", f"{cur_o2} %")
        k3.metric("Səs Küyü", f"{cur_db} dB")
        k4.metric("İşıq", f"{cur_lux} Lux")
        k5.metric("Temperatur", f"{cur_temp} °C", delta=f"{round(cur_temp - 24.0, 1)} °C")

        # Dinamik Ekran və Məsləhət İdarəetməsi
        mentor_msg = "🌿 Bütün parametrlər idealdır (CO₂ < 600 ppm, İşıq: 500-1000 lx, Temperatur: ~24°C). Dərin fokus fazasındasınız."

        active_factor = None
        active_val = None
        active_dur = 0

        if tt["sound"] > 0:
            active_factor = "sound"
            active_val = cur_db
            active_dur = tt["sound"]
        elif tt["co2"] > 0:
            active_factor = "co2"
            active_val = cur_co2
            active_dur = tt["co2"]
        elif tt["temp"] > 0:
            active_factor = "temp"
            active_val = cur_temp
            active_dur = tt["temp"]
        elif tt["light"] > 0:
            active_factor = "light"
            active_val = cur_lux
            active_dur = tt["light"]

        if active_factor:
            if active_dur < 3:
                local_alerts = {
                    "sound": f"🔊 Səs səviyyəsi yüksəldi ({cur_db} dB) — İzlənilir ({active_dur} san)...",
                    "co2": f"⚠️ Hava köhnəlir: CO₂ yüksəldi ({cur_co2} ppm) — İzlənilir ({active_dur} san)...",
                    "temp": f"🌡️ Temperatur yüksəldi ({cur_temp} °C) — İzlənilir ({active_dur} san)...",
                    "light": f"💡 Masada işıqlanma zəiflədi ({cur_lux} Lux) — İzlənilir ({active_dur} san)..."
                }
                mentor_msg = local_alerts.get(active_factor)
                if st.session_state.last_active_factor != active_factor:
                    st.session_state.cached_ai_response = None
                    st.session_state.last_active_factor = active_factor
            else:
                if not st.session_state.cached_ai_response or st.session_state.last_active_factor != active_factor:
                    advice_text = get_smart_advice(active_factor, active_val, is_offline_manual)
                    st.session_state.cached_ai_response = advice_text
                    st.session_state.last_active_factor = active_factor
                
                label_prefix = "📋 Lokal Qayda" if is_offline_manual else "🤖 AI Məsləhəti"
                mentor_msg = f"{label_prefix} (Hədd {active_dur} san aşıldı): {st.session_state.cached_ai_response}"
        else:
            st.session_state.cached_ai_response = None
            st.session_state.last_active_factor = None

        # Taymer
        elapsed_sec = int(time.time() - (st.session_state.start_time or time.time()))
        mins, secs = divmod(elapsed_sec, 60)
        timer_text = f"{mins:02d}:{secs:02d}"

        # Status Nişanı (Manual rejimə görə)
        status_badge_html = (
            '<span class="status-badge-offline">🟡 Oflayn Rejim (Lokal Məntiq)</span>'
            if is_offline_manual or not client
            else '<span class="status-badge-online">🟢 Gemini AI Aktiv</span>'
        )

        st.markdown(
            f"""
            <div class="mentor-container">
                <div class="mentor-header-row">
                    <div class="mentor-header-left">
                        <h3 class="mentor-title-left">🤖 Mentor</h3>
                        <span class="compact-timer-tag">⏱️ Taymer: {timer_text}</span>
                    </div>
                    {status_badge_html}
                </div>
                <p class="mentor-msg-text">{mentor_msg}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.line_chart(
            df_live.set_index("Saniyə")[["CO2 (ppm)", "Səs (dB)"]],
            color=["#38BDF8", "#F43F5E"]
        )

    else:
        k1.metric("CO₂ Səviyyəsi", "420.0 ppm")
        k2.metric("O₂ Balansı", "20.95 %")
        k3.metric("Səs Küyü", "40 dB")
        k4.metric("İşıq", "500 Lux")
        k5.metric("Temperatur", "24.0 °C")

        status_badge_html = (
            '<span class="status-badge-offline">🟡 Oflayn Rejim (Lokal Məntiq)</span>'
            if is_offline_manual or not client
            else '<span class="status-badge-online">🟢 Gemini AI Aktiv</span>'
        )

        st.markdown(
            f"""
            <div class="mentor-container">
                <div class="mentor-header-row">
                    <div class="mentor-header-left">
                        <h3 class="mentor-title-left">🤖 Mentor</h3>
                        <span class="compact-timer-tag">⏱️ Taymer: 00:00</span>
                    </div>
                    {status_badge_html}
                </div>
                <p class="mentor-msg-text">Sistem gözləmədədir. Sessiya başladılan kimi canlı analitika və mentor tövsiyələri aktivləşəcək.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

render_live_dashboard()

# --- Yekun Hesabat Pəncərəsi ---
if st.session_state.last_report and not st.session_state.session_running:
    rep = st.session_state.last_report
    st.markdown("---")
    st.markdown("### 🏆 Sessiyanın Keyfiyyət Hesabatı")
    r1, r2 = st.columns([3, 7])
    with r1:
        st.metric("Fokus Skoru", f"{rep['score']} / 100")
        st.caption(f"Fokus müddəti: {rep['time']}")
    with r2:
        st.info(f"**Mentor Yekun Təhlili:**\n\n{rep['feedback']}")

# --- Fokus Tarixçəsi Cədvəli ---
st.markdown("---")
h_col1, h_col2 = st.columns([8, 2])
with h_col1:
    st.markdown('<div class="section-title">📚 Fokus Sessiyaları Tarixçəsi</div>', unsafe_allow_html=True)
with h_col2:
    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("🗑️ Tarixçəni Təmizlə", use_container_width=True):
        st.session_state.focus_history = []
        st.session_state.last_report = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.focus_history:
    st.dataframe(pd.DataFrame(st.session_state.focus_history), use_container_width=True)
else:
    st.markdown(
        """
        <div class="empty-history-box">
            Hələ qeydə alınmış fokus sessiyası yoxdur. Sessiyanı başlatdıqdan sonra bitirdikdə bura qeyd olunacaq.
        </div>
        """,
        unsafe_allow_html=True
    )