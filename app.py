import os
import time
import random
import requests
import json
import math
from types import MappingProxyType
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from google import genai
from google.genai import types

# Serial port library (for physical ESP32 connection)
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# --- Session State Initialization (Before Page Config so sidebar state matches active page) ---
defaults = {
    "active_page": "Home",
    "focus_history": [],
    "session_running": False,
    "start_time": None,
    "last_report": None,
    "data_history": [],
    "ieq_scores_history": [],
    "raw_buffer": {"co2": [], "temp": [], "lux": [], "db": []},
    "trigger_timers": {"co2": 0, "sound": 0, "temp": 0, "light": 0},
    "cached_ai_response": {},
    "session_end_cache": {},
    "last_ai_call_time": 0.0,
    "serial_conn": None,
    "last_packet_ts": None,
    "hw_error_msg": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

is_dashboard_active = (st.session_state.active_page == "Dashboard")

# 1. Page Configuration
st.set_page_config(
    page_title="LearnSphere",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded" if is_dashboard_active else "collapsed"
)

# --- Clean Light UI Inspired by Modern Workspace Design, Tailored to LearnSphere Identity ---
sidebar_visibility_css = (
    """
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    """
    if is_dashboard_active
    else """
    section[data-testid="stSidebar"],
    button[data-testid="stExpandSidebarButton"],
    div[data-testid="collapsedControl"] {
        display: none !important;
    }
    """
)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {{
        --ls-primary: #2563EB;
        --ls-primary-hover: #1D4ED8;
        --ls-primary-soft: #EFF6FF;
        --ls-accent: #0EA5E9;
        --ls-emerald: #10B981;
        --ls-emerald-dark: #059669;
        --ls-emerald-soft: #ECFDF5;
        --ls-amber: #F59E0B;
        --ls-amber-soft: #FFFBEB;
        --ls-rose: #E11D48;
        --ls-rose-soft: #FFF1F2;
        --ls-bg: #FFFFFF;
        --ls-surface: #F8FAFC;
        --ls-border: #E2E8F0;
        --ls-text: #0F172A;
        --ls-muted: #64748B;
    }}

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: var(--ls-bg) !important;
        color: var(--ls-text) !important;
    }}

    h1, h2, h3, h4 {{
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        color: var(--ls-text) !important;
        letter-spacing: -0.02em;
    }}

    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes auroraShift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    @keyframes floatSoft {{
        0%, 100% {{ transform: translate(0px, 0px) scale(1); }}
        50% {{ transform: translate(16px, -18px) scale(1.05); }}
    }}

    .page-animate {{
        animation: fadeInUp 0.38s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }}

    /* Top Header */
    header[data-testid="stHeader"] {{
        background-color: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(10px);
        border-bottom: 1px solid #F1F5F9;
    }}
    header[data-testid="stHeader"] button {{
        color: var(--ls-muted) !important;
        border-radius: 50% !important;
    }}
    header[data-testid="stHeader"] svg {{
        fill: var(--ls-muted) !important;
    }}

    /* Conditional Sidebar Styling */
    {sidebar_visibility_css}

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: var(--ls-text) !important;
        font-weight: 700 !important;
        font-size: 0.94rem !important;
    }}
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {{
        color: var(--ls-muted) !important;
        font-weight: 500 !important;
        font-size: 0.87rem !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label span {{
        color: var(--ls-text) !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="base-input"] {{
        background-color: #FFFFFF !important;
        border: 1px solid var(--ls-border) !important;
        border-radius: 10px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
        border-color: var(--ls-primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
    }}
    section[data-testid="stSidebar"] input {{
        color: var(--ls-text) !important;
    }}

    /* Smooth Pill Buttons */
    div.stButton > button {{
        border-radius: 9999px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.46rem 1.2rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: none !important;
    }}
    div.stButton > button[kind="secondary"] {{
        background-color: transparent !important;
        color: var(--ls-muted) !important;
        border: 1px solid transparent !important;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        background-color: #F1F5F9 !important;
        color: var(--ls-text) !important;
        transform: translateY(-1px);
    }}
    div.stButton > button[kind="primary"] {{
        background-color: var(--ls-primary-soft) !important;
        color: var(--ls-primary) !important;
        border: 1px solid rgba(37, 99, 235, 0.22) !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background-color: #DBEAFE !important;
        color: var(--ls-primary-hover) !important;
        transform: translateY(-1px);
    }}
    div.stButton > button:active {{
        transform: scale(0.98) !important;
    }}

    /* Action Buttons */
    .start-btn button {{
        background-color: var(--ls-primary) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        padding: 0.58rem 1.2rem !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.28) !important;
    }}
    .start-btn button:hover {{
        background-color: var(--ls-primary-hover) !important;
        box-shadow: 0 6px 14px rgba(37, 99, 235, 0.32) !important;
        transform: translateY(-1px) !important;
    }}
    .stop-btn button {{
        background-color: var(--ls-rose) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        padding: 0.58rem 1.2rem !important;
        box-shadow: 0 2px 6px rgba(225, 29, 72, 0.26) !important;
    }}
    .stop-btn button:hover {{
        background-color: #BE123C !important;
        box-shadow: 0 6px 14px rgba(225, 29, 72, 0.32) !important;
        transform: translateY(-1px) !important;
    }}
    .clear-btn button {{
        background-color: #FFFFFF !important;
        color: var(--ls-muted) !important;
        border: 1px solid var(--ls-border) !important;
        border-radius: 9999px !important;
    }}
    .clear-btn button:hover {{
        background-color: var(--ls-rose-soft) !important;
        color: var(--ls-rose) !important;
        border-color: rgba(225, 29, 72, 0.28) !important;
    }}

    /* Home Page: LearnSphere Signature Kinetic Canvas */
    .home-stage {{
        position: relative;
        min-height: 72vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: radial-gradient(circle at 22% 28%, rgba(37, 99, 235, 0.08), transparent 48%),
                    radial-gradient(circle at 78% 72%, rgba(14, 165, 233, 0.09), transparent 48%),
                    radial-gradient(circle at 72% 24%, rgba(16, 185, 129, 0.06), transparent 45%),
                    #FFFFFF;
        border: 1px solid var(--ls-border);
        border-radius: 28px;
        overflow: hidden;
        padding: 48px 24px;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
    }}
    .aura-orb {{
        position: absolute;
        border-radius: 50%;
        filter: blur(56px);
        opacity: 0.45;
        pointer-events: none;
        animation: floatSoft 8s ease-in-out infinite;
    }}
    .aura-1 {{ width: 280px; height: 280px; background: #93C5FD; top: -70px; left: 10%; animation-delay: 0s; }}
    .aura-2 {{ width: 250px; height: 250px; background: #7DD3FC; bottom: -60px; right: 12%; animation-delay: 2.5s; }}
    .aura-3 {{ width: 210px; height: 210px; background: #6EE7B7; top: 35%; right: 22%; animation-delay: 4.5s; }}

    .home-brand-title {{
        position: relative;
        z-index: 2;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
        font-size: clamp(3.4rem, 8.5vw, 6.4rem);
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.05;
        margin: 0;
        background: linear-gradient(120deg, #0F172A 0%, #2563EB 45%, #0EA5E9 75%, #10B981 100%);
        background-size: 240% 240%;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        animation: auroraShift 7s ease infinite, fadeInUp 0.65s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        user-select: none;
    }}
    .brand-underline {{
        position: relative;
        z-index: 2;
        width: 84px;
        height: 4px;
        border-radius: 9999px;
        margin-top: 20px;
        background: linear-gradient(90deg, #2563EB, #0EA5E9, #10B981);
        background-size: 200% 200%;
        animation: auroraShift 5s ease infinite;
    }}

    /* Dashboard Typography & Cards */
    .page-header {{
        margin-bottom: 20px;
    }}
    .page-title {{
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--ls-text);
        margin: 0 0 4px 0;
    }}
    .page-subtitle {{
        font-size: 0.94rem;
        color: var(--ls-muted);
        margin: 0;
    }}
    .section-title {{
        color: var(--ls-text) !important;
        font-size: 1.12rem;
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 14px;
    }}

    /* Clean Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: #FFFFFF !important;
        border: 1px solid var(--ls-border) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.07) !important;
        border-color: #CBD5E1 !important;
    }}
    div[data-testid="stMetricLabel"] p {{
        color: var(--ls-muted) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }}
    div[data-testid="stMetricValue"] {{
        color: var(--ls-text) !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }}

    /* Mentor Panel */
    .mentor-container {{
        background-color: #FFFFFF;
        border: 1px solid var(--ls-border);
        border-left: 4px solid var(--ls-primary);
        border-radius: 16px;
        padding: 20px 24px;
        margin-top: 18px;
        margin-bottom: 22px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }}
    .mentor-header-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 12px;
    }}
    .mentor-header-left {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    }}
    .mentor-title-left {{
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--ls-text) !important;
        margin: 0;
    }}
    .compact-timer-tag {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--ls-primary) !important;
        background-color: var(--ls-primary-soft);
        padding: 4px 12px;
        border-radius: 9999px;
    }}
    .status-badge-online {{
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--ls-emerald-dark);
        background-color: var(--ls-emerald-soft);
        padding: 4px 12px;
        border-radius: 9999px;
    }}
    .status-badge-offline {{
        font-size: 0.8rem;
        font-weight: 600;
        color: #B45309;
        background-color: var(--ls-amber-soft);
        padding: 4px 12px;
        border-radius: 9999px;
    }}
    .mentor-msg-text {{
        font-size: 0.96rem;
        color: var(--ls-text) !important;
        line-height: 1.6;
        margin: 0;
    }}

    /* About Page Cards */
    .ls-card {{
        background: #FFFFFF;
        border: 1px solid var(--ls-border);
        border-radius: 18px;
        padding: 22px 24px;
        height: 100%;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.22s ease, box-shadow 0.22s ease;
    }}
    .ls-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
    }}
    .ls-card-tag {{
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 4px 10px;
        border-radius: 9999px;
        margin-bottom: 10px;
    }}
    .tag-blue {{ background: var(--ls-primary-soft); color: var(--ls-primary); }}
    .tag-rose {{ background: var(--ls-rose-soft); color: var(--ls-rose); }}
    .tag-emerald {{ background: var(--ls-emerald-soft); color: var(--ls-emerald-dark); }}
    .tag-amber {{ background: var(--ls-amber-soft); color: #B45309; }}

    .ls-card h4 {{
        font-size: 1.06rem;
        font-weight: 700;
        margin: 0 0 8px 0;
        color: var(--ls-text);
    }}
    .ls-card p {{
        font-size: 0.92rem;
        color: var(--ls-muted);
        line-height: 1.6;
        margin: 0;
    }}

    .stat-tile {{
        background: var(--ls-surface);
        border: 1px solid var(--ls-border);
        border-radius: 16px;
        padding: 18px;
        text-align: center;
        height: 100%;
    }}
    .stat-value {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 6px;
    }}
    .stat-desc {{
        font-size: 0.85rem;
        color: var(--ls-muted);
        line-height: 1.45;
    }}

    .empty-history-box {{
        background-color: var(--ls-surface);
        border: 1px dashed #CBD5E1;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        color: var(--ls-muted);
        font-size: 0.92rem;
    }}

    .nav-live-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--ls-emerald-dark);
        background: var(--ls-emerald-soft);
        padding: 5px 12px;
        border-radius: 9999px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# API Client
api_key = None
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass
if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY", None)

client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        if is_dashboard_active:
            st.sidebar.error(f"Gemini API initialization error: {e}")

BACKUP_CSV_PATH = "learnsphere_live_backup.csv"
SENSOR_STALE_TIMEOUT_SEC = 5.0

# Default control values (used even when sidebar is hidden on Home/About)
is_hardware_mode = False
selected_port = None
baud_rate = 115200
co2_baseline_offset = 0
is_offline_manual = False
mode = "Solo Cabin (1 person)"
total_people = 1
room_vol = 10

# ==============================================================
# Google Sheets Webhook Integration (Database Connection Preserved)
# ==============================================================
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyRW0AZquTlgSM51-LR96vausUQ5_lIirM-5For6OprXfUH-CkZEbaWMwk35TTEcdLWLA/exec"

def export_to_google_sheets(rejim, total_people, duration_str, focus_score, final_co2, avg_temp):
    payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rejim": str(rejim),
        "total_people": int(total_people),
        "men_count": 0,
        "women_count": 0,
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
        st.warning(f"Google Sheets connection error: {e}")
        return False

# ==============================================================
# Moving Average Filter (For Sensor Noise Smoothing)
# ==============================================================
def apply_moving_average(key, new_val, window=5):
    try:
        val = float(new_val)
        if math.isnan(val) or math.isinf(val):
            return None
        buf = st.session_state.raw_buffer[key]
        buf.append(val)
        if len(buf) > window:
            buf.pop(0)
        return round(sum(buf) / len(buf), 1)
    except Exception:
        return None

# ==============================================================
# Physical ESP32 Serial Reader (Anti-Stale, Zero Fallback)
# ==============================================================
def close_serial_safely():
    conn = st.session_state.get("serial_conn")
    if conn is not None:
        try:
            if conn.is_open:
                conn.close()
        except Exception:
            pass
    st.session_state.serial_conn = None

def read_esp32_sensor_data(port, baud):
    if not SERIAL_AVAILABLE:
        return None, "Device not connected: `pyserial` library is not installed."
    if not port:
        close_serial_safely()
        return None, "Device not connected: No active COM port found. Please plug in the ESP32."

    try:
        conn = st.session_state.serial_conn
        if conn is None or not conn.is_open or conn.port != port or conn.baudrate != baud:
            close_serial_safely()
            conn = serial.Serial(port, baud, timeout=0.3)
            conn.reset_input_buffer()
            st.session_state.serial_conn = conn

        latest_valid = None
        if conn.in_waiting > 0:
            raw_bytes = conn.read(conn.in_waiting)
            lines = raw_bytes.decode("utf-8", errors="ignore").splitlines()
            for line in reversed(lines):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        required_keys = ("co2", "temp", "lux", "db")
                        if all(k in data for k in required_keys):
                            latest_valid = {
                                "co2": float(data["co2"]),
                                "temp": float(data["temp"]),
                                "lux": float(data["lux"]),
                                "db": float(data["db"]),
                            }
                            break
                    except (ValueError, TypeError, json.JSONDecodeError):
                        continue

        if latest_valid is not None:
            st.session_state.last_packet_ts = time.time()
            return latest_valid, None

        last_ts = st.session_state.last_packet_ts
        if last_ts is None:
            return None, "ESP32 is connected, but no measurement packet has been received yet."
        if (time.time() - last_ts) > SENSOR_STALE_TIMEOUT_SEC:
            return None, f"Sensor data is stale (no new packet for {int(time.time() - last_ts)}s). Check device connection."

        return None, "Waiting for next fresh sensor packet..."
    except serial.SerialException as e:
        close_serial_safely()
        return None, f"Device disconnected or serial error ({port}): {e}"
    except Exception as e:
        close_serial_safely()
        return None, f"ESP32 read error: {e}"

# ==============================================================
# Scientific Mass Balance Model (Persily & de Jonge 2017 - No O2, No Gender/Weight)
# ==============================================================
def calculate_advanced_bio(room_volume_m3, total_ppl, prev_co2):
    total_g_L_s = max(int(total_ppl), 1) * 0.005
    total_g_m3_s = total_g_L_s / 1000.0

    total_q_m3_s = max(total_ppl * 0.004, 0.002)
    c_out_ppm = 415.0

    dt = 1.0
    c_prev = float(prev_co2) if prev_co2 is not None else 450.0

    alpha = total_q_m3_s / max(float(room_volume_m3), 1.0)
    c_inf = c_out_ppm + (total_g_m3_s / total_q_m3_s) * 1e6

    theoretical_co2 = c_inf + (c_prev - c_inf) * math.exp(-alpha * dt)
    theoretical_co2 = max(415.0, min(theoretical_co2, 3500.0))

    return round(theoretical_co2, 1)

# ==============================================================
# Scientific IEQ Focus Scoring Model (Isolated from AI)
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

# ==============================================================
# AI Framing & Digital Lock (Immutable Snapshot)
# ==============================================================
AI_SYSTEM_INSTRUCTION = (
    "You are the LearnSphere scientific Indoor Environmental Quality (IEQ) and Cognitive Ergonomics Mentor. "
    "STRICT RULES:\n"
    "1. All numeric values passed to you (CO2, Temperature, Light, Noise, IEQ Index) are locked by the backend. "
    "NEVER modify, recalculate, estimate, or alter these numbers.\n"
    "2. Give concise, practical, science-based study environment advice strictly aligned with "
    "ASHRAE 62.1 (CO2 <= 1000 ppm), optimal thermal comfort (20.8-24.8 C), lighting (500-1000 Lux), and acoustics (<= 40 dBA).\n"
    "3. Stay strictly on topic, never give medical diagnoses, and respond in clear, simple English."
)

OFFLINE_EXPERT_RULES = {
    "co2": "ASHRAE 62.1 limit exceeded (>1000 ppm). High CO2 reduces cognitive focus. Open a window or improve airflow immediately.",
    "sound": "Background noise exceeded the focus limit (>40 dBA). Noise disrupts working memory. Reduce ambient sound or isolate the study area.",
    "temp": "Temperature reached a critical level (>=28.0 C), which increases cognitive error rates. Cool the room toward 20.8-24.8 C.",
    "light": "Desk lighting is below the study standard (<500 Lux). Increase task lighting to prevent eye strain."
}

def create_locked_metrics_snapshot(metrics_dict):
    return MappingProxyType({k: v for k, v in metrics_dict.items()})

def get_smart_advice(factor, locked_value, force_offline):
    if force_offline or not client:
        return OFFLINE_EXPERT_RULES.get(factor, "Environmental thresholds exceeded. Adjust room conditions.")

    now_ts = time.time()
    if factor in st.session_state.cached_ai_response and (now_ts - st.session_state.last_ai_call_time) < 45.0:
        return st.session_state.cached_ai_response[factor]

    prompts = {
        "co2": f"[LOCKED METRIC] CO2 = {locked_value} ppm (Limit: <=1000 ppm). Give 1 concise sentence of practical study environment advice.",
        "sound": f"[LOCKED METRIC] Noise = {locked_value} dBA (Limit: <=40 dBA). Give 1 concise sentence of acoustic focus advice.",
        "temp": f"[LOCKED METRIC] Temperature = {locked_value} C (Optimal: 20.8-24.8 C). Give 1 concise sentence of thermal comfort advice.",
        "light": f"[LOCKED METRIC] Lighting = {locked_value} Lux (Optimal: 500-1000 Lux). Give 1 concise sentence of visual ergonomics advice."
    }

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompts.get(factor, "Environment is outside optimal range. Give brief advice."),
            config=types.GenerateContentConfig(
                system_instruction=AI_SYSTEM_INSTRUCTION,
                temperature=0.3
            )
        )
        ans = res.text.strip() if res and res.text else OFFLINE_EXPERT_RULES.get(factor)
        st.session_state.cached_ai_response[factor] = ans
        st.session_state.last_ai_call_time = now_ts
        return ans
    except Exception:
        return OFFLINE_EXPERT_RULES.get(factor, "Environmental thresholds exceeded. Adjust room conditions.")

def get_per_metric_final_evaluations(locked_snapshot, force_offline):
    cache_key = (
        locked_snapshot["avg_co2"],
        locked_snapshot["avg_temp"],
        locked_snapshot["avg_lux"],
        locked_snapshot["max_db"],
        force_offline
    )
    if st.session_state.session_end_cache.get("key") == cache_key:
        return st.session_state.session_end_cache["data"]

    metric_specs = {
        "co2": {
            "label": "CO₂ (Air Quality)",
            "value_str": f"Avg: {locked_snapshot['avg_co2']} ppm | Final: {locked_snapshot['last_co2']} ppm",
            "offline": (
                "CO₂ stayed within the safe ASHRAE 62.1 standard (<=1000 ppm)."
                if locked_snapshot["avg_co2"] <= 1000
                else "Average CO₂ exceeded 1000 ppm; ventilate the room more frequently in your next session."
            ),
            "prompt": f"[LOCKED] Session Avg CO2={locked_snapshot['avg_co2']} ppm, Final CO2={locked_snapshot['last_co2']} ppm. Write a 1-sentence final assessment."
        },
        "temp": {
            "label": "Temperature (Thermal)",
            "value_str": f"Avg: {locked_snapshot['avg_temp']} °C",
            "offline": (
                "Room temperature remained in the optimal cognitive zone (20.8-24.8 °C)."
                if 20.8 <= locked_snapshot["avg_temp"] <= 24.8
                else "Temperature drifted outside the optimal 20.8-24.8 °C range; adjust cooling or heating."
            ),
            "prompt": f"[LOCKED] Session Avg Temperature={locked_snapshot['avg_temp']} C. Write a 1-sentence final assessment."
        },
        "lux": {
            "label": "Lighting (Visual)",
            "value_str": f"Avg: {locked_snapshot['avg_lux']} Lux",
            "offline": (
                "Lighting stayed within the ideal study range (500-1000 Lux)."
                if 500 <= locked_snapshot["avg_lux"] <= 1000
                else "Lighting fell outside the optimal 500-1000 Lux range; adjust desk illumination."
            ),
            "prompt": f"[LOCKED] Session Avg Lighting={locked_snapshot['avg_lux']} Lux. Write a 1-sentence final assessment."
        },
        "db": {
            "label": "Noise (Acoustics)",
            "value_str": f"Peak: {locked_snapshot['max_db']} dBA",
            "offline": (
                "Acoustic background remained ideal for deep reading and memory (<=40 dBA)."
                if locked_snapshot["max_db"] <= 40
                else "Peak noise exceeded 40 dBA; reduce background noise to protect concentration."
            ),
            "prompt": f"[LOCKED] Session Peak Noise={locked_snapshot['max_db']} dBA. Write a 1-sentence final assessment."
        }
    }

    results = {}
    for m_key, spec in metric_specs.items():
        if force_offline or not client:
            feedback = spec["offline"]
        else:
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=spec["prompt"],
                    config=types.GenerateContentConfig(
                        system_instruction=AI_SYSTEM_INSTRUCTION,
                        temperature=0.3
                    )
                )
                feedback = res.text.strip() if res and res.text else spec["offline"]
            except Exception:
                feedback = spec["offline"]

        results[m_key] = {
            "label": spec["label"],
            "value_str": spec["value_str"],
            "feedback": feedback
        }

    st.session_state.session_end_cache = {"key": cache_key, "data": results}
    return results

def get_session_summary(locked_snapshot, duration_str, force_offline):
    offline_summary = (
        f"Session finished with an IEQ Focus Score of {locked_snapshot['score']}/100 ({duration_str}). "
        f"Averages: {locked_snapshot['avg_co2']} ppm CO₂, {locked_snapshot['avg_temp']} °C temperature, "
        f"{locked_snapshot['avg_lux']} Lux lighting, and {locked_snapshot['max_db']} dBA peak noise."
    )

    if force_offline or not client:
        return offline_summary

    prompt = (
        f"[LOCKED SESSION METRICS] Duration: {duration_str}, IEQ Focus Index: {locked_snapshot['score']}/100, "
        f"Avg CO2: {locked_snapshot['avg_co2']} ppm, Peak Noise: {locked_snapshot['max_db']} dBA, "
        f"Avg Light: {locked_snapshot['avg_lux']} Lux, Avg Temp: {locked_snapshot['avg_temp']} C. "
        f"Write a concise 2-sentence final IEQ review based strictly on these numbers."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=AI_SYSTEM_INSTRUCTION,
                temperature=0.3
            )
        )
        return response.text.strip() if response and response.text else offline_summary
    except Exception:
        return offline_summary

# ==============================================================
# Sidebar Controls — Rendered ONLY on Dashboard Page
# ==============================================================
if is_dashboard_active:
    st.sidebar.markdown("### System & Device Mode")

    data_source = st.sidebar.radio(
        "Data Source:",
        ["Simulation (Mathematical Model)", "Physical Device (ESP32 USB Serial)"],
        index=0
    )
    is_hardware_mode = (data_source == "Physical Device (ESP32 USB Serial)")

    if is_hardware_mode:
        if SERIAL_AVAILABLE:
            try:
                ports = [p.device for p in serial.tools.list_ports.comports()]
            except Exception as e:
                ports = []
                st.sidebar.error(f"Failed to scan serial ports: {e}")

            if ports:
                selected_port = st.sidebar.selectbox("COM Port:", ports)
            else:
                selected_port = None
                st.sidebar.error("ESP32 device is not connected (no COM port found).")
            baud_rate = st.sidebar.selectbox("Baud Rate:", [115200, 9600], index=0)
        else:
            st.sidebar.error("`pyserial` is not installed (`pip install pyserial`). ESP32 mode cannot run.")

    co2_baseline_offset = st.sidebar.slider("CO₂ Calibration Offset (ppm):", -200, 200, 0, step=5)

    system_mode = st.sidebar.radio(
        "Mentor Mode:",
        ["Online (Gemini AI)", "Offline (Local Rules)"],
        index=0
    )
    is_offline_manual = (system_mode == "Offline (Local Rules)")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Room & Kinetics Settings")
    mode = st.sidebar.radio("Room Format:", ["Solo Cabin (1 person)", "Group Room (Multiple people)"])

    if mode == "Solo Cabin (1 person)":
        total_people = 1
        default_vol = 10
    else:
        total_people = st.sidebar.number_input("Participants", 1, 60, 4)
        default_vol = 30

    room_vol = st.sidebar.number_input("Room Volume (m³)", 3, 300, default_vol)
    st.sidebar.markdown("---")

    if not st.session_state.session_running:
        st.sidebar.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.sidebar.button("Start Session", use_container_width=True):
            if is_hardware_mode and (not SERIAL_AVAILABLE or not selected_port):
                st.sidebar.error("ESP32 is not connected. Cannot start session.")
            else:
                st.session_state.session_running = True
                st.session_state.start_time = time.time()
                st.session_state.last_report = None
                st.session_state.data_history = []
                st.session_state.ieq_scores_history = []
                st.session_state.raw_buffer = {"co2": [], "temp": [], "lux": [], "db": []}
                st.session_state.trigger_timers = {"co2": 0, "sound": 0, "temp": 0, "light": 0}
                st.session_state.session_end_cache = {}
                st.session_state.last_packet_ts = None
                st.session_state.hw_error_msg = None
                st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="stop-btn">', unsafe_allow_html=True)
        if st.sidebar.button("End Session", use_container_width=True):
            st.session_state.session_running = False
            close_serial_safely()

            elapsed_sec = max(int(time.time() - (st.session_state.start_time or time.time())), 1)
            mins, secs = divmod(elapsed_sec, 60)
            total_time_str = f"{mins:02d}m {secs:02d}s"

            if not st.session_state.data_history:
                st.session_state.last_report = {
                    "empty": True,
                    "time": total_time_str,
                    "error": "No valid sensor measurements were recorded during this session."
                }
                st.session_state.start_time = None
                st.rerun()

            try:
                df_final = pd.DataFrame(st.session_state.data_history)
                avg_co2 = int(round(df_final["CO2 (ppm)"].mean()))
                max_db = int(round(df_final["Noise (dBA)"].max()))
                avg_lux = int(round(df_final["Light (Lux)"].mean()))
                avg_temp = round(float(df_final["Temperature (°C)"].mean()), 1)
                last_co2 = round(float(df_final["CO2 (ppm)"].iloc[-1]), 1)
                final_score = int(round(df_final["IEQ Index"].mean()))

                try:
                    df_final.to_csv(BACKUP_CSV_PATH, index=False)
                except Exception as e:
                    st.warning(f"Local CSV backup error: {e}")

                locked_metrics = create_locked_metrics_snapshot({
                    "score": final_score,
                    "avg_co2": avg_co2,
                    "last_co2": last_co2,
                    "max_db": max_db,
                    "avg_lux": avg_lux,
                    "avg_temp": avg_temp,
                })

                sheet_ok = export_to_google_sheets(
                    rejim=mode,
                    total_people=total_people,
                    duration_str=total_time_str,
                    focus_score=locked_metrics["score"],
                    final_co2=locked_metrics["last_co2"],
                    avg_temp=locked_metrics["avg_temp"]
                )

                ai_final_feedback = get_session_summary(locked_metrics, total_time_str, is_offline_manual)
                per_metric_reviews = get_per_metric_final_evaluations(locked_metrics, is_offline_manual)

                st.session_state.focus_history.append({
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Mode": mode,
                    "People": total_people,
                    "Duration": total_time_str,
                    "IEQ Index": f"{locked_metrics['score']}/100",
                    "Final CO₂": f"{locked_metrics['last_co2']} ppm",
                    "Avg Temp": f"{locked_metrics['avg_temp']} °C"
                })

                st.session_state.last_report = {
                    "empty": False,
                    "score": locked_metrics["score"],
                    "time": total_time_str,
                    "feedback": ai_final_feedback,
                    "per_metric": per_metric_reviews,
                    "sheet_status": sheet_ok
                }
            except Exception as e:
                st.session_state.last_report = {
                    "empty": True,
                    "time": total_time_str,
                    "error": f"Failed to generate session report: {e}"
                }

            st.session_state.start_time = None
            st.rerun()
        st.sidebar.markdown('</div>', unsafe_allow_html=True)

# ==============================================================
# Top Navigation Bar
# ==============================================================
nav_left, nav_center, nav_right = st.columns([2.2, 4.6, 2.2], vertical_alignment="center")

with nav_left:
    st.markdown(
        '<div style="font-family:\'Plus Jakarta Sans\',sans-serif;font-weight:800;font-size:1.25rem;letter-spacing:-0.03em;color:#0F172A;">'
        'Learn<span style="color:#2563EB;">Sphere</span>'
        '</div>',
        unsafe_allow_html=True
    )

with nav_center:
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button(
            "Home",
            key="nav_home",
            type="primary" if st.session_state.active_page == "Home" else "secondary",
            use_container_width=True
        ):
            st.session_state.active_page = "Home"
            st.rerun()
    with b2:
        if st.button(
            "Dashboard",
            key="nav_dashboard",
            type="primary" if st.session_state.active_page == "Dashboard" else "secondary",
            use_container_width=True
        ):
            st.session_state.active_page = "Dashboard"
            st.rerun()
    with b3:
        if st.button(
            "About",
            key="nav_about",
            type="primary" if st.session_state.active_page == "About" else "secondary",
            use_container_width=True
        ):
            st.session_state.active_page = "About"
            st.rerun()

with nav_right:
    if st.session_state.session_running:
        st.markdown(
            '<div style="text-align:right;"><span class="nav-live-pill">● Live Session</span></div>',
            unsafe_allow_html=True
        )

st.markdown('<hr style="margin: 10px 0 22px 0; border: none; border-top: 1px solid #E2E8F0;">', unsafe_allow_html=True)

# ==============================================================
# PAGE 1: HOME (Minimal Animated Brand Showcase Only)
# ==============================================================
def render_home_page():
    st.markdown(
        """
        <div class="page-animate">
            <div class="home-stage">
                <div class="aura-orb aura-1"></div>
                <div class="aura-orb aura-2"></div>
                <div class="aura-orb aura-3"></div>
                <h1 class="home-brand-title">LearnSphere</h1>
                <div class="brand-underline"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================================================
# PAGE 2: DASHBOARD (Live Monitoring, Report & History)
# ==============================================================
@st.fragment(run_every=1.0 if (st.session_state.session_running and st.session_state.active_page == "Dashboard") else None)
def render_live_dashboard():
    st.markdown(
        f'<div class="section-title">Live Metrics ({total_people} Participant{"s" if total_people > 1 else ""} · Thermal Load: {total_people * 100} W)</div>',
        unsafe_allow_html=True
    )
    k1, k2, k3, k4 = st.columns(4)

    status_badge_html = (
        '<span class="status-badge-offline">Offline Mode (Local Rules)</span>'
        if is_offline_manual or not client
        else '<span class="status-badge-online">Gemini AI Active</span>'
    )

    if st.session_state.session_running:
        step = len(st.session_state.data_history) + 1
        elapsed_sec = int(time.time() - (st.session_state.start_time or time.time()))
        mins, secs = divmod(elapsed_sec, 60)
        timer_text = f"{mins:02d}:{secs:02d}"

        if is_hardware_mode:
            hw_packet, hw_err = read_esp32_sensor_data(selected_port, baud_rate)
            if hw_err or hw_packet is None:
                st.error(f"{hw_err or 'ESP32 device is not connected or no measurement received.'}")
                k1.metric("CO₂ Level", "—")
                k2.metric("Ambient Noise", "—")
                k3.metric("Lighting", "—")
                k4.metric("Temperature", "—")
                st.markdown(
                    f"""
                    <div class="mentor-container">
                        <div class="mentor-header-row">
                            <div class="mentor-header-left">
                                <h3 class="mentor-title-left">AI Mentor</h3>
                                <span class="compact-timer-tag">Timer: {timer_text}</span>
                            </div>
                            {status_badge_html}
                        </div>
                        <p class="mentor-msg-text">Waiting for live measurements from the ESP32 device. Please verify your USB connection.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                return

            raw_co2 = hw_packet["co2"] + co2_baseline_offset
            raw_temp = hw_packet["temp"]
            raw_lux = hw_packet["lux"]
            raw_db = hw_packet["db"]

            prev_teo_co2 = (
                st.session_state.data_history[-1]["Theoretical CO2 (ppm)"]
                if st.session_state.data_history
                else raw_co2
            )
            teo_co2 = calculate_advanced_bio(room_vol, total_people, prev_teo_co2)
        else:
            prev_teo_co2 = (
                st.session_state.data_history[-1]["Theoretical CO2 (ppm)"]
                if st.session_state.data_history
                else 450.0
            )
            teo_co2 = calculate_advanced_bio(room_vol, total_people, prev_teo_co2)
            raw_co2 = teo_co2 + random.uniform(-2.0, 2.0) + co2_baseline_offset
            raw_db = random.randint(46, 56) if (10 <= step % 22 <= 14) else random.randint(34, 39)
            raw_lux = random.randint(430, 480) if (16 <= step % 28 <= 19) else random.randint(580, 680)
            heat_increment = (total_people * 0.015) * (step / 30.0)
            raw_temp = 22.5 + heat_increment + random.uniform(-0.1, 0.1)

        f_co2 = apply_moving_average("co2", raw_co2, window=5)
        f_temp = apply_moving_average("temp", raw_temp, window=5)
        f_lux = apply_moving_average("lux", raw_lux, window=3)
        f_db = apply_moving_average("db", raw_db, window=3)

        if None in (f_co2, f_temp, f_lux, f_db):
            st.error("Invalid numeric value (NaN/Inf) detected in sensor stream. Packet skipped.")
            return

        cur_co2 = max(400.0, f_co2)
        cur_temp = f_temp
        cur_lux = int(f_lux)
        cur_db = int(f_db)

        current_ieq_point = calculate_ieq_score(cur_co2, cur_temp, cur_lux, cur_db)
        st.session_state.ieq_scores_history.append(current_ieq_point)

        tt = st.session_state.trigger_timers
        tt["co2"] = tt["co2"] + 1 if cur_co2 > 1000 else 0
        tt["sound"] = tt["sound"] + 1 if cur_db > 40 else 0
        tt["temp"] = tt["temp"] + 1 if cur_temp >= 28.0 else 0
        tt["light"] = tt["light"] + 1 if cur_lux < 500 else 0

        st.session_state.data_history.append({
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Second": step,
            "CO2 (ppm)": cur_co2,
            "Theoretical CO2 (ppm)": teo_co2,
            "Noise (dBA)": cur_db,
            "Light (Lux)": cur_lux,
            "Temperature (°C)": cur_temp,
            "IEQ Index": current_ieq_point
        })

        if step % 60 == 0:
            try:
                pd.DataFrame(st.session_state.data_history).to_csv(BACKUP_CSV_PATH, index=False)
            except Exception as e:
                st.warning(f"Auto-backup error: {e}")

        df_window = pd.DataFrame(st.session_state.data_history[-300:])

        k1.metric("CO₂ Level", f"{cur_co2} ppm", delta=f"Model: {teo_co2} ppm")
        k2.metric("Ambient Noise", f"{cur_db} dBA", delta="Optimal" if cur_db <= 40 else "High >40", delta_color="inverse")
        k3.metric("Lighting", f"{cur_lux} Lux")
        k4.metric("Temperature", f"{cur_temp} °C", delta=f"{round(cur_temp - 24.8, 1)} °C")

        mentor_msg = (
            f"IEQ Focus Index: {current_ieq_point}/100. All parameters are within the optimal study zone "
            f"(Temp: 20.8-24.8 °C, Noise <=40 dBA, CO₂ <=1000 ppm)."
        )

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
                    "sound": f"Noise exceeded threshold ({cur_db} dBA > 40 dBA) — Monitoring ({active_dur}s)...",
                    "co2": f"CO₂ rising ({cur_co2} ppm > 1000 ppm) — Monitoring ({active_dur}s)...",
                    "temp": f"Critical temperature reached ({cur_temp} °C >= 28.0 °C) — Monitoring ({active_dur}s)...",
                    "light": f"Lighting dropped below standard ({cur_lux} Lux < 500) — Monitoring ({active_dur}s)..."
                }
                mentor_msg = local_alerts.get(active_factor)
            else:
                advice_text = get_smart_advice(active_factor, active_val, is_offline_manual)
                label_prefix = "Local Rule" if is_offline_manual or not client else "AI Advice"
                mentor_msg = f"{label_prefix} ({active_dur}s outside target): {advice_text}"

        st.markdown(
            f"""
            <div class="mentor-container">
                <div class="mentor-header-row">
                    <div class="mentor-header-left">
                        <h3 class="mentor-title-left">AI Mentor · IEQ Index: {current_ieq_point}/100</h3>
                        <span class="compact-timer-tag">Timer: {timer_text}</span>
                    </div>
                    {status_badge_html}
                </div>
                <p class="mentor-msg-text">{mentor_msg}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        ch1, ch2 = st.columns(2)
        with ch1:
            st.caption("CO₂ Dynamics: Measured vs. Persily-de Jonge Model (ppm)")
            st.line_chart(
                df_window.set_index("Second")[["CO2 (ppm)", "Theoretical CO2 (ppm)"]],
                color=["#2563EB", "#0EA5E9"]
            )
        with ch2:
            st.caption("Cognitive Ergonomics: IEQ Focus Index (0-100), Noise (dBA) & Temp (°C)")
            st.line_chart(
                df_window.set_index("Second")[["IEQ Index", "Noise (dBA)", "Temperature (°C)"]],
                color=["#10B981", "#E11D48", "#F59E0B"]
            )

    else:
        k1.metric("CO₂ Level", "—")
        k2.metric("Ambient Noise", "—")
        k3.metric("Lighting", "—")
        k4.metric("Temperature", "—")

        st.markdown(
            f"""
            <div class="mentor-container">
                <div class="mentor-header-row">
                    <div class="mentor-header-left">
                        <h3 class="mentor-title-left">AI Mentor</h3>
                        <span class="compact-timer-tag">Timer: 00:00</span>
                    </div>
                    {status_badge_html}
                </div>
                <p class="mentor-msg-text">System is on standby. Click Start Session in the left panel to begin real-time IEQ monitoring.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_dashboard_page():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="page-header">
            <h2 class="page-title">Telemetry Dashboard</h2>
            <p class="page-subtitle">Real-time Indoor Environmental Quality (IEQ) monitoring, Persily-de Jonge dynamics & Dual AI Mentor</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    render_live_dashboard()

    # End-of-Session Quality Report
    if st.session_state.last_report and not st.session_state.session_running:
        rep = st.session_state.last_report
        st.markdown("---")
        st.markdown('<div class="section-title">Session Quality Report</div>', unsafe_allow_html=True)

        if rep.get("empty"):
            st.error(rep.get("error", "No measurement data available."))
        else:
            if rep.get("sheet_status"):
                st.success("Session data was saved to Google Sheets and backed up locally.")
            else:
                st.warning("Cloud sync unavailable. Data is safely preserved in `learnsphere_live_backup.csv`.")

            r1, r2 = st.columns([3, 7])
            with r1:
                st.metric("IEQ Focus Score", f"{rep['score']} / 100")
                st.caption(f"Duration: {rep['time']}")
                if os.path.exists(BACKUP_CSV_PATH):
                    try:
                        with open(BACKUP_CSV_PATH, "rb") as f:
                            st.download_button(
                                "Download Telemetry CSV",
                                f,
                                file_name="learnsphere_session_data.csv",
                                mime="text/csv"
                            )
                    except Exception as e:
                        st.warning(f"CSV download error: {e}")
            with r2:
                st.info(f"**Mentor Summary:**\n\n{rep['feedback']}")

            per_metric = rep.get("per_metric", {})
            if per_metric:
                st.markdown('<div class="section-title" style="margin-top:18px;">Per-Metric Final Evaluation (Locked Values)</div>', unsafe_allow_html=True)
                m_cols = st.columns(4)
                for idx, m_key in enumerate(["co2", "temp", "lux", "db"]):
                    if m_key in per_metric:
                        item = per_metric[m_key]
                        with m_cols[idx]:
                            st.markdown(
                                f"""
                                <div class="ls-card">
                                    <h4>{item['label']}</h4>
                                    <p style="font-weight:600;color:#2563EB;margin-bottom:8px;">{item['value_str']}</p>
                                    <p>{item['feedback']}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

    # Focus History Table
    st.markdown("---")
    h_col1, h_col2 = st.columns([8, 2], vertical_alignment="center")
    with h_col1:
        st.markdown('<div class="section-title">Session History</div>', unsafe_allow_html=True)
    with h_col2:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("Clear History", use_container_width=True):
            st.session_state.focus_history = []
            st.session_state.ieq_scores_history = []
            st.session_state.last_report = None
            st.session_state.session_end_cache = {}
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.focus_history:
        st.dataframe(pd.DataFrame(st.session_state.focus_history), use_container_width=True)
    else:
        st.markdown(
            """
            <div class="empty-history-box">
                No completed focus sessions yet. Finish a session to see your logged history here.
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================
# PAGE 3: ABOUT (Based Strictly on Project Document)
# ==============================================================
def render_about_page():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="ls-card" style="margin-bottom: 22px; background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);">
            <span class="ls-card-tag tag-blue">About LearnSphere</span>
            <h2 style="font-size: 1.8rem; font-weight: 800; margin: 0 0 10px 0; color: #0F172A;">
                Maximum Focus and Cognitive Productivity in Learning Environments
            </h2>
            <p style="font-size: 1rem; color: #64748B; max-width: 860px;">
                LearnSphere is a smart IoT and AI ecosystem that monitors air quality, lighting, temperature, and noise
                in real time inside enclosed study rooms and libraries to prevent distraction before it starts.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-rose">The Problem</span>
                <h4>Why Focus Drops Indoors</h4>
                <p>
                    Fatigue and loss of focus during long study sessions are not only about low motivation.
                    Rising carbon dioxide (CO₂), uncomfortable temperatures, and background noise in enclosed rooms
                    can reduce the brain's decision-making ability by up to 50%.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-emerald">Our Solution</span>
                <h4>Making Invisible Barriers Visible</h4>
                <p>
                    LearnSphere measures room conditions second by second through a physical sensor station,
                    calculates a unified Focus Index (0–100), and delivers timely guidance before mental fatigue sets in.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title" style="margin-top:26px;">How It Works (3-Step Ecosystem)</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-blue">Step 1</span>
                <h4>Real-Time Monitoring (IoT Station)</h4>
                <p>
                    Our ESP32-S3 station continuously tracks air quality, temperature, lighting, and acoustics
                    using MQ-135, DHT11, BH1750, and MAX9814 sensors.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with s2:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-amber">Step 2</span>
                <h4>Scientific Analysis (IEQ Model)</h4>
                <p>
                    Collected data is processed using international ASHRAE 62.1 standards and the Persily–de Jonge
                    mass balance equation to produce a single optimality score.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with s3:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-emerald">Step 3</span>
                <h4>Dual AI Mentor Support</h4>
                <p>
                    When metrics drift outside optimal ranges, Gemini AI provides tailored advice. Without internet,
                    the system automatically switches to Offline Scientific Rules for uninterrupted support.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title" style="margin-top:26px;">Scientific Standards in Numbers</div>', unsafe_allow_html=True)
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-value" style="color:#2563EB;">0–100</div>
                <div class="stat-desc">Unified IEQ Focus Index combining four factors (0.35 IAQ + 0.30 TC + 0.20 VC + 0.15 AC).</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with n2:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-value" style="color:#10B981;">≤ 1000 ppm</div>
                <div class="stat-desc">Safe indoor carbon dioxide threshold based on ASHRAE standards.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with n3:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-value" style="color:#D97706;">20.8°C–24.8°C</div>
                <div class="stat-desc">Optimal thermal comfort zone that minimizes errors in cognitive tasks.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with n4:
        st.markdown(
            """
            <div class="stat-tile">
                <div class="stat-value" style="color:#E11D48;">≤ 40 dBA</div>
                <div class="stat-desc">Ideal acoustic quietness level for working memory and deep reading.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('<div class="section-title" style="margin-top:26px;">Our Team — Trihedron</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-blue">System Architect & AI Lead</span>
                <h4>İlkin Nadirli</h4>
                <p>System architecture, Streamlit telemetry dashboard, data analytics, and Dual AI Mentor integration.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with t2:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-emerald">Hardware Specialist</span>
                <h4>Səma Behbudova</h4>
                <p>ESP32-S3 hardware design, sensor integration, and thermal insulation engineering.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with t3:
        st.markdown(
            """
            <div class="ls-card">
                <span class="ls-card-tag tag-amber">Scientific Researcher</span>
                <h4>Fatimə Məmmədova</h4>
                <p>ASHRAE standards analysis, IEQ weighting models, and field research.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
        <div class="ls-card" style="margin-top: 22px;">
            <span class="ls-card-tag tag-blue">Pilot Deployment & Vision</span>
            <h4>From Qarabağ University to Smart Campuses</h4>
            <p>
                Currently being prepared for pilot deployment in the library and reading halls of Qarabağ University,
                LearnSphere aims to grow into an accessible Smart Campus solution for universities, schools, and modern offices.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================
# Page Router
# ==============================================================
if st.session_state.active_page == "Home":
    render_home_page()
elif st.session_state.active_page == "Dashboard":
    render_dashboard_page()
else:
    render_about_page()