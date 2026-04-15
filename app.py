import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Terminal Pro Tech", layout="wide")

# --- FUNCIONES DE CARGA ---
@st.cache_data(ttl=3600)
def cargar_datos_pro():
    tickers = {
        "Nvidia": "NVDA", "Apple": "AAPL", "Microsoft": "MSFT", 
        "Google": "GOOGL", "Amazon": "AMZN", "Meta": "META",
        "Tesla": "TSLA", "Broadcom": "AVGO", "TSMC": "TSM", "Alibaba": "BABA"
    }
    data = []
    for nombre, t in tickers.items():
        try:
            tk = yf.Ticker(t)
            inf = tk.info
            data.append({
                "Empresa": nombre,
                "Ticker": t,
                "Market Cap": inf.get('marketCap', 0),
                "Ingresos": inf.get('totalRevenue', 0),
                "P/E Ratio": inf.get('trailingPE', 0),
                "Empleados": inf.get('fullTimeEmployees', 0),
                "Precio": inf.get('currentPrice', 0),
                "EBITDA": inf.get('ebitda', 0)
            })
        except: continue
    return pd.DataFrame(data)

@st.cache_data(ttl=1800)
def cargar_historico_limpio(tickers, fecha_inicio):
    df_h = yf.download(tickers, start=fecha_inicio)['Close']
    if isinstance(df_h, pd.Series): # Si solo es uno, convertir a DF
        df_h = df_h.to_frame()
    return df_h

# --- INTERFAZ ---
st.title("🚀 Terminal de Inteligencia Corporativa Tech")

df = cargar_datos_pro()

# --- 1. TABLA RESUMEN (ORDENABLE Y FORMATEADA) ---
st.subheader("📋 Monitor de Mercado (Datos Actuales)")
st.markdown("_Haz clic en las cabeceras para ordenar por valor real_")

# Usamos st.dataframe con configuración de columnas para mantener el orden numérico
st.dataframe(
    df,
    column_config={
        "Market Cap": st.column_config.NumberColumn("Market Cap ($)", format="%d", help="Valor total de mercado"),
        "Ingresos": st.column_config.NumberColumn("Ingresos ($)", format="%d"),
        "Empleados": st.column_config.NumberColumn("Empleados", format="%d"),
        "P/E Ratio": st.column_config.NumberColumn("P/E Ratio", format="%.2f"),
        "Precio": st.column_config.NumberColumn("Precio ($)", format="%.2f"),
        "EBITDA": st.column_config.NumberColumn("EBITDA ($)", format="%d"),
    },
    hide_index=True,
    use_container_width=True
)

st.divider()

# --- 2. GRÁFICO COMPARATIVO INTEGRADO ---
col_ctrl, col_viz = st.columns([1, 3])

with col_ctrl:
    st.markdown("### 🛠️ Comparador")
    empresas_selec = st.multiselect("Empresas:", df['Empresa'].unique(), default=["Nvidia", "Apple"])
    
    # Permitimos elegir CUALQUIER variable de la tabla para el gráfico
    var_map = {
        "Precio Histórico": "Precio",
        "Market Cap Actual": "Market Cap",
        "Ingresos": "Ingresos",
        "Ratio P/E": "P/E Ratio",
        "Empleados": "Empleados"
    }
    variable_a_ver = st.selectbox("Variable a comparar:", list(var_map.keys()))
    
    fecha_in = st.date_input("Desde:", datetime.now() - timedelta(days=365))

with col_viz:
    if variable_a_ver == "Precio Histórico":
        # Gráfico de líneas temporal
        tickers_sel = df[df['Empresa'].isin(empresas_selec)]['Ticker'].tolist()
        if tickers_sel:
            h_data = cargar_historico_limpio(tickers_sel, fecha_in)
            # Mapear columnas de Ticker a Nombre de Empresa para la leyenda
            nombres_map = dict(zip(df['Ticker'], df['Empresa']))
            h_data.columns = [nombres_map.get(c, c) for c in h_data.columns]
            
            fig = px.line(h_data, title="Evolución de Precio ($)", template="plotly_dark")
            fig.update_layout(hovermode="x unified", yaxis_title="Precio USD")
            st.plotly_chart(fig, use_container_width=True)
    else:
        # Gráfico de barras para variables estáticas (Ingresos, MC, etc.)
        df_sub = df[df['Empresa'].isin(empresas_selec)]
        fig_bar = px.bar(
            df_sub, x="Empresa", y=var_map[variable_a_ver], 
            color="Empresa", title=f"Comparativa de {variable_a_ver}",
            template="plotly_dark", text_auto='.2s'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --- 3. GLOSARIO CONCISO ---
st.divider()
st.markdown("### 📖 Glosario Técnico")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Market Cap:** Valor total de la empresa en bolsa.")
    st.markdown("**Ingresos:** Facturación total bruta (Revenue).")
with c2:
    st.markdown("**P/E Ratio:** Relación precio/beneficio (valoración).")
    st.markdown("**EBITDA:** Beneficio operativo antes de impuestos/amortización.")
with c3:
    st.markdown("**Volumen:** Cantidad de acciones negociadas en el mercado.")
    st.markdown("**Empleados:** Fuerza laboral total declarada.")

st.caption(f"Actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Notación: Puntos para miles habilitados en tabla.")
