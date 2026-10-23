import os
import time
import random
import requests
import json
import math
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from google import genai
from google.genai import types

# Serial port kitabxanası (ESP32 fiziki qoşulduqda istifadə üçün)
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# 1. Konfiqurasiya yalnız bir dəfə və ən yuxarıda çağırılmalıdır
st.set_page_config(
    page_title="LearnSphere AI Hub",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Müasir Slate Dark & Indigo Palitrası ---
st.markdown(
    """
    <style>
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
    section[data-testid="stSidebar"] {
        background-color: #1E1B4B !important;
        border-right: 1px solid #312E81 !important;
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
    .start-btn button {
        background-color: #10B981 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
    }
    .stop-btn button {
        background-color: #EF4444 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3) !important;
    }
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
    div[data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #94A3B8 !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
    }
    .mentor-container {
        background-color: #1E1B4B;
        border: 1px solid #312E81;
        border-left: 4px solid #6366F1;
        border-radius: 12px;
        padding: 18px 24px;
        margin-top: 20px;
        margin-bottom: 20px;
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
    }
    .empty-history-box {
        background-color: #1E293B;
        border: 1px dashed #475569;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: #94A3B8;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="hero-title">LearnSphere</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">STEAM Layihəsi | Elmi IEQ Modeli, Persily-de Jonge Dinamikası & Koqnitiv Erqonomika</div>', unsafe_allow_html=True)

# API Müştərisi
api_key = None
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass
if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY", None)

client = genai.Client(api_key=api_key) if api_key else None

# --- Sessiya Yaddaşı (State Management) ---
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
if "ieq_scores_history" not in st.session_state:
    st.session_state.ieq_scores_history = []
if "raw_buffer" not in st.session_state:
    st.session_state.raw_buffer = {"co2": [], "temp": [], "lux": [], "db": []}
if "trigger_timers" not in st.session_state:
    st.session_state.trigger_timers = {"co2": 0, "sound": 0, "temp": 0, "light": 0}
if "cached_ai_response" not in st.session_state:
    st.session_state.cached_ai_response = {}
if "last_ai_call_time" not in st.session_state:
    st.session_state.last_ai_call_time = 0.0
if "serial_conn" not in st.session_state:
    st.session_state.serial_conn = None

BACKUP_CSV_PATH = "learnsphere_live_backup.csv"

# --- Sol Panel Parametrləri ---
st.sidebar.markdown("### ⚙️ Sistem və Cihaz Rejimi")

data_source = st.sidebar.radio(
    "Məlumat Mənbəyi:",
    ["🧪 Simulyasiya (Riyazi Model)", "📡 Fiziki Cihaz (ESP32 USB Serial)"],
    index=0
)
is_hardware_mode = (data_source == "📡 Fiziki Cihaz (ESP32 USB Serial)")

selected_port = None
baud_rate = 115200
if is_hardware_mode:
    if SERIAL_AVAILABLE:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        selected_port = st.sidebar.selectbox("COM Port:", ports if ports else ["Port tapılmadı (Simulyasiya fallback)"])
        baud_rate = st.sidebar.selectbox("Baud Rate:", [115200, 9600], index=0)
    else:
        st.sidebar.warning("`pyserial` quraşdırılmayıb (`pip install pyserial`). Avtomatik simulyasiya işləyir.")

co2_baseline_offset = st.sidebar.slider("CO₂ Kalibrasiya Ofseti (ppm):", -200, 200, 0, step=5)

system_mode = st.sidebar.radio(
    "Mentor Rejimi:",
    ["🟢 Onlayn (Gemini AI)", "🟡 Oflayn (Lokal Qaydalar)"],
    index=0
)
is_offline_manual = (system_mode == "🟡 Oflayn (Lokal Qaydalar)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 👥 Məkan və Kinetika Parametrləri")
mode = st.sidebar.radio("Otaq Formatı:", ["👤 Fərdi Kabinə (1 nəfər)", "👥 Qrup Otağı (Çox nəfərlik)"])

MEN_DEFAULT_WEIGHT = 84.9
WOMEN_DEFAULT_WEIGHT = 71.9

if mode == "👤 Fərdi Kabinə (1 nəfər)":
    gender = st.sidebar.selectbox("Cins:", ["Kişi", "Qadın"])
    weight = st.sidebar.number_input(
        "Çəki (kq)", 40, 130, 
        int(MEN_DEFAULT_WEIGHT if gender == "Kişi" else WOMEN_DEFAULT_WEIGHT)
    )
    men_count = 1 if gender == "Kişi" else 0
    women_count = 1 if gender == "Qadın" else 0
    men_avg_weight = float(weight if men_count else 0)
    women_avg_weight = float(weight if women_count else 0)
    total_people = 1
    default_vol = 10
else:
    col_m, col_w = st.sidebar.columns(2)
    with col_m:
        men_count = st.number_input("Kişi sayı", 0, 30, 2)
        men_avg_weight = float(st.number_input("Kişi orta çəki (kq)", 40, 120, int(MEN_DEFAULT_WEIGHT)))
    with col_w:
        women_count = st.number_input("Qadın sayı", 0, 30, 2)
        women_avg_weight = float(st.number_input("Qadın orta çəki (kq)", 40, 120, int(WOMEN_DEFAULT_WEIGHT)))
    
    total_people = max(men_count + women_count, 1)
    default_vol = 30

room_vol = st.sidebar.number_input("Otaq Həcmi (m³)", 3, 300, default_vol)

st.sidebar.markdown("---")

# ==============================================================
# Google Sheets Webhook İnteqrasiyası
# ==============================================================
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyRW0AZquTlgSM51-LR96vausUQ5_lIirM-5For6OprXfUH-CkZEbaWMwk35TTEcdLWLA/exec"

def export_to_google_sheets(rejim, total_people, men_count, women_count, duration_str, focus_score, final_co2, avg_temp):
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rejim": str(rejim),
        "total_people": int(total_people),
        "men_count": int(men_count),
        "women_count": int(women_count),
        "duration": str(duration_str),
        "focus_score": round(float(focus_score), 2),
        "final_co2": round(float(final_co2), 1),
        "avg_temp": round(float(avg_temp), 1)
    }
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=8,
            allow_redirects=True
        )
        return response.status_code in [200, 302]
    except Exception as e:
        print(f"Sheets xətası: {e}")
        return False

# ==============================================================
# Hərəkətli Ortalama Filtri (Moving Average - Sensor Küyü Üçün)
# ==============================================================
def apply_moving_average(key, new_val, window=5):
    buf = st.session_state.raw_buffer[key]
    buf.append(float(new_val))
    if len(buf) > window:
        buf.pop(0)
    return round(sum(buf) / len(buf), 1)

# ==============================================================
# Fiziki ESP32 Serial Oxuyucu (JSON Format: {"co2":600,"temp":23.5,"lux":550,"db":38})
# ==============================================================
def read_esp32_sensor_data(port, baud):
    if not SERIAL_AVAILABLE or not port or "tapılmadı" in port:
        return None
    try:
        if st.session_state.serial_conn is None or not st.session_state.serial_conn.is_open:
            st.session_state.serial_conn = serial.Serial(port, baud, timeout=0.5)
        conn = st.session_state.serial_conn
        if conn.in_waiting > 0:
            line = conn.readline().decode("utf-8", errors="ignore").strip()
            if line.startswith("{") and line.endswith("}"):
                data = json.loads(line)
                return {
                    "co2": float(data.get("co2", 450.0)),
                    "temp": float(data.get("temp", 23.0)),
                    "lux": float(data.get("lux", 600.0)),
                    "db": float(data.get("db", 38.0))
                }
    except Exception:
        st.session_state.serial_conn = None
    return None

# ==============================================================
# Elmi Əsaslı Bioloji Kütlə Balansı (Persily & de Jonge 2017)
# ==============================================================
def calculate_advanced_bio(men_count, men_weight, women_count, women_weight, room_volume_m3, total_ppl, prev_co2):
    g_m = men_count * (0.0056 * (men_weight / MEN_DEFAULT_WEIGHT)) if men_count > 0 else 0.0
    g_w = women_count * (0.0044 * (women_weight / WOMEN_DEFAULT_WEIGHT)) if women_count > 0 else 0.0
    total_g_L_s = g_m + g_w
    total_g_m3_s = total_g_L_s / 1000.0

    total_q_m3_s = max(total_ppl * 0.004, 0.002)
    c_out_ppm = 415.0

    dt = 1.0
    c_prev = prev_co2 if prev_co2 is not None else 450.0
    
    alpha = total_q_m3_s / room_volume_m3
    c_inf = c_out_ppm + (total_g_m3_s / total_q_m3_s) * 1e6
    
    theoretical_co2 = c_inf + (c_prev - c_inf) * math.exp(-alpha * dt)
    theoretical_co2 = max(415.0, min(theoretical_co2, 3500.0))

    co2_delta = theoretical_co2 - 415.0
    o2_consumed = (co2_delta / 0.85) / 10000.0
    current_o2 = round(max(20.95 - o2_consumed, 19.5), 2)

    return round(theoretical_co2, 1), current_o2

# ==============================================================
# Xətti Cəbr: Sensor Müstəqilliyinin Kovariasiya Determinantı
# ==============================================================
def calculate_covariance_det(df_recent):
    if len(df_recent) < 6:
        return None
    try:
        cols = ["CO2 (ppm)", "Temperatur (°C)", "İşıq (Lux)", "Səs (dBA)"]
        sub = df_recent[cols].tail(30)
        cov_matrix = np.cov(sub.values, rowvar=False)
        det_val = float(np.linalg.det(cov_matrix))
        return det_val
    except Exception:
        return None

# ==============================================================
# Elmi IEQ Fokus Skorlama Modeli
# ==============================================================
def calculate_ieq_score(co2, temp, lux, db):
    if co2 <= 600:
        s_iaq = 100.0
    elif co2 <= 1000:
        s_iaq = 100.0 - ((co2 - 600) / 400.0) * 25.0
    elif co2 <= 1600:
        s_iaq = 75.0 - ((co2 - 1000) / 600.0) * 40.0
    else:
        s_iaq = max(35.0 - ((co2 - 1600) / 800.0) * 35.0, 0.0)

    if 20.8 <= temp <= 24.8:
        s_therm = 100.0
    elif temp < 20.8:
        s_therm = max(100.0 - (20.8 - temp) * 12.0, 20.0)
    elif 24.8 < temp <= 28.0:
        s_therm = 100.0 - ((temp - 24.8) / 3.2) * 35.0
    else:
        s_therm = max(65.0 - (temp - 28.0) * 15.0, 10.0)

    if 500 <= lux <= 1000:
        s_vis = 100.0
    elif lux < 500:
        s_vis = max((lux / 500.0) * 100.0, 20.0)
    else:
        s_vis = max(100.0 - ((lux - 1000) / 1000.0) * 40.0, 40.0)

    if db <= 40:
        s_acou = 100.0
    elif db <= 50:
        s_acou = 100.0 - ((db - 40) / 10.0) * 30.0
    elif db <= 60:
        s_acou = 70.0 - ((db - 50) / 10.0) * 35.0
    else:
        s_acou = max(35.0 - ((db - 60) / 20.0) * 35.0, 0.0)

    final_ieq = (0.35 * s_iaq) + (0.30 * s_therm) + (0.20 * s_vis) + (0.15 * s_acou)
    return round(final_ieq, 1)

# --- Oflayn Qayda Əsaslı Elmi Məsləhət Bankı ---
OFFLINE_EXPERT_RULES = {
    "co2": "ASHRAE 62.1 norması aşıldı (>1000 ppm). Karbon qazı beyin qan axını və oksigenlənməni azaldır. Dərhal pəncərəni açaraq təmiz hava sirkulyasiyası yaradın.",
    "sound": "Tədris və fokus üçün kritik fon küyü aşıldı (>40 dBA). Səs küyü işçi yaddaşı və mütaliə dəqiqliyini zəiflədir. Akustik izolyasiya təmin edin.",
    "temp": "Temperatur kritik həddə çatdı (≥28.0°C). Elmi tədqiqatlara görə bu dərəcədə zehni tapşırıqlarda xəta faizi 5.2% yüksəlir. Otağı sərinlədin (ideal: 20.8–24.8°C).",
    "light": "Vizual işıqlanma tədris standartından aşağıdır (<500 Lux). Göz yorğunluğunun qarşısını almaq üçün masaüstü işığı artırın."
}

def get_smart_advice(factor, value, force_offline):
    if force_offline or not client:
        return OFFLINE_EXPERT_RULES.get(factor, "Mühit normativləri pozuldu. Parametrləri tənzimləyin.")

    # Cooldown yoxlaması: eyni faktor üzrə keşdə cavab varsa və ya son sorğudan 45 saniyə keçməyibsə API-ni yorma
    now_ts = time.time()
    if factor in st.session_state.cached_ai_response and (now_ts - st.session_state.last_ai_call_time) < 45.0:
        return st.session_state.cached_ai_response[factor]

    prompts = {
        "co2": f"Sinif/otaqda CO2 göstəricisi {value} ppm oldu (ASHRAE 62.1 həddi 1000 ppm). Elmi əsaslı 1 cümləlik akademik tövsiyə ver.",
        "sound": f"Fokus tələb edən dərs otağında səs {value} dBA oldu (Elmi fokus həddi maksimum 40 dBA). 1 cümləlik qısa tövsiyə yaz.",
        "temp": f"Otaq temperaturu {value} °C oldu (Təsdiqlənmiş optimal hədd 20.8-24.8°C, kritik xəta həddi 28°C). 1 cümləlik tövsiyə ver.",
        "light": f"İş masasında işıqlanma {value} Lux oldu (Optimal tədris norması: 500-1000 Lux). 1 cümləlik tövsiyə ver."
    }

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompts.get(factor, "Mühit normadan kənara çıxdı. Qısa tövsiyə ver."),
            config=types.GenerateContentConfig(temperature=0.7)
        )
        ans = res.text.strip() if res.text else OFFLINE_EXPERT_RULES.get(factor)
        st.session_state.cached_ai_response[factor] = ans
        st.session_state.last_ai_call_time = now_ts
        return ans
    except Exception:
        return OFFLINE_EXPERT_RULES.get(factor, "Mühit normativləri pozuldu. Otaq şəraitini tənzimləyin.")

def get_session_summary(duration_str, score, avg_co2, max_db, avg_lux, avg_temp, force_offline):
    offline_summary = (
        f"Sessiya {score}/100 IEQ Fokus balı ilə başa çatdı ({duration_str}). "
        f"Orta göstəricilər: {avg_co2} ppm CO₂, {avg_temp} °C temperatur, {avg_lux} Lux işıq və maks {max_db} dBA küy. "
        f"ASHRAE 62.1 və IEQ təhsil normativlərinə əsasən fasilələrlə otaq havasını təmizləmək tövsiyə olunur."
    )

    if force_offline or not client:
        return offline_summary

    prompt = f"""
    Sən elmi IEQ və dərs mentorusan. Sessiya yenicə bitdi.
    Göstəricilər: Müddət: {duration_str}, IEQ Fokus İndeksi: {score}/100, Orta CO2: {avg_co2} ppm, Maks Küy: {max_db} dBA, İşıq: {avg_lux} lx, Temp: {avg_temp} °C.
    Tələbəyə elmi daxili mühit standartlarına (optimal 20.8-24.8°C, fon küyü <=40 dBA, CO2 <=1000 ppm) söykənən 2 cümləlik peşəkar təhlil və rəy yaz.
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
        st.session_state.data_history = []
        st.session_state.ieq_scores_history = []
        st.session_state.raw_buffer = {"co2": [], "temp": [], "lux": [], "db": []}
        st.session_state.trigger_timers = {"co2": 0, "sound": 0, "temp": 0, "light": 0}
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
            max_db = int(df_final["Səs (dBA)"].max())
            avg_lux = int(df_final["İşıq (Lux)"].mean())
            avg_temp = round(df_final["Temperatur (°C)"].mean(), 1)
            last_co2 = df_final["CO2 (ppm)"].iloc[-1]
            final_score = int(round(df_final["IEQ İndeksi"].mean()))
            # Yekun CSV yedəkləməsi
            df_final.to_csv(BACKUP_CSV_PATH, index=False)
        else:
            avg_co2, max_db, avg_lux, avg_temp, last_co2, final_score = 420, 38, 600, 23.5, 420.0, 100

        sheet_ok = export_to_google_sheets(
            rejim=mode,
            total_people=total_people,
            men_count=men_count,
            women_count=women_count,
            duration_str=total_time_str,
            focus_score=final_score,
            final_co2=last_co2,
            avg_temp=avg_temp
        )

        ai_final_feedback = get_session_summary(
            total_time_str, final_score, avg_co2, max_db, avg_lux, avg_temp, is_offline_manual
        )

        st.session_state.focus_history.append({
            "Tarix": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Rejim": mode,
            "İştirakçı": total_people,
            "Müddət": total_time_str,
            "IEQ İndeksi": f"{final_score}/100 ⭐",
            "Son CO₂": f"{last_co2} ppm",
            "Ort. Temp": f"{avg_temp} °C"
        })

        st.session_state.last_report = {
            "score": final_score,
            "time": total_time_str,
            "feedback": ai_final_feedback,
            "sheet_status": sheet_ok
        }

        st.session_state.start_time = None
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

# --- CANLI PANEL ---
@st.fragment(run_every=1.0 if st.session_state.session_running else None)
def render_live_dashboard():
    st.markdown(
        f'<div class="section-title">📊 Canlı Göstəricilər ({total_people} Nəfər | Tələbə İstilik Yükü: {total_people * 100} W)</div>', 
        unsafe_allow_html=True
    )
    k1, k2, k3, k4, k5 = st.columns(5)

    if st.session_state.session_running:
        step = len(st.session_state.data_history) + 1
        prev_teo_co2 = st.session_state.data_history[-1]["Nəzəri CO2 (ppm)"] if st.session_state.data_history else 450.0

        # 1. Həmişə Persily & de Jonge nəzəri modelini hesabla (Müqayisə bazası üçün)
        teo_co2, cur_o2 = calculate_advanced_bio(
            men_count, men_avg_weight, women_count, women_avg_weight, room_vol, total_people, prev_teo_co2
        )

        # 2. Fiziki cihazdan oxu və ya Simulyasiya yarat
        hw_packet = read_esp32_sensor_data(selected_port, baud_rate) if is_hardware_mode else None

        if hw_packet:
            raw_co2 = hw_packet["co2"] + co2_baseline_offset
            raw_temp = hw_packet["temp"]
            raw_lux = hw_packet["lux"]
            raw_db = hw_packet["db"]
        else:
            raw_co2 = teo_co2 + random.uniform(-2.0, 2.0) + co2_baseline_offset
            raw_db = random.randint(46, 56) if (10 <= step % 22 <= 14) else random.randint(34, 39)
            raw_lux = random.randint(430, 480) if (16 <= step % 28 <= 19) else random.randint(580, 680)
            heat_increment = (total_people * 0.015) * (step / 30.0)
            raw_temp = 22.5 + heat_increment + random.uniform(-0.1, 0.1)

        # 3. Hərəkətli Ortalama Filtri (Moving Average) ilə küyü təmizlə
        cur_co2 = max(400.0, apply_moving_average("co2", raw_co2, window=5))
        cur_temp = apply_moving_average("temp", raw_temp, window=5)
        cur_lux = int(apply_moving_average("lux", raw_lux, window=3))
        cur_db = int(apply_moving_average("db", raw_db, window=3))

        # Oksigen balansını faktiki CO2 əsasında yenilə
        cur_o2 = round(max(20.95 - ((cur_co2 - 415.0) / 0.85) / 10000.0, 19.5), 2)

        # Cari saniyəlik IEQ Balı
        current_ieq_point = calculate_ieq_score(cur_co2, cur_temp, cur_lux, cur_db)
        st.session_state.ieq_scores_history.append(current_ieq_point)

        tt = st.session_state.trigger_timers
        tt["co2"] = tt["co2"] + 1 if cur_co2 > 1000 else 0
        tt["sound"] = tt["sound"] + 1 if cur_db > 40 else 0
        tt["temp"] = tt["temp"] + 1 if cur_temp >= 28.0 else 0
        tt["light"] = tt["light"] + 1 if cur_lux < 500 else 0

        st.session_state.data_history.append({
            "Zaman": datetime.now().strftime("%H:%M:%S"),
            "Saniyə": step, 
            "CO2 (ppm)": cur_co2,
            "Nəzəri CO2 (ppm)": teo_co2,
            "Səs (dBA)": cur_db, 
            "İşıq (Lux)": cur_lux, 
            "Temperatur (°C)": cur_temp,
            "IEQ İndeksi": current_ieq_point
        })

        # 1 Həftəlik Sınaq Qoruyucusu: Hər 60 saniyədən bir lokal CSV-yə auto-backup et
        if step % 60 == 0:
            pd.DataFrame(st.session_state.data_history).to_csv(BACKUP_CSV_PATH, index=False)

        # Brauzerin donmaması üçün yalnız son 300 saniyəni qrafikə ötür
        df_window = pd.DataFrame(st.session_state.data_history[-300:])

        k1.metric("CO₂ Səviyyəsi", f"{cur_co2} ppm", delta=f"Nəzəri: {teo_co2} ppm")
        k2.metric("O₂ Balansı", f"{cur_o2} %")
        k3.metric("Fon Küyü", f"{cur_db} dBA", delta="Normal" if cur_db <= 40 else "Kritik >40", delta_color="inverse")
        k4.metric("İşıq", f"{cur_lux} Lux")
        k5.metric("Temperatur", f"{cur_temp} °C", delta=f"{round(cur_temp - 24.8, 1)} °C")

        mentor_msg = f"🌿 IEQ Fokus İndeksi: {current_ieq_point}/100. Bütün parametrlər elmi komfort zonasındadır (Temp: 20.8-24.8°C, Fon küyü ≤40 dBA, CO₂ ≤1000 ppm)."

        active_factor, active_val, active_dur = None, None, 0
        if tt["sound"] > 0:
            active_factor, active_val, active_dur = "sound", cur_db, tt["sound"]
        elif tt["co2"] > 0:
            active_factor, active_val, active_dur = "co2", cur_co2, tt["co2"]
        elif tt["temp"] > 0:
            active_factor, active_val, active_dur = "temp", cur_temp, tt["temp"]
        elif tt["light"] > 0:
            active_factor, active_val, active_dur = "light", cur_lux, tt["light"]

        if active_factor:
            if active_dur < 3:
                local_alerts = {
                    "sound": f"🔊 Səs səviyyəsi həddi aşdı ({cur_db} dBA > 40 dBA) — İzlənilir ({active_dur} san)...",
                    "co2": f"⚠️ Hava köhnəlir: CO₂ yüksəldi ({cur_co2} ppm > 1000 ppm) — İzlənilir ({active_dur} san)...",
                    "temp": f"🌡️ Kritik temperatur həddi aşıldı ({cur_temp} °C ≥ 28.0°C) — İzlənilir ({active_dur} san)...",
                    "light": f"💡 İşıqlanma normativdən düşdü ({cur_lux} Lux < 500) — İzlənilir ({active_dur} san)..."
                }
                mentor_msg = local_alerts.get(active_factor)
            else:
                advice_text = get_smart_advice(active_factor, active_val, is_offline_manual)
                label_prefix = "📋 Lokal Elmi Qayda" if is_offline_manual else "🤖 AI Məsləhəti"
                mentor_msg = f"{label_prefix} (Norma {active_dur} san pozuldu): {advice_text}"

        elapsed_sec = int(time.time() - (st.session_state.start_time or time.time()))
        mins, secs = divmod(elapsed_sec, 60)
        timer_text = f"{mins:02d}:{secs:02d}"

        det_val = calculate_covariance_det(df_window)
        det_badge = f" | det(Σ) ≠ 0 Təsdiqləndi ({det_val:.2e})" if det_val and abs(det_val) > 0 else ""

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
                        <h3 class="mentor-title-left">🤖 Mentor (IEQ İndeksi: {current_ieq_point}/100{det_badge})</h3>
                        <span class="compact-timer-tag">⏱️ Taymer: {timer_text}</span>
                    </div>
                    {status_badge_html}
                </div>
                <p class="mentor-msg-text">{mentor_msg}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # İki Ayrı Miqyaslı Qrafik (Miqyas əzilməsinin qarşısını alır)
        ch1, ch2 = st.columns(2)
        with ch1:
            st.caption("📈 Karbon Qazı Dinamikası: Sensor vs. Persily-de Jonge İnteqralı (ppm)")
            st.line_chart(
                df_window.set_index("Saniyə")[["CO2 (ppm)", "Nəzəri CO2 (ppm)"]],
                color=["#38BDF8", "#A855F7"]
            )
        with ch2:
            st.caption("🎯 Koqnitiv Erqonomika: IEQ Fokus İndeksi (0-100) və Akustik Fon (dBA)")
            st.line_chart(
                df_window.set_index("Saniyə")[["IEQ İndeksi", "Səs (dBA)", "Temperatur (°C)"]],
                color=["#10B981", "#F43F5E", "#F59E0B"]
            )

    else:
        k1.metric("CO₂ Səviyyəsi", "415.0 ppm")
        k2.metric("O₂ Balansı", "20.95 %")
        k3.metric("Fon Küyü", "35 dBA")
        k4.metric("İşıq", "600 Lux")
        k5.metric("Temperatur", "22.5 °C")

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
                <p class="mentor-msg-text">Sistem gözləmədədir. Sessiya başladılan kimi elmi IEQ inteqrasiyalı canlı monitorinq aktivləşəcək.</p>
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
    
    if rep.get("sheet_status"):
        st.success("📊 Məlumatlar uğurla Google Sheets bulud bazasına və lokal CSV faylına yazıldı!")
    else:
        st.warning("⚠️ Bulud bağlantısı yoxdur, lakin məlumatlar lokal `learnsphere_live_backup.csv` faylında tam qorundu.")

    r1, r2 = st.columns([3, 7])
    with r1:
        st.metric("IEQ Fokus Skoru", f"{rep['score']} / 100")
        st.caption(f"Fokus müddəti: {rep['time']}")
        if os.path.exists(BACKUP_CSV_PATH):
            with open(BACKUP_CSV_PATH, "rb") as f:
                st.download_button("📥 Tam Telemetriya CSV Yüklə", f, file_name="learnsphere_session_data.csv", mime="text/csv")
    with r2:
        st.info(f"**Mentor Yekun Elmi Təhlili:**\n\n{rep['feedback']}")

# --- Fokus Tarixçəsi Cədvəli ---
st.markdown("---")
h_col1, h_col2 = st.columns([8, 2])
with h_col1:
    st.markdown('<div class="section-title">📚 Fokus Sessiyaları Tarixçəsi</div>', unsafe_allow_html=True)
with h_col2:
    st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
    if st.button("🗑️ Tarixçəni Təmizlə", use_container_width=True):
        st.session_state.focus_history = []
        st.session_state.ieq_scores_history = []
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