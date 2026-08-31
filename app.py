import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Configurazione della pagina
st.set_page_config(
    page_title="QuantEdge - Developed Markets PAC Screener",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS Personalizzato (Dark Theme)
st.markdown("""
<style>
    /* Sfondo generale */
    .stApp {
        background-color: #0b0e14;
        color: #e2e8f0;
    }
    
    /* Header Bar */
    .header-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0px 20px 0px;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 800;
        color: #00e676;
    }
    .live-status {
        font-size: 13px;
        color: #00e676;
        font-weight: 600;
    }

    /* Card delle Metriche */
    .metric-card {
        background-color: #131822;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .metric-title {
        font-size: 11px;
        color: #64748b;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #00e676;
        margin-top: 4px;
    }

    /* Badge della tabella */
    .badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        text-align: center;
    }
    .badge-green { background-color: #064e3b; color: #34d399; }
    .badge-yellow { background-color: #451a03; color: #fbbf24; }
    .badge-red { background-color: #4c0519; color: #f87171; }
    
    /* Box Insights */
    .insight-box {
        background-color: #131822;
        border-left: 3px solid #00e676;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 13px;
        margin-top: 10px;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="header-box">
    <div class="brand-title">Q <span style="color: #ffffff;">Quant</span><span style="color: #00e676;">Edge</span></div>
    <div class="live-status">● DEVELOPED MARKETS PAC &nbsp;&nbsp;<span style="color: #94a3b8;">10:44:55 CET</span></div>
</div>
""", unsafe_allow_html=True)

# --- TITOLO E FILTRI ---
col_title, col_filter = st.columns([2, 1])

with col_title:
    st.title("Developed Markets PAC Screener")
    st.write("Monitoraggio dedicato esclusivamente ai **mercati sviluppati e stabili** per l'accumulo di lungo termine.")

with col_filter:
    st.write("")
    filter_option = st.radio(
        "", 
        ["ALL", "Strong Buy", "Accumulate", "Wait"], 
        horizontal=True,
        label_visibility="collapsed"
    )

st.write("")

# --- TOP CARDS (KPIs) ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">PAC MONTHLY BUDGET</div>
        <div class="metric-value">€200</div>
        <div class="metric-subtitle">Quota fissa programmata</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">RISK PROFILE</div>
        <div class="metric-value" style="color: #00e676;">Low / Moderate</div>
        <div class="metric-subtitle" style="color: #94a3b8;">Solo mercati sviluppati</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">BEST DISCOUNT ETF</div>
        <div class="metric-value" style="color: #00e676;">IWDA</div>
        <div class="metric-subtitle">-11.5% dai massimi</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-title">AVG DRAWDOWN</div>
        <div class="metric-value" style="color: #fbbf24;">-8.7%</div>
        <div class="metric-subtitle" style="color: #94a3b8;">Basket Developed World</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.subheader("▼ Core Developed ETFs Signals")

# --- CALCOLO SEGNALE PAC ---
def calculate_pac_signal(rsi_val, bollinger_val, drawdown_val):
    rsi = float(rsi_val)
    drawdown = float(drawdown_val.replace('%', ''))
    
    if rsi < 45 or bollinger_val == "Lower" or drawdown < -12.0:
        return "Strong Buy"
    elif rsi > 60 or bollinger_val == "Upper":
        return "Wait"
    else:
        return "Accumulate"

# --- DATI ETF (SOLO MERCATI SVILUPPATI E CORE) ---
raw_data = [
    {"ETF": "VWCE", "Name": "Vanguard FTSE All-World (Dev Focus)", "Price": "€108.42", "Change": "+1.34%", "RSI": "62.4", "Bollinger": "Upper", "Drawdown": "-8.2%", "MACD": "Bullish"},
    {"ETF": "IWDA", "Name": "iShares Core MSCI World (Dev Markets)", "Price": "€94.18", "Change": "-0.45%", "RSI": "43.1", "Bollinger": "Lower", "Drawdown": "-11.5%", "MACD": "Bearish"},
    {"ETF": "SXR8", "Name": "iShares Core S&P 500 UCITS ETF", "Price": "€485.20", "Change": "+0.62%", "RSI": "56.8", "Bollinger": "Mid", "Drawdown": "-6.4%", "MACD": "Neutral"},
    {"ETF": "MEUD", "Name": "Amundi MSCI Europe UCITS ETF", "Price": "€38.56", "Change": "-0.12%", "RSI": "44.2", "Bollinger": "Lower", "Drawdown": "-9.8%", "MACD": "Bearish"},
    {"ETF": "CSX5", "Name": "iShares Core EURO STOXX 50", "Price": "€52.10", "Change": "+0.23%", "RSI": "51.0", "Bollinger": "Mid", "Drawdown": "-7.5%", "MACD": "Neutral"},
    {"ETF": "AGGH", "Name": "iShares Core Global Agg Bond", "Price": "€44.63", "Change": "+0.12%", "RSI": "48.3", "Bollinger": "Mid", "Drawdown": "-6.1%", "MACD": "Neutral"},
]

data = []
for item in raw_data:
    item["Signal"] = calculate_pac_signal(item["RSI"], item["Bollinger"], item["Drawdown"])
    data.append(item)

df = pd.DataFrame(data)

if filter_option != "ALL":
    df = df[df["Signal"] == filter_option]

# Layout tabella
cols = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
headers = ["ETF", "PRICE", "CHANGE", "RSI (14)", "BOLLINGER", "52W DRAWDOWN", "MACD", "PAC SIGNAL"]

for col, header in zip(cols, headers):
    col.markdown(f"**<span style='color: #64748b; font-size: 11px;'>{header}</span>**", unsafe_allow_html=True)

st.divider()

for _, row in df.iterrows():
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1])
    
    c1.markdown(f"**{row['ETF']}** <span style='color: #64748b; font-size: 11px;'>{row['Name']}</span>", unsafe_allow_html=True)
    c2.markdown(f"**{row['Price']}**")
    
    change_color = "#00e676" if "+" in row["Change"] else "#ff5252"
    c3.markdown(f"<span style='color: {change_color}; font-weight:600;'>{row['Change']}</span>", unsafe_allow_html=True)
    
    rsi_val = float(row['RSI'])
    rsi_class = "badge-green" if rsi_val <= 45 else ("badge-yellow" if rsi_val <= 60 else "badge-red")
    c4.markdown(f"<span class='badge {rsi_class}'>● {row['RSI']}</span>", unsafe_allow_html=True)
    
    boll_class = "badge-green" if row['Bollinger'] == "Lower" else ("badge-yellow" if row['Bollinger'] == "Mid" else "badge-red")
    c5.markdown(f"<span class='badge {boll_class}'>● {row['Bollinger']}</span>", unsafe_allow_html=True)
    
    dd_val = float(row['Drawdown'].replace('%', ''))
    dd_class = "badge-green" if dd_val < -10.0 else ("badge-yellow" if dd_val < -6.0 else "badge-red")
    c6.markdown(f"<span class='badge {dd_class}'>● {row['Drawdown']}</span>", unsafe_allow_html=True)
    
    macd_class = "badge-green" if row['MACD'] == "Bearish" else ("badge-yellow" if row['MACD'] == "Neutral" else "badge-red")
    c7.markdown(f"<span class='badge {macd_class}'>● {row['MACD']}</span>", unsafe_allow_html=True)
    
    signal_class = "badge-green" if row['Signal'] == "Strong Buy" else ("badge-yellow" if row['Signal'] == "Accumulate" else "badge-red")
    c8.markdown(f"<span class='badge {signal_class}'>● {row['Signal']}</span>", unsafe_allow_html=True)

st.write("")

# --- GRAFICI SIMULATI ---
dates = pd.date_range(start="2026-01-01", end="2026-08-31", freq="D")
np.random.seed(42)
price_trend = np.linspace(80, 102, len(dates)) + np.sin(np.linspace(0, 12, len(dates))) * 3
sma_20 = pd.Series(price_trend).rolling(20).mean().bfill()
sma_200 = pd.Series(price_trend).rolling(200).mean()
bb_upper = price_trend + 2.5
bb_lower = price_trend - 2.5

# GRAFICO PREZZO
st.subheader("IWDA - iShares Core MSCI World")

fig_price = go.Figure()
fig_price.add_trace(go.Scatter(x=dates, y=price_trend, mode='lines', name='Price', line=dict(color='#00e676', width=2)))
fig_price.add_trace(go.Scatter(x=dates, y=sma_20, mode='lines', name='SMA 20', line=dict(color='#eab308', width=1.5)))
fig_price.add_trace(go.Scatter(x=dates, y=sma_200, mode='lines', name='SMA 200', line=dict(color='#a855f7', width=1.5, dash='dash')))
fig_price.add_trace(go.Scatter(x=dates, y=bb_upper, mode='lines', name='BB Upper', line=dict(color='#2563eb', width=1, dash='dot')))
fig_price.add_trace(go.Scatter(x=dates, y=bb_lower, mode='lines', name='BB Lower', line=dict(color='#2563eb', width=1, dash='dot')))

fig_price.update_layout(
    template="plotly_dark",
    paper_bgcolor="#131822",
    plot_bgcolor="#131822",
    margin=dict(l=20, r=20, t=20, b=20),
    height=350,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    xaxis=dict(showgrid=True, gridcolor="#1e293b"),
    yaxis=dict(showgrid=True, gridcolor="#1e293b", side="right")
)

st.plotly_chart(fig_price, use_container_width=True)

# Insight Box
st.markdown("""
<div class="insight-box">
    💡 <b>Portafoglio Core Sviluppato:</b> Gli ETF in elenco (S&P 500, MSCI World, Europa Sviluppata) includono solo le aziende economicamente più solide al mondo. L'accumulo a sconto su questi strumenti riduce i rischi di lungo periodo mantenendo un'ottima crescita.
</div>
""", unsafe_allow_html=True)

st.caption("Source: Simulated market data · Developed Markets PAC Screener | QuantEdge v2.6")