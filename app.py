import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Configurazione della pagina
st.set_page_config(
    page_title="QuantEdge - Developed Markets PAC Screener",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Personalizzato (Dark Theme Globale: Pagina, Sidebar e Pop-up Modal)
st.markdown("""
<style>
/* Sfondo Generale */
.stApp {
    background-color: #0b0e14;
    color: #e2e8f0;
}
/* Personalizzazione Sidebar Dark */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stNumberInput input {
    background-color: #131822 !important;
    color: #00e676 !important;
    border: 1px solid #1e293b !important;
    border-radius: 6px;
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
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}
.metric-subtitle {
    font-size: 12px;
    color: #00e676;
    margin-top: 4px;
}
/* Badge della Tabella */
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
/* Styling del Pop-up Modale in Dark Mode */
[data-testid="stModal"] > div:first-child {
    background-color: #0d1117 !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: PARAMETRI PAC E SALVADANAIO ---
st.sidebar.header("⚙️ Impostazioni PAC & Liquidità")
monthly_budget = st.sidebar.number_input(
    "Budget Mensile PAC (€)",
    min_value=50,
    max_value=10000,
    value=200,
    step=50,
    help="Importo ordinario da investire ogni mese."
)
savings_cash = st.sidebar.number_input(
    "Salvadanaio / Liquidità Inutilizzata (€)",
    min_value=0,
    max_value=10000,
    value=150,
    step=10,
    help="Soldi avanzati dagli acquisti precedenti o risparmi extra pronti da investire."
)
st.sidebar.markdown("---")
st.sidebar.caption("💡 **Regola del Salvadanaio:**\nSe ci sono ETF in **Strong Buy** (molto convenienti), l'algoritmo preleva l'extra dal salvadanaio e lo aggiunge ai €200 mensili per amplificare l'acquisto a sconto.")

# --- HEADER ---
st.markdown("""
<div class="header-box">
<div class="brand-title">Q <span style="color: #ffffff;">Quant</span><span style="color: #00e676;">Edge</span></div>
<div class="live-status">● DEVELOPED MARKETS PAC <span style="color: #94a3b8;">LIVE</span></div>
</div>
""", unsafe_allow_html=True)

# --- CALCOLO SEGNALE PAC ---
def calculate_pac_signal(rsi_val, bollinger_val, drawdown_val):
    rsi = float(rsi_val)
    drawdown = float(drawdown_val.replace('%', ''))
    if rsi < 45 or bollinger_val == "Lower" or drawdown < -10.0:
        return "Strong Buy"
    elif rsi > 60 or bollinger_val == "Upper":
        return "Wait"
    else:
        return "Accumulate"

# --- DATI ETF (MERCATI SVILUPPATI - SENZA AGGH) ---
raw_data = [
    {"ETF": "VWCE", "Name": "Vanguard FTSE All-World", "Price": "€108.42", "Change": "+1.34%", "RSI": "62.4", "Bollinger": "Upper", "Drawdown": "-4.2%", "MACD": "Bullish", "Seed": 10},
    {"ETF": "IWDA", "Name": "iShares Core MSCI World", "Price": "€94.18", "Change": "-0.45%", "RSI": "43.1", "Bollinger": "Lower", "Drawdown": "-11.5%", "MACD": "Bearish", "Seed": 42},
    {"ETF": "SXR8", "Name": "iShares Core S&P 500", "Price": "€485.20", "Change": "+0.62%", "RSI": "56.8", "Bollinger": "Mid", "Drawdown": "-6.4%", "MACD": "Neutral", "Seed": 15},
    {"ETF": "MEUD", "Name": "Amundi MSCI Europe", "Price": "€38.56", "Change": "-0.12%", "RSI": "41.2", "Bollinger": "Lower", "Drawdown": "-9.8%", "MACD": "Bearish", "Seed": 99},
    {"ETF": "CSX5", "Name": "iShares Core EURO STOXX 50", "Price": "€52.10", "Change": "+0.23%", "RSI": "51.0", "Bollinger": "Mid", "Drawdown": "-7.5%", "MACD": "Neutral", "Seed": 27}
]

# Calcolo segnali
data = []
for item in raw_data:
    item["Signal"] = calculate_pac_signal(item["RSI"], item["Bollinger"], item["Drawdown"])
    data.append(item)

df = pd.DataFrame(data)

# --- LOGICA ALLOCAZIONE DINAMICA E IMPORTO EURO ---
strong_buy_count = len(df[df["Signal"] == "Strong Buy"])
extra_invested = savings_cash if strong_buy_count > 0 else 0
total_investable = monthly_budget + extra_invested

weights = {"Strong Buy": 2.5, "Accumulate": 1.0, "Wait": 0.0}
df["Weight"] = df["Signal"].map(weights)
total_weight = df["Weight"].sum()

if total_weight > 0:
    df["Allocazione_Euro"] = (df["Weight"] / total_weight) * total_investable
else:
    df["Allocazione_Euro"] = 0.0

# --- FUNZIONE GENERAZIONE GRAFICI PER POP-UP E DASHBOARD ---
def generate_etf_charts(etf_symbol, seed_val):
    dates = pd.date_range(start="2026-01-01", end="2026-08-31", freq="D")
    np.random.seed(seed_val)
    base_price = 100 if etf_symbol != "SXR8" else 480
    price_trend = np.linspace(base_price * 0.85, base_price * 1.05, len(dates)) + np.sin(np.linspace(0, 12, len(dates))) * (base_price * 0.03)
    sma_20 = pd.Series(price_trend).rolling(20).mean().bfill()
    sma_200 = pd.Series(price_trend).rolling(200).mean()
    bb_upper = price_trend + (base_price * 0.025)
    bb_lower = price_trend - (base_price * 0.025)

    # Prezzo
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=dates, y=price_trend, mode='lines', name='Price', line=dict(color='#00e676', width=2)))
    fig_price.add_trace(go.Scatter(x=dates, y=sma_20, mode='lines', name='SMA 20', line=dict(color='#eab308', width=1.5)))
    fig_price.add_trace(go.Scatter(x=dates, y=sma_200, mode='lines', name='SMA 200', line=dict(color='#a855f7', width=1.5, dash='dash')))
    fig_price.add_trace(go.Scatter(x=dates, y=bb_upper, mode='lines', name='BB Upper', line=dict(color='#2563eb', width=1, dash='dot')))
    fig_price.add_trace(go.Scatter(x=dates, y=bb_lower, mode='lines', name='BB Lower', line=dict(color='#2563eb', width=1, dash='dot')))
    fig_price.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(showgrid=True, gridcolor="#1e293b"),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", side="right")
    )

    # MACD
    macd_line = np.sin(np.linspace(0, 10, len(dates))) * 0.5 + 0.1
    signal_line = np.sin(np.linspace(0, 10, len(dates)) - 0.2) * 0.45 + 0.1
    histogram = macd_line - signal_line
    fig_macd = go.Figure()
    colors = ['#00e676' if h >= 0 else '#ff5252' for h in histogram]
    fig_macd.add_trace(go.Bar(x=dates, y=histogram, name='Histogram', marker_color=colors))
    fig_macd.add_trace(go.Scatter(x=dates, y=macd_line, mode='lines', name='MACD Line', line=dict(color='#3b82f6', width=1.5)))
    fig_macd.add_trace(go.Scatter(x=dates, y=signal_line, mode='lines', name='Signal Line', line=dict(color='#eab308', width=1.5)))
    fig_macd.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        margin=dict(l=20, r=20, t=20, b=20),
        height=200,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        xaxis=dict(showgrid=True, gridcolor="#1e293b"),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", side="right")
    )

    return fig_price, fig_macd

# --- FUNZIONE DIALOG/POP-UP IN STYLE DARK ---
@st.dialog("📊 Analisi Dettagliata ETF", width="large")
def show_etf_popup(etf_info):
    st.markdown(f"### **{etf_info['ETF']}** - {etf_info['Name']}")
    
    # Kpi veloci
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Prezzo", etf_info["Price"], etf_info["Change"])
    p2.metric("RSI (14)", etf_info["RSI"])
    p3.metric("Drawdown", etf_info["Drawdown"])
    p4.metric("Allocazione Euro", f"€{etf_info['Allocazione_Euro']:.2f}")
    st.write("")
    
    fig_p, fig_m = generate_etf_charts(etf_info['ETF'], etf_info['Seed'])
    st.subheader("Andamento Prezzo & Bande di Bollinger")
    st.plotly_chart(fig_p, use_container_width=True)
    st.subheader("Indicatore MACD")
    st.plotly_chart(fig_m, use_container_width=True)

# --- TITOLO E FILTRI ---
col_title, col_filter = st.columns([2, 1])
with col_title:
    st.title("Developed Markets PAC Screener")
    st.write("Calcolatore dell'importo esatto in **Euro** da investire per ciascun ETF.\nClicca su un titolo per aprire la scheda nel **pop-up scuro**.")

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
top_discount_etf = df.sort_values(by="Drawdown")["ETF"].iloc[0]
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-title">CAPITALE TOTALE DA INVESTIRE</div>
    <div class="metric-value">€{total_investable:.2f}</div>
    <div class="metric-subtitle">€{monthly_budget:.0f} PAC + €{extra_invested:.0f} Extra</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-title">SALVADANAIO RIMANENTE</div>
    <div class="metric-value" style="color: {'#fbbf24' if extra_invested > 0 else '#00e676'};">€{(savings_cash - extra_invested):.2f}</div>
    <div class="metric-subtitle">{"Fondi impiegati a sconto!" if extra_invested > 0 else "Nessun Strong Buy attivo"}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-title">OPPORTUNITÀ A SCONTO</div>
    <div class="metric-value" style="color: #00e676;">{strong_buy_count} ETF</div>
    <div class="metric-subtitle">Signal: Strong Buy</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
    <div class="metric-title">MAGGIOR SCONTO</div>
    <div class="metric-value" style="color: #00e676;">{top_discount_etf}</div>
    <div class="metric-subtitle">Priorità d'acquisto</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- RIPARTIZIONE IMPORTO EURO SU CIASCUN ETF ---
st.subheader(f"📊 Importo Esatto da Spendere Questo Mese (Totale: €{total_investable:.2f})")
alloc_cols = st.columns(len(df))
for idx, row in df.iterrows():
    with alloc_cols[idx]:
        color = "#00e676" if row["Allocazione_Euro"] > 0 else "#64748b"
        st.markdown(f"""
        <div class="metric-card" style="text-align: center; padding: 12px;">
        <div style="font-size: 14px; font-weight: 800; color: #ffffff;">{row['ETF']}</div>
        <div style="font-size: 20px; font-weight: 700; color: {color}; margin: 5px 0;">€{row['Allocazione_Euro']:.2f}</div>
        <div style="font-size: 11px; color: #94a3b8;">{row['Signal']}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.subheader("▼ Core Developed ETFs Technical Signals (Clicca per Aprire Pop-Up)")

df_display = df.copy()
if filter_option != "ALL":
    df_display = df_display[df_display["Signal"] == filter_option]

# Layout tabella con pulsante per il Pop-Up
cols = st.columns([1.8, 1, 1, 1, 1, 1, 1, 1, 1])
headers = ["ETF / DETTAGLIO", "PRICE", "CHANGE", "RSI (14)", "BOLLINGER", "DRAWDOWN", "MACD", "PAC SIGNAL", "COMPRA (€)"]
for col, header in zip(cols, headers):
    col.markdown(f"**<span style='color: #64748b; font-size: 11px;'>{header}</span>**", unsafe_allow_html=True)

st.divider()

for _, row in df_display.iterrows():
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([1.8, 1, 1, 1, 1, 1, 1, 1, 1])
    
    if c1.button(f"🔍 {row['ETF']}", key=f"btn_{row['ETF']}", help=f"Apri grafico e dettagli di {row['Name']}"):
        show_etf_popup(row)
        
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
    
    c9.markdown(f"<strong style='color: #00e676;'>€{row['Allocazione_Euro']:.2f}</strong>", unsafe_allow_html=True)

st.write("")

# --- GRAFICO INIZIALE (VISTA STANDARD) ---
st.subheader("IWDA - iShares Core MSCI World (Vista Generale)")
fig_p_def, fig_m_def = generate_etf_charts("IWDA", 42)
st.plotly_chart(fig_p_def, use_container_width=True)
st.plotly_chart(fig_m_def, use_container_width=True)

# Insight Box
st.markdown(f"""
<div class="insight-box">
📊 <b>Nuova Funzionalità Pop-up Dark:</b> Cliccando su uno qualsiasi dei pulsanti <b>🔍 ETF</b> nella prima colonna della tabella, si aprirà una finestra modale in stile scuro con l'andamento dei prezzi, le Bande di Bollinger e il pannello MACD dedicati a quel singolo titolo.
</div>
""", unsafe_allow_html=True)

st.caption("Source: Simulated market data · Developed Markets PAC Screener")