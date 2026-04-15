import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Terminal Inteligencia Corporativa", layout="wide", page_icon="📈")

# --- FUNCIONES DE FORMATEO EUROPEO ---
def format_point_thousands(n):
    """Convierte 1000000 en 1.000.000"""
    if pd.isna(n) or n == 0: return "N/D"
    return f"{int(n):,}".replace(",", ".")

def format_currency_eu(n):
    """Convierte números grandes en formato moneda europea legible"""
    if pd.isna(n) or n == 0: return "N/D"
    return f"{n:,.2f} $".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CARGA DE DATOS ---
@st.cache_data(ttl=3600)
def cargar_datos_completos():
    tickers = {
        "Nvidia": "NVDA", "Apple": "AAPL", "Microsoft": "MSFT", 
        "Alphabet": "GOOGL", "Amazon": "AMZN", "Meta": "META",
        "Tesla": "TSLA", "Broadcom": "AVGO", "TSMC": "TSM", 
        "Alibaba": "BABA", "Tencent": "TCEHY", "ASML": "ASML"
    }
    
    data_list = []
    for nombre, t in tickers.items():
        try:
            tk = yf.Ticker(t)
            inf = tk.info
            data_list.append({
                "Empresa": nombre,
                "Ticker": t,
                "Market Cap": inf.get('marketCap', 0),
                "Ingresos": inf.get('totalRevenue', 0),
                "EBITDA": inf.get('ebitda', 0),
                "Empleados": inf.get('fullTimeEmployees', 0),
                "P/E Ratio": inf.get('trailingPE', 0),
                "Margen Neto (%)": inf.get('profitMargins', 0) * 100,
                "Ecosistema": "USA" if t not in ["BABA", "TCEHY", "TSM", "ASML"] else "Global"
            })
        except: continue
    return pd.DataFrame(data_list)

# --- INTERFAZ ---
st.title("🏛️ Terminal de Análisis Tecnológico")
df_raw = cargar_datos_completos()

# --- SIDEBAR: FILTROS TEMPORALES Y SELECCIÓN ---
with st.sidebar:
    st.header("📅 Filtros de Tiempo")
    fecha_inicio = st.date_input("Ver datos desde:", datetime.now() - timedelta(days=365))
    st.divider()
    st.header("📊 Configuración Gráfica")
    empresas_selec = st.multiselect("Comparar Empresas:", df_raw['Empresa'].unique(), default=["Nvidia", "Microsoft"])
    variable_grafico = st.selectbox("Variable a graficar:", ["Precio (Cierre)", "Volumen", "Market Cap (Histórico Est.)"])

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📋 Tabla de Datos", "📉 Gráfico Comparativo", "📖 Glosario"])

with tab1:
    st.subheader("Estado Actual de las Compañías")
    
    # Preparamos una copia formateada para la tabla sin tocar los números para el gráfico
    df_tabla = df_raw.copy()
    df_tabla['Market Cap'] = df_tabla['Market Cap'].apply(format_point_thousands)
    df_tabla['Ingresos'] = df_tabla['Ingresos'].apply(format_point_thousands)
    df_tabla['EBITDA'] = df_tabla['EBITDA'].apply(format_point_thousands)
    df_tabla['Empleados'] = df_tabla['Empleados'].apply(format_point_thousands)
    df_tabla['P/E Ratio'] = df_tabla['P/E Ratio'].apply(lambda x: f"{x:,.2f}".replace(".", ","))

    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    st.caption("Nota: Haz clic en el nombre de la columna para ordenar. Los valores de moneda están en USD.")

with tab2:
    if not empresas_selec:
        st.warning("Selecciona al menos una empresa en el panel izquierdo.")
    else:
        st.subheader(f"Comparativa: {variable_grafico}")
        
        # Diccionario para mapear la variable seleccionada con el dato de Yahoo
        mapa_vars = {"Precio (Cierre)": "Close", "Volumen": "Volume", "Market Cap (Histórico Est.)": "Close"}
        
        datos_comparativos = pd.DataFrame()
        
        for emp in empresas_selec:
            t = df_raw[df_raw['Empresa'] == emp]['Ticker'].values[0]
            h = yf.download(t, start=fecha_inicio)
            
            if not h.empty:
                # Aplanar multi-index si existe
                if isinstance(h.columns, pd.MultiIndex):
                    h.columns = h.columns.get_level_values(0)
                
                serie = h[mapa_vars[variable_grafico]]
                
                # Si es Market Cap estimado, multiplicamos precio por el market cap actual/precio actual
                if variable_grafico == "Market Cap (Histórico Est.)":
                    m_cap_actual = df_raw[df_raw['Empresa'] == emp]['Market Cap'].values[0]
                    precio_actual = serie.iloc[-1]
                    serie = serie * (m_cap_actual / precio_actual)
                
                datos_comparativos[emp] = serie

        if not datos_comparativos.empty:
            fig = px.line(datos_comparativos, template="plotly_dark", 
                          labels={"value": variable_grafico, "Date": "Fecha"})
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No se pudieron recuperar datos históricos para la comparación.")

with tab3:
    st.markdown("""
    ### Glosario de Términos
    * **Market Cap:** Valor total de mercado (Acciones x Precio).
    * **P/E Ratio:** Veces que el beneficio está contenido en el precio.
    * **EBITDA:** Capacidad operativa de generar caja.
    * **Notación:** Se utiliza el punto (.) para separar miles y la coma (,) para decimales para facilitar la lectura europea.
    """)

st.markdown("---")
st.caption(f"Terminal v3.1 | Fuente: Yahoo Finance | Última consulta: {datetime.now().strftime('%H:%M:%S')}")
