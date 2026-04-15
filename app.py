import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Tech Intelligence Terminal", 
    layout="wide", 
    page_icon="📊"
)

# Estilos visuales
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE FORMATEO ---

def format_eu(value):
    """Formatea números con puntos para miles (Estilo Europeo)"""
    if pd.isna(value) or value == 0: return "N/D"
    return f"{value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CARGA DE DATOS ---

@st.cache_data(ttl=3600)
def cargar_datos_terminal():
    # Tickers: Incluimos Gigantes USA, Asia y estimaciones manuales para privadas
    tickers = {
        "Nvidia": "NVDA", "Apple": "AAPL", "Microsoft": "MSFT", 
        "Alphabet (Google)": "GOOGL", "Amazon": "AMZN", "Meta": "META",
        "Tesla": "TSLA", "Broadcom": "AVGO", "TSMC": "TSM", 
        "Alibaba": "BABA", "Tencent": "TCEHY", "ASML": "ASML"
    }
    
    lista_final = []
    for nombre, t in tickers.items():
        try:
            tk = yf.Ticker(t)
            inf = tk.info
            lista_final.append({
                "Empresa": nombre,
                "Ticker": t,
                "Market Cap": inf.get('marketCap', 0),
                "Ingresos (Anual)": inf.get('totalRevenue', 0),
                "EBITDA": inf.get('ebitda', 0),
                "Empleados": inf.get('fullTimeEmployees', 0),
                "P/E Ratio": inf.get('trailingPE', 0),
                "Margen Neto (%)": inf.get('profitMargins', 0) * 100,
                "Ecosistema": "USA" if t not in ["BABA", "TCEHY", "TSM", "ASML"] else "Global/Asia"
            })
        except: continue
    
    # Añadimos Privadas (Estimaciones manuales de mercado)
    privadas = [
        {"Empresa": "Anthropic", "Ticker": "Privada", "Market Cap": 18000000000, "Ingresos (Anual)": 800000000, 
         "EBITDA": 0, "Empleados": 500, "P/E Ratio": 0, "Margen Neto (%)": 0, "Ecosistema": "IA Pura"},
        {"Empresa": "xAI", "Ticker": "Privada", "Market Cap": 24000000000, "Ingresos (Anual)": 100000000, 
         "EBITDA": 0, "Empleados": 200, "P/E Ratio": 0, "Margen Neto (%)": 0, "Ecosistema": "IA Pura"}
    ]
    
    df = pd.DataFrame(lista_final + privadas)
    return df

@st.cache_data(ttl=1800)
def cargar_historico_seguro(ticker, period="2y"):
    try:
        data = yf.download(ticker, period=period)
        if data.empty: return pd.DataFrame()
        # Limpieza de Multi-index de yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except:
        return pd.DataFrame()

# --- INTERFAZ PRINCIPAL ---

st.title("🖥️ Terminal de Inteligencia: Big Tech & AI")
st.caption(f"Datos actualizados: {datetime.now().strftime('%d/%m/%Y')} | Fuente: Yahoo Finance & World Bank")

df_main = cargar_datos_terminal()

# Creamos las pestañas que pediste
tab_dashboard, tab_comparador, tab_ayuda = st.tabs([
    "📈 Dashboard Principal", 
    "📊 Comparador de Variables", 
    "❓ Ayuda y Glosario"
])

# --- PESTAÑA 1: DASHBOARD PRINCIPAL ---
with tab_dashboard:
    st.subheader("Tabla de Mando Competitiva")
    st.markdown("_Haz clic en cualquier encabezado para ordenar las filas_")
    
    # Configuración de columnas para que la tabla sea profesional
    st.dataframe(
        df_main,
        column_config={
            "Market Cap": st.column_config.NumberColumn("Market Cap ($)", format="%.2e"),
            "Ingresos (Anual)": st.column_config.NumberColumn("Ingresos ($)", format="%.2e"),
            "Empleados": st.column_config.NumberColumn("Empleados", format="%d"),
            "P/E Ratio": st.column_config.NumberColumn("P/E Ratio", format="%.2f"),
            "Margen Neto (%)": st.column_config.ProgressColumn("Margen Neto", min_value=0, max_value=60, format="%.1f%%"),
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()
    
    # Análisis temporal
    col_sel, col_graph = st.columns([1, 3])
    with col_sel:
        empresa_fav = st.selectbox("Analizar Histórico:", df_main[df_main['Ticker'] != "Privada"]['Empresa'])
        rango = st.select_slider("Rango:", options=["1mo", "6mo", "1y", "2y", "5y", "max"], value="1y")
        ticker_fav = df_main[df_main['Empresa'] == empresa_fav]['Ticker'].values[0]
        
    with col_graph:
        datos_h = cargar_historico_seguro(ticker_fav, period=rango)
        if not datos_h.empty:
            fig = px.line(datos_h, y="Close", title=f"Evolución Precio: {empresa_fav} ({ticker_fav})", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

# --- PESTAÑA 2: COMPARADOR ---
with tab_comparador:
    st.subheader("Cruce de Variables Estratégicas")
    c1, c2, c3 = st.columns(3)
    eje_x = c1.selectbox("Eje X:", ["Empleados", "Ingresos (Anual)", "Market Cap"], index=0)
    eje_y = c2.selectbox("Eje Y:", ["Market Cap", "Ingresos (Anual)", "P/E Ratio"], index=0)
    eje_s = c3.selectbox("Tamaño Burbuja:", ["Market Cap", "Ingresos (Anual)", "EBITDA"], index=1)
    
    fig_bubble = px.scatter(
        df_main, x=eje_x, y=eje_y, size=eje_s, color="Ecosistema",
        hover_name="Empresa", log_x=True, log_y=True,
        template="plotly_dark", height=600
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

# --- PESTAÑA 3: AYUDA Y GLOSARIO ---
with tab_ayuda:
    st.header("📘 Glosario de Variables Técnicas")
    st.markdown("""
    Esta sección explica el significado financiero de los datos mostrados en la terminal:
    
    * **Market Cap (Capitalización de Mercado):** Es el valor total de todas las acciones de la empresa. Se calcula multiplicando el precio de una acción por el número total de acciones en circulación. Indica el "tamaño" que el mercado otorga a la compañía.
    * **Ingresos (Revenue):** La cantidad total de dinero que la empresa recibe por la venta de sus productos o servicios antes de descontar cualquier gasto.
    * **P/E Ratio (Price-to-Earnings):** Relación entre el precio de la acción y el beneficio por acción. Indica cuánto están dispuestos a pagar los inversores por cada dólar de beneficio. Un P/E alto puede significar que se espera mucho crecimiento futuro.
    * **EBITDA:** Beneficio antes de intereses, impuestos, depreciaciones y amortizaciones. Es un indicador de la rentabilidad operativa pura de la empresa.
    * **Margen Neto:** El porcentaje de ingresos que queda como beneficio real después de pagar absolutamente todos los gastos e impuestos.
    * **Ecosistema:** Clasificación geográfica o funcional (USA, Asia, o IA Pura para empresas no cotizadas).
    
    ---
    **Nota sobre Notación:**
    * **10^9:** Representado como 'Billions' en USA, equivale a **Mil Millones** en Europa.
    * **10^12:** Representado como 'Trillions' en USA, equivale a **Billones** en Europa.
    """)

st.divider()
st.caption(f"Terminal Corporativa v3.0 | Datos de mercado con retardo de 15 min | Fuente: Yahoo Finance API")
