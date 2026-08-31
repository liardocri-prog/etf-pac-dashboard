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

# 2. CSS Personalizzato (Dark Theme Globale, Bottoni Custom & Modali Scure)
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

    /* Forzatura Totale Dark Mode sul Modale / Pop-up di Streamlit */
    [data-testid="stModal"] {
        background-color: rgba(11, 14, 20, 0.85) !important;
    }
    [data-testid="stModal"] > div:first-child {
        background-color: #0d1117 !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stModal"] * {
        color: #e2e8f0;
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
st.sidebar.caption("💡 **Regola del Salvadanaio:**\nSe l'ETF scelto del mese è in **Strong Buy**, l'algoritmo preleva l'extra dal salvadanaio e lo somma ai €200 mensili per massimizzare l'acquisto a sconto.")

# --- HEADER ---
st.markdown("""
<div class="header-box">
    <div class="brand-title">Q <span style="color: #ffffff;">Quant</span><span style="color: #00e676;">Edge</span></div>
    <div class="live-status">● DEVELOPED MARKETS PAC &nbsp;&nbsp;<span style="color: #94a3b8;">LIVE</span></div>
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

# --- DATI ETF (MERCATI SVILUPPATI) ---
raw_data = [
    {"ETF": "VWCE", "Name": "Vanguard FTSE All-World", "Price": "€108.42", "Change": "+1.34%", "RSI": "62.4", "Bollinger": "Upper", "Drawdown": "-4.2%", "MACD": "Bullish", "Seed": 10},
    {"ETF": "IWDA", "Name": "iShares Core MSCI World", "Price": "€94.18", "Change": "-0.45%", "RSI": "43.1", "Bollinger": "Lower", "Drawdown": "-11.5%", "MACD": "Bearish", "Seed": 42},
    {"ETF": "SXR8", "Name": "iShares Core S&P 500", "Price": "€485.20", "Change": "+0.62%", "RSI": "56.8", "Bollinger": "Mid", "Drawdown": "-6.4%", "MACD": "Neutral", "Seed": 15},
    {"ETF": "MEUD", "Name": "Amundi MSCI Europe", "Price": "€38.56", "Change": "-0.12%", "RSI": "41.2", "Bollinger": "Lower", "Drawdown": "-9.8%", "MACD": "Bearish", "Seed": 99},
    {"ETF": "CSX5", "Name": "iShares Core EURO STOXX 50", "Price": "€52.10", "Change": "+0.23%", "RSI": "51.0", "Bollinger": "Mid", "Drawdown": "-7.5%", "MACD": "Neutral", "Seed": 27},
    {"ETF": "AGGH", "Name": "iShares Core Global Agg Bond", "Price": "€44.63", "Change": "+0.12%", "RSI": "48.3", "Bollinger": "Mid", "Drawdown": "-5.1%", "MACD": "Neutral", "Seed": 77},
]

data = []
for item in raw_data:
    item["Signal"] = calculate_pac_signal(item["RSI"], item["Bollinger"], item["Drawdown"])
    item["DD_Val"] = float(item["Drawdown"].replace('%', ''))
    data.append(item)

df = pd.DataFrame(data)

# --- LOGICA DI SELEZIONE DELL'UNICA AZIONE PIÙ CONVENIENTE ---
df = df.sort_values(by="DD_Val", ascending=True).reset_index(drop=True)
best_etf_idx = 0
best_etf_signal = df.loc[best_etf_idx, "Signal"]

extra_invested = savings_cash if best_etf_signal == "Strong Buy" else 0
total_investable = monthly_budget + extra_invested

df["Allocazione_Euro"] = 0.0
df.loc[best_etf_idx, "Allocazione_Euro"] = total_investable

# --- FUNZIONE GENERAZIONE GRAFICI ---
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
        font=dict(color="#e2e8f0"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color="#e2e8f0")),
        xaxis=dict(showgrid=True, gridcolor="#1e293b", tickfont=dict(color="#e2e8f0")),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", side="right", tickfont=dict(color="#e2e8f0"))
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
        font=dict(color="#e2e8f0"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=200,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color="#e2e8f0")),
        xaxis=dict(showgrid=True, gridcolor="#1e293b", tickfont=dict(color="#e2e8f0")),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", side="right", tickfont=dict(color="#e2e8f0"))
    )

    return fig_price, fig_macd

# --- FUNZIONE POP-UP DARK ---
@st.dialog("📊 Analisi Dettagliata ETF", width="large")
def show_etf_popup(etf_info):
    st.markdown(f"### **{etf_info['ETF']}** - {etf_info['Name']}")
    
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
    st.write("Acquisto mensile concentrato **sull'ETF più conveniente** (maggiore sconto / drawdown). Clicca sul badge dell'ETF per aprire il pop-up.")

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
selected_etf_name = df.loc[best_etf_idx, "ETF"]

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">INVESTIMENTO DEL MESE</div>
        <div class="metric-value">€{total_investable:.2f}</div>
        <div class="metric-subtitle">Interamente su {selected_etf_name}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">SALVADANAIO RIMANENTE</div>
        <div class="metric-value" style="color: {'#fbbf24' if extra_invested > 0 else '#00e676'};">€{(savings_cash - extra_invested):.2f}</div>
        <div class="metric-subtitle">{"Prelievo extra attivato!" if extra_invested > 0 else "In attesa di Strong Buy"}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">SCELTA TOP DEL MESE</div>
        <div class="metric-value" style="color: #00e676;">{selected_etf_name}</div>
        <div class="metric-subtitle">Max sconto: {df.loc[best_etf_idx, 'Drawdown']}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">SEGNALE TOP</div>
        <div class="metric-value" style="color: #00e676;">{best_etf_signal}</div>
        <div class="metric-subtitle">Priorità assoluta d'acquisto</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- RIPARTIZIONE IMPORTO EURO ---
st.subheader(f"💶 Assegnazione Budget: €{total_investable:.2f} interamente su {selected_etf_name}")

alloc_cols = st.columns(len(df))
for idx, row in df.iterrows():
    with alloc_cols[idx]:
        is_chosen = row["Allocazione_Euro"] > 0
        color = "#00e676" if is_chosen else "#64748b"
        border_style = "border: 2px solid #00e676;" if is_chosen else "border: 1px solid #1e293b;"
        st.markdown(f"""
        <div class="metric-card" style="text-align: center; padding: 12px; {border_style}">
            <div style="font-size: 14px; font-weight: 800; color: #ffffff;">{row['ETF']}</div>
            <div style="font-size: 18px; font-weight: 700; color: {color}; margin: 5px 0;">€{row['Allocazione_Euro']:.2f}</div>
            <div style="font-size: 11px; color: #94a3b8;">{row['Signal']}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.subheader("▼ Core Developed ETFs Technical Signals")

df_display = df.copy()
if filter_option != "ALL":
    df_display = df_display[df_display["Signal"] == filter_option]

cols = st.columns([1.8, 1, 1, 1, 1, 1, 1, 1, 1])
headers = ["ETF / DETTAGLIO", "PRICE", "CHANGE", "RSI (14)", "BOLLINGER", "DRAWDOWN", "MACD", "PAC SIGNAL", "COMPRA (€)"]

for col, header in zip(cols, headers):
    col.markdown(f"**<span style='color: #64748b; font-size: 11px;'>{header}</span>**", unsafe_allow_html=True)

st.divider()

for _, row in df_display.iterrows():
    c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns([1.8, 1, 1, 1, 1, 1, 1, 1, 1])
    
    # Sostituiamo il bottone bianco con un pulsante nativo trasparente e gestito tramite form/callback o usiamo un trucco pulito con st.button stilizzato
    # Per rendere il bottone pulito senza sfondo bianco, usiamo lo stile minimal dei bottoni o un interruttore pulito:
    with c1:
        # Colore del bordo in base al segnale o all'andamento
        btn_border = "#34d399" if row['Signal'] == "Strong Buy" else ("#fbbf24" if row['Signal'] == "Accumulate" else "#f87171")
        if st.button(f"🔍 {row['ETF']}", key=f"btn_{row['ETF']}", help=f"Apri grafico e dettagli di {row['Name']}"):
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

# --- GRAFICO INIZIALE (VISTA STANDARD SULL'ETF TOP DEL MESE) ---
st.subheader(f"{selected_etf_name} - Analisi Grafica Principale")
fig_p_def, fig_m_def = generate_etf_charts(selected_etf_name, int(df.loc[best_etf_idx, "Seed"]))
st.plotly_chart(fig_p_def, use_container_width=True)
st.plotly_chart(fig_m_def, use_container_width=True)

st.markdown(f"""
<div class="insight-box">
    📊 <b>Strategia di Concentrazione Mensile:</b> 
    Questo mese tutto il budget (€{total_investable:.2f}) viene allocato al 100% su <b>{selected_etf_name}</b> in quanto risulta l'asset più conveniente sul mercato. Gli altri ETF rimangono a zero fino al prossimo mese.
</div>
""", unsafe_allow_html=True)

st.caption("Source: Simulated market data · Developed Markets PAC Screener | QuantEdge v3.1")