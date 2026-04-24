import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Terminal Pro Finnhub", layout="wide")

# CONFIGURA TU API KEY AQUÍ O EN SECRETS
# Si usas Streamlit Cloud, ponlo en Secrets y usa: API_KEY = st.secrets["FINNHUB_API_KEY"]
API_KEY = "d7lpfrpr01qk7lvttq4gd7lpfrpr01qk7lvttq50" 

# --- FUNCIONES DE LLAMADA A API (CON CUIDADO DE QUOTA) ---

@st.cache_data(ttl=3600)
def fetch_finnhub(endpoint, params={}):
    """Función base para peticiones a Finnhub"""
    base_url = "https://finnhub.io/api/v1/"
    params['token'] = API_KEY
    try:
        response = requests.get(base_url + endpoint, params=params)
        return response.json()
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def cargar_datos_totales():
    tickers = {
        "Nvidia": "NVDA", "Apple": "AAPL", "Microsoft": "MSFT", 
        "Google": "GOOGL", "Amazon": "AMZN", "Meta": "META",
        "Tesla": "TSLA", "Broadcom": "AVGO", "TSMC": "TSM", "Alibaba": "BABA"
    }
    data = []
    
    for nombre, symbol in tickers.items():
        # Datos de precio (Quote)
        quote = fetch_finnhub("quote", {"symbol": symbol})
        # Datos de perfil (Metric)
        metrics = fetch_finnhub("stock/metric", {"symbol": symbol, "metric": "all"})
        
        if quote and metrics:
            m = metrics.get('metric', {})
            data.append({
                "Empresa": nombre,
                "Ticker": symbol,
                "Market Cap": m.get('marketCapitalization', 0) * 1_000_000, # Finnhub lo da en millones
                "Ingresos": m.get('revenueTTM', 0) * 1_000_000,
                "P/E Ratio": m.get('peExclExtraTTM', 0),
                "Empleados": 0, # Finnhub gratuito no siempre da empleados en metric/all
                "Precio": quote.get('c', 0),
                "EBITDA": m.get('ebitdaTTM', 0) * 1_000_000,
                "Margen Neto (%)": m.get('netProfitMarginTTM', 0)
            })
        # Pequeña pausa para no quemar la API (Rate limit de Finnhub: 60 llamadas/min)
        time.sleep(0.1) 
    
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def cargar_historico_finnhub(symbol, dias):
    """Obtiene velas (candles) diarias"""
    end = int(time.time())
    start = end - (dias * 24 * 60 * 60)
    
    res = fetch_finnhub("stock/candle", {
        "symbol": symbol,
        "resolution": "D",
        "from": start,
        "to": end
    })
    
    if res and res.get('s') == 'ok':
        df = pd.DataFrame({
            "Fecha": pd.to_datetime(res['t'], unit='s'),
            "Precio": res['c']
        })
        return df.set_index("Fecha")
    return pd.DataFrame()

# --- INTERFAZ ---
st.title("🏛️ Terminal Tech Intelligence (Powered by Finnhub)")

if API_KEY == "TU_API_KEY_AQUI":
    st.error("Por favor, introduce tu API KEY de Finnhub en el código.")
else:
    df = cargar_datos_totales()

    if not df.empty:
        # 1. MONITOR DE MERCADO
        st.subheader("📋 Monitor de Mercado")
        st.dataframe(
            df,
            column_config={
                "Market Cap": st.column_config.NumberColumn("Market Cap ($)", format="%d"),
                "Ingresos": st.column_config.NumberColumn("Ingresos ($)", format="%d"),
                "P/E Ratio": st.column_config.NumberColumn("P/E Ratio", format="%.2f"),
                "Precio": st.column_config.NumberColumn("Precio ($)", format="%.2f"),
                "Margen Neto (%)": st.column_config.ProgressColumn("Margen Neto", min_value=0, max_value=60, format="%.1f%%"),
            },
            hide_index=True,
            use_container_width=True
        )

        st.divider()

        # 2. COMPARADOR TEMPORAL
        col_ctrl, col_viz = st.columns([1, 3])

        with col_ctrl:
            st.markdown("### 🛠️ Configuración")
            empresas_selec = st.multiselect("Empresas:", df['Empresa'].unique(), default=["Nvidia", "Apple"])
            dias_atras = st.slider("Días atrás:", 30, 365, 180) # Finnhub free tiene límites de histórico
            
        with col_viz:
            if empresas_selec:
                combined_h = pd.DataFrame()
                for emp in empresas_selec:
                    sym = df[df['Empresa'] == emp]['Ticker'].values[0]
                    h = cargar_historico_finnhub(sym, dias_atras)
                    if not h.empty:
                        combined_h[emp] = h['Precio']
                
                if not combined_h.empty:
                    fig = px.line(combined_h, title="Evolución de Precio (Datos Reales API)", template="plotly_dark")
                    fig.update_layout(hovermode="x unified", yaxis_title="Precio USD")
                    st.plotly_chart(fig, use_container_width=True)

        # 3. GLOSARIO
        st.divider()
        st.markdown("### 📖 Glosario Técnico")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Market Cap:** Valoración total basada en el último precio de cierre.")
            st.markdown("**Ingresos:** Facturación total (TTM - Trailing Twelve Months).")
        with c2:
            st.markdown("**P/E Ratio:** Ratio Precio/Beneficio (TTM).")
            st.markdown("**EBITDA:** Beneficio operativo antes de depreciaciones.")
        with c3:
            st.markdown("**Margen Neto:** Porcentaje de beneficio sobre ventas totales.")
            st.markdown("**Finnhub API:** Datos profesionales directos (JSON), evitando bloqueos de scraping.")

    else:
        st.error("No se pudieron cargar los datos. Revisa tu API KEY.")

st.caption(f"Terminal v5.0 | Fuente: Finnhub.io | {datetime.now().strftime('%H:%M')}")
