import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. Configurazione della pagina
st.set_page_config(
    page_title="QuantEdge - Developed Markets PAC Screener",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Personalizzato con Selettori Forzati per Bottoni e Modali
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

    /* Forzatura Universale Bottoni */
    button, .stButton button, div.stButton > button {
        background-color: #131822 !important;
        color: #00e676 !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        width: 100%;
    }
    button:hover, .stButton button:hover, div.stButton > button:hover {
        background-color: #1e293b !important;
        border-color: #00e676 !important;
        color: #ffffff !important;
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

    /* Forzatura Totale Dark Mode sul Modale (BaseWeb Dialog) */
    div[data-baseweb="modal"], div[data-baseweb="dialog"] {
        background-color: rgba(11, 14, 20, 0.85) !important;
    }
    div[data-baseweb="modal"] > div, div[data-baseweb="dialog"] > div {
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
st.sidebar.caption("💡 **Regola del Salvadanaio:**\nSe l'ETF scelto del mese è in **Strong Buy**, l'algoritmo preleva l'extra dal salvadanaio e lo somma ai €200 mensili per massimizzare l'acquisto a sconto.")

# --- HEADER ---
st.markdown("""
<div class="header-box">
    <div class="brand-title">Q <span style="color: #ffffff;">Quant</span><span style="color: #00e676;">Edge</span></div>
    <div class="live-status">● DEVELOPED MARKETS PAC &nbsp;&nbsp;<span style="color: #94a3b8;">LIVE (YFINANCE)</span></div>
</div>
""", unsafe_allow_html=True)

# --- CONFIGURAZIONE TICKERS (Yahoo Finance) ---
ETF_CONFIG = {
    "VWCE": {"ticker": "VWCE.DE", "name": "Vanguard FTSE All-World"},
    "IWDA": {"ticker": "IWDA.AS", "name": "iShares Core MSCI World"},
    "SXR8": {"ticker": "SXR8.DE", "name": "iShares Core S&P 500"},
    "MEUD": {"ticker": "MEUD.PA", "name": "Amundi MSCI Europe"},
    "CSX5": {"ticker": "CSX5.DE", "name": "iShares Core EURO STOXX 50"},
    "AGGH": {"ticker": "AGGH.AS", "name": "iShares Core Global Agg Bond"}
}

# --- FUNZIONE SCARICAMENTO DATI REALI ---
@st.cache_data(ttl=3600)
def fetch_etf_data():
    data_list = []
    hist_dict = {}
    
    for symbol, info in ETF_CONFIG.items():
        try:
            ticker = yf.Ticker(info["ticker"])
            hist = ticker.history(period="1y")
            if hist.empty:
                continue
            
            # Prezzo attuale e variazione giornaliera
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # Calcolo RSI (14)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            rsi_val = rsi_series.iloc[-1]
            if np.isnan(rsi_val):
                rsi_val = 50.0

            # Bande di Bollinger (20, 2)
            sma_20 = hist['Close'].rolling(window=20).mean()
            std_20 = hist['Close'].rolling(window=20).std()
            upper_band = sma_20 + (std_20 * 2)
            lower_band = sma_20 - (std_20 * 2)
            
            cur_upper = upper_band.iloc[-1]
            cur_lower = lower_band.iloc[-1]
            
            if current_price >= cur_upper:
                bollinger_val = "Upper"
            elif current_price <= cur_lower:
                bollinger_val = "Lower"
            else:
                bollinger_val = "Mid"

            # Drawdown da massimo a 1 anno
            rolling_max = hist['Close'].cummax()
            drawdown_series = (hist['Close'] - rolling_max) / rolling_max * 100
            drawdown_val = drawdown_series.iloc[-1]

            # MACD
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            
            if macd_line.iloc[-1] > signal_line.iloc[-1]:
                macd_status = "Bullish"
            elif macd_line.iloc[-1] < signal_line.iloc[-1]:
                macd_status = "Bearish"
            else:
                macd_status = "Neutral"

            # Segnale PAC
            if rsi_val < 45 or bollinger_val == "Lower" or drawdown_val < -10.0:
                signal = "Strong Buy"
            elif rsi_val > 60 or bollinger_val == "Upper":
                signal = "Wait"
            else:
                signal = "Accumulate"

            data_list.append({
                "ETF": symbol,
                "Name": info["name"],
                "Price": f"€{current_price:.2f}",
                "Price_Raw": current_price,
                "Change": f"{'+' if change_pct >= '' else ''}{change_pct:.2f}%",
                "RSI": f"{rsi_val:.1f}",
                "Bollinger": bollinger_val,
                "Drawdown": f"{drawdown_val:.1f}%",
                "DD_Val": drawdown_val,
                "MACD": macd_status,
                "Signal": signal
            })
            
            hist_dict[symbol] = hist
        except Exception as e:
            st.error(f"Errore nel recupero dati per {symbol}: {e}")
            
    return pd.DataFrame(data_list), hist_dict

df, hist_dict = fetch_etf_data()

if df.empty:
    st.error("Impossibile caricare i dati da yfinance. Controlla la connessione di rete.")
    st.stop()

# --- LOGICA DI SELEZIONE DELL'UNICA AZIONE PIÙ CONVENIENTE ---
df = df.sort_values(by="DD_Val", ascending=True).reset_index(drop=True)
best_etf_idx = 0
best_etf_signal = df.loc[best_etf_idx, "Signal"]

extra_invested = savings_cash if best_etf_signal == "Strong Buy" else 0
total_investable = monthly_budget + extra_invested

df["Allocazione_Euro"] = 0.0
df.loc[best_etf_idx, "Allocazione_Euro"] = total_investable

# --- FUNZIONE GENERAZIONE GRAFICI REALI ---
def generate_etf_charts(etf_symbol):
    hist = hist_dict.get(etf_symbol)
    if hist is None or hist.empty:
        return go.Figure(), go.Figure()
        
    dates = hist.index
    price_trend = hist['Close']
    sma_20 = price_trend.rolling(20).mean()
    sma_200 = price_trend.rolling(200).mean()
    std_20 = price_trend.rolling(20).std()
    bb_upper = sma_20 + (std_20 * 2)
    bb_lower = sma_20 - (std_20 * 2)

    # Prezzo & Bollinger
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

    # MACD Reale
    exp1 = price_trend.ewm(span=12, adjust=False).mean()
    exp2 = price_trend.ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
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
    fig_p, fig_m = generate_etf_charts(etf_info['ETF'])
    
    st.subheader("Andamento Prezzo & Bande di Bollinger")
    st.plotly_chart(fig_p, use_container_width=True)
    
    st.subheader("Indicatore MACD")
    st.plotly_chart(fig_m, use_container_width=True)

# --- TITOLO E FILTRI ---
col_title, col_filter = st.columns([2, 1])

with col_title:
    st.title("Developed Markets PAC Screener")
    st.write("Acquisto mensile concentrato **sull'ETF più conveniente** basato su dati reali di mercato. Clicca sull'ETF per aprire i grafici.")

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
    
    with c1:
        if st.button(f"🔍 {row['ETF']}", key=f"btn_{row['ETF']}", help=f"Apri grafico e dettagli di {row['Name']}"):
            show_etf_popup(row)

    c2.markdown(f"**{row['Price']}**")
    
    change_color = "#00e676" if "+" in row["Change"] else "#ff5252"
    c3.markdown(f"<span style='color: {change_color}; font-weight:600;'>{row['Change']}</span>", unsafe_allow_html=True)
    
    rsi_val = float(row['RSI'])
    rsi_class = "badge-green" if rsi_val <= 45 else ("badge-yellow" if rsi_val <= 60 else "badge-red")
    c4.markdown(f"<span class='badge {rsi_class}'>● {row['RSI']}</span>", unsafe_allow_html=True)
    
    boll_class = "badge-green" if row['Terminal' if False else 'Bollinger'] == "Lower" else ("badge-yellow" if row['Bollinger'] == "Mid" else "badge-red")
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
fig_p_def, fig_m_def = generate_etf_charts(selected_etf_name)
st.plotly_chart(fig_p_def, use_container_width=True)
st.plotly_chart(fig_m_def, use_container_width=True)

st.markdown(f"""
<div class="insight-box">
    📊 <b>Strategia di Concentrazione Mensile:</b> 
    Questo mese tutto il budget (€{total_investable:.2f}) viene allocato al 100% su <b>{selected_etf_name}</b> in quanto risulta l'asset più conveniente in base ai dati di mercato in tempo reale.
</div>
""", unsafe_allow_html=True)

st.caption("Source: Yahoo Finance Live Data · Developed Markets PAC Screener | QuantEdge v4.0")