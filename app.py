import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA (Estilo Profesional) ---
st.set_page_config(
    page_title="Terminal Tech Intelligence", 
    layout="wide", 
    page_icon="🖥️"
)

# Estilos CSS para tablas y bordes
st.markdown("""
    <style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
    .stTable { 
        font-family: 'Courier New', Courier, monospace; 
        font-size: 0.9rem;
    }
    .main_title { text-align: center; color: white; font-weight: bold;}
    .data-card {
        border: 1px solid #30363d; 
        border-radius: 10px; 
        padding: 15px;
        background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- UTILIDADES DE FORMATEO (Europeo) ---

def format_currency_euro(value, mode='B'):
    """Convierte valor crudo a string formateado europeo (€/B/T)"""
    if pd.isna(value) or value == 0:
        return "N/D"
    
    # Notación Americana vs Europea:
    # 1 Billion (US) = 1.000.000.000 = 1 Mil millones (EU)
    # 1 Trillion (US) = 1.000.000.000.000 = 1 Billón (EU)
    
    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000
    
    # Formateo con puntos de millar y $ al final
    if value >= trillion:
        return f"{value/trillion:,.2f} B$".replace(",", "X").replace(".", ",").replace("X", ".")
    elif value >= billion:
        return f"{value/billion:,.2f} mMl$".replace(",", "X").replace(".", ",").replace("X", ".") # Mil Millones
    elif value >= million:
        return f"{value/million:,.2f} M$".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        return f"{value:,.0f}$".replace(",", "X").replace(".", ",").replace("X", ".")

def format_number(value):
    """Formatea números crudos (empleados)"""
    if pd.isna(value) or value == 0:
        return "N/D"
    return f"{value:,.0f}".replace(",", ".")

# --- FUENTES DE DATOS (Caché Corta: Actualizado) ---

@st.cache_data(ttl=3600) # Se actualiza cada hora
def cargar_tech_datos_prof():
    tickers = {
        "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", 
        "Amazon": "AMZN", "Nvidia": "NVDA", "Meta": "META",
        "TSMC": "TSM", "Alibaba": "BABA", "Tencent": "TCEHY"
    }
    results = []
    for nombre, t in tickers.items():
        try:
            tk = yf.Ticker(t)
            inf = tk.info
            results.append({
                "Empresa": nombre,
                "Ticker": t,
                "Ecosistema": "USA" if t not in ["BABA", "TCEHY", "TSM"] else "Asia",
                "Market Cap": inf.get('marketCap', 0),
                "Ingresos": inf.get('totalRevenue', 0),
                "Beneficio": inf.get('ebitda', 0),
                "Empleados": inf.get('fullTimeEmployees', 0),
                "P/E Ratio": inf.get('trailingPE', 0),
                "Source_Date": datetime.now().strftime("%d/%m/%Y")
            })
        except: continue
        
    df = pd.DataFrame(results)
    return df, datetime.now().strftime("%d/%m/%Y %H:%M")

@st.cache_data(ttl=1800)
def cargar_historia_ticker(ticker, period="2y"):
    try:
        data = yf.download(ticker, period=period)
        return data
    except:
        return pd.DataFrame()

# --- LÓGICA DE LA APP ---

# TÍTULO CENTRAL (Como image_2.png)
st.markdown("<h1 class='main_title'>Tech Giants: Market & Fundamentals Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray'>Seguimiento regular de la evolución competitiva</p>", unsafe_allow_html=True)
st.divider()

# Cargamos datos base
df_prof, last_update = cargar_tech_datos_prof()

# --- SIDEBAR (Controles de Línea Temporal) ---
with st.sidebar:
    st.header("🎛️ Controles del Dashboard")
    st.divider()
    empresa_focus = st.selectbox("Selecciona Empresa Principal:", df_prof['Empresa'].unique(), index=4) # Nvidia index
    st.divider()
    periodo_hist = st.radio("Rango Temporal para Gráficos:", ["1M", "6M", "YTD", "1A", "5A", "Max"], index=3)
    mapa_periodo = {"1M":"1mo", "6M":"6mo", "YTD":"ytd", "1A":"1y", "5A":"5y", "Max":"max"}
    st.divider()
    st.caption(f"Actualización Total: {last_update}")
    st.caption(f"Fuente de datos: Yahoo Finance")

# --- MÓDULO 1: LA TABLA RESUMEN (Inspirada en las referencias) ---
st.subheader("📋 Resumen Competitivo Actual (Formato Europeo)")

# Preparamos los datos para visualización
df_display = df_prof.copy()
df_display['Market Cap (EU)'] = df_display['Market Cap'].apply(lambda x: format_currency_euro(x, 'B'))
df_display['Ingresos (EU)'] = df_display['Ingresos'].apply(lambda x: format_currency_euro(x, 'B'))
df_display['Beneficio (EU)'] = df_display['Beneficio'].apply(lambda x: format_currency_euro(x, 'B'))
df_display['Empleados (EU)'] = df_display['Empleados'].apply(format_number)
df_display['P/E Ratio'] = df_display['P/E Ratio'].apply(lambda x: f"{x:.1f}" if x > 0 else "N/D")

# Visualización limpia (st.write en lugar de st.dataframe)
# st.write(df_display[['Empresa', 'Ticker', 'Market Cap (EU)', 'Ingresos (EU)', 'Empleados (EU)', 'P/E Ratio']])
# O mejor, usar st.table para un formato más estático como el de las fotos:
st.table(df_display[['Empresa', 'Ticker', 'Market Cap (EU)', 'Ingresos (EU)', 'Empleados (EU)', 'P/E Ratio']].sort_values("Market Cap (EU)", ascending=False))

# --- MÓDULO 2: LÍNEA TEMPORAL DE EVOLUCIÓN (Jugar con variables) ---
st.divider()
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"### 📈 Análisis de: {empresa_focus}")
    st.markdown(f"_Período seleccionado: {periodo_hist}_")
    
    ticker_focus = df_prof[df_prof['Empresa'] == empresa_focus]['Ticker'].values[0]
    hist_data = cargar_historia_ticker(ticker_focus, period=mapa_periodo[periodo_hist])
    
    if not hist_data.empty:
        ultimo_cierre = hist_data['Close'].iloc[-1].item()
        cierre_ayer = hist_data['Close'].iloc[-2].item()
        cambio = (ultimo_cierre - cierre_ayer) / cierre_ayer
        st.metric(f"Último Cierre (${ticker_focus})", f"{ultimo_cierre:.2f}$", f"{cambio*100:.2f}%")
        
        fig_line = px.line(hist_data, y="Close", template="plotly_dark", title=f"Precio de {ticker_focus}")
        st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.subheader("🔬 Comparativa de Variables Propias")
    # Este módulo permite elegir qué variables cruzar en una gráfica de burbujas
    st.markdown("<p style='color:gray'>Juega con los ejes para ver correlaciones.</p>", unsafe_allow_html=True)
    
    col_x = st.selectbox("Eje X:", ["Empleados", "Ingresos", "Market Cap"])
    col_y = st.selectbox("Eje Y:", ["Ingresos", "Market Cap", "P/E Ratio"])
    col_size = st.selectbox("Tamaño:", ["Market Cap", "Ingresos", "Empleados"])
    
    fig_bubble = px.scatter(df_prof, x=col_x, y=col_y, size=col_size, color="Empresa",
                             hover_name="Empresa", template="plotly_dark", title=f"{col_y} vs {col_x}")
    fig_bubble.update_layout(log_x=True, log_y=True) # Escalas logs para ver los datos mejor
    st.plotly_chart(fig_bubble, use_container_width=True)

# --- PIE DE PÁGINA PROFESIONAL ---
st.divider()
st.caption(f"©️ Terminal de Inteligencia Corporativa - Datos Estructurales (Market Cap, Ingresos, Empleados) de Yahoo Finance. Última actualización sincrónica: {last_update}.")
st.caption(f"Nota de notación: Se utiliza notación europea. mMl$ = Mil Millones de Dólares (10^9). B$ = Billones de Dólares (10^12).")
