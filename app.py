import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import yfinance as yf
from datetime import datetime, timedelta
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Terminal Inteligencia v5.5", layout="wide")

# SUSTITUYE POR TU API KEY DE FINNHUB
API_KEY = "d7lpfrpr01qk7lvttq4gd7lpfrpr01qk7lvttq50" 

# --- METADATA MAESTRA (Respaldo para datos que quedan vacíos) ---
# Estos datos aseguran que la tabla NUNCA tenga "N/D" en variables estructurales
DATA_MAESTRA = {
    "NVDA": {"empleados": 29600, "sector": "Semiconductores"},
    "AAPL": {"empleados": 161000, "sector": "Consumo Electrónico"},
    "MSFT": {"empleados": 221000, "sector": "Software/Cloud"},
    "GOOGL": {"empleados": 182000, "sector": "Servicios Digitales"},
    "AMZN": {"empleados": 1525000, "sector": "E-commerce/Cloud"},
    "META": {"empleados": 67000, "sector": "Redes Sociales"},
    "TSLA": {"empleados": 140000, "sector": "Automotriz/Energía"},
    "AVGO": {"empleados": 20000, "sector": "Semiconductores"},
    "TSM": {"empleados": 76000, "sector": "Fundición Chips"},
    "BABA": {"empleados": 235000, "sector": "E-commerce Asia"}
}

# --- FUNCIONES DE API ---

@st.cache_data(ttl=3600)
def fetch_finnhub(endpoint, params={}):
    base_url = "https://finnhub.io/api/v1/"
    params['token'] = API_KEY
    try:
        r = requests.get(base_url + endpoint, params=params, timeout=5)
        return r.json()
    except:
        return None

@st.cache_data(ttl=86400) # Caché de 24 horas para no saturar
def cargar_datos_hibridos():
    tickers = {
        "Nvidia": "NVDA", "Apple": "AAPL", "Microsoft": "MSFT", 
        "Google": "GOOGL", "Amazon": "AMZN", "Meta": "META",
        "Tesla": "TSLA", "Broadcom": "AVGO", "TSMC": "TSM", "Alibaba": "BABA"
    }
    
    final_data = []
    
    for nombre, symbol in tickers.items():
        # 1. Intentar Finnhub para métricas financieras
        metrics = fetch_finnhub("stock/metric", {"symbol": symbol, "metric": "all"})
        quote = fetch_finnhub("quote", {"symbol": symbol})
        
        m = metrics.get('metric', {}) if metrics else {}
        
        # 2. Combinar con DATA_MAESTRA si faltan datos (como empleados)
        empleados = DATA_MAESTRA.get(symbol, {}).get("empleados", 0)
        
        final_data.append({
            "Empresa": nombre,
            "Ticker": symbol,
            "Market Cap": m.get('marketCapitalization', 0) * 1_000_000,
            "Ingresos": m.get('revenueTTM', 0) * 1_000_000,
            "P/E Ratio": m.get('peExclExtraTTM', 0) or m.get('peBasicExclExtraTTM', 0),
            "Empleados": empleados,
            "Precio": quote.get('c', 0) if quote else 0,
            "EBITDA": m.get('ebitdaTTM', 0) * 1_000_000,
            "Margen Neto (%)": m.get('netProfitMarginTTM', 0)
        })
        time.sleep(0.1) # Respetar rate limit
        
    return pd.DataFrame(final_data)

@st.cache_data(ttl=3600)
def cargar_historia_integral(symbol, variable, dias):
    """
    Si la variable es 'Precio', usamos Finnhub (robusto).
    Si es 'Ingresos/EBITDA', usamos yfinance con un manejo de error agresivo.
    """
    if variable == "Precio":
        end = int(time.time())
        start = end - (dias * 24 * 60 * 60)
        res = fetch_finnhub("stock/candle", {"symbol": symbol, "resolution": "D", "from": start, "to": end})
        if res and res.get('s') == 'ok':
            return pd.Series(res['c'], index=pd.to_datetime(res['t'], unit='s'))
    else:
        # Intentamos yfinance para fundamentales con protección
        try:
            tk = yf.Ticker(symbol)
            if variable == "Ingresos":
                return tk.quarterly_financials.loc['Total Revenue']
            elif variable == "EBITDA":
                return tk.quarterly_financials.loc['EBITDA']
        except:
            return pd.Series()
    return pd.Series()

# --- INTERFAZ ---
st.title("🛰️ Terminal Híbrida de Inteligencia Corporativa")

if API_KEY == "TU_API_KEY_AQUI":
    st.warning("⚠️ Inserta tu API KEY de Finnhub para activar los datos en vivo.")
    st.stop()

df = cargar_datos_hibridos()

# 1. MONITOR DE MERCADO (Con puntos de miles y orden numérico)
st.subheader("📋 Monitor Global de Activos")
st.dataframe(
    df,
    column_config={
        "Market Cap": st.column_config.NumberColumn("Market Cap ($)", format="%d"),
        "Ingresos": st.column_config.NumberColumn("Ingresos ($)", format="%d"),
        "P/E Ratio": st.column_config.NumberColumn("P/E Ratio", format="%.2f"),
        "Empleados": st.column_config.NumberColumn("Empleados", format="%d"),
        "Precio": st.column_config.NumberColumn("Precio ($)", format="%.2f"),
        "Margen Neto (%)": st.column_config.ProgressColumn("Margen Neto", min_value=0, max_value=60, format="%.1f%%"),
    },
    hide_index=True,
    use_container_width=True
)

st.divider()

# 2. COMPARADOR TEMPORAL TOTAL
col_ctrl, col_viz = st.columns([1, 3])

with col_ctrl:
    st.markdown("### 🛠️ Configuración")
    empresas_selec = st.multiselect("Empresas:", df['Empresa'].unique(), default=["Nvidia", "Microsoft"])
    var_grafico = st.selectbox("Variable Temporal:", ["Precio", "Ingresos", "EBITDA"])
    dias_atras = st.slider("Horizonte temporal (días):", 90, 1000, 365)

with col_viz:
    if empresas_selec:
        combined_h = pd.DataFrame()
        for emp in empresas_selec:
            sym = df[df['Empresa'] == emp]['Ticker'].values[0]
            h = cargar_historia_integral(sym, var_grafico, dias_atras)
            if not h.empty:
                combined_h[emp] = h
        
        if not combined_h.empty:
            # Si son fundamentales (trimestrales), usamos puntos. Si es precio, línea.
            mode = 'lines+markers' if var_grafico in ["Ingresos", "EBITDA"] else 'lines'
            fig = px.line(combined_h, title=f"Evolución: {var_grafico}", template="plotly_dark")
            fig.update_traces(mode=mode)
            fig.update_layout(hovermode="x unified", yaxis_title="Valor USD")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos históricos suficientes para esta variable. Yahoo Finance podría estar limitando el acceso.")

# 3. GLOSARIO
st.divider()
st.markdown("### 📖 Glosario y Fuentes")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Fuente Principal:** Finnhub API (Datos JSON directos).")
    st.markdown("**Respaldo Estructural:** Base de datos interna para Empleados/Sectores.")
with c2:
    st.markdown("**Market Cap / Ingresos:** Datos TTM (Trailing Twelve Months).")
    st.markdown("**Margen Neto:** Capacidad de conversión de ingresos en beneficio neto.")
with c3:
    st.markdown("**Ordenación:** La tabla permite ordenar por valor real haciendo clic en la cabecera.")
    st.markdown("**Sincronización:** Datos actualizados cada 60 minutos.")
