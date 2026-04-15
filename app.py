import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Terminal Pro Tech v4.0", layout="wide")

# --- FUNCIONES DE CARGA ---
@st.cache_data(ttl=3600)
def cargar_datos_completos():
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
                "EBITDA": inf.get('ebitda', 0),
                "Margen Neto (%)": inf.get('profitMargins', 0) * 100
            })
        except: continue
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def cargar_historico_variable(tickers_dict, variable, fecha_inicio):
    """Obtiene histórico para cualquier variable disponible"""
    df_combined = pd.DataFrame()
    
    for nombre, t in tickers_dict.items():
        tk = yf.Ticker(t)
        
        if variable == "Precio":
            h = tk.history(start=fecha_inicio)['Close']
        elif variable == "Market Cap":
            # Estimación: Precio Histórico * Acciones actuales
            h = tk.history(start=fecha_inicio)['Close'] * tk.info.get('sharesOutstanding', 1)
        else:
            # Para Ingresos/EBITDA usamos datos trimestrales (puntos en el tiempo)
            fin = tk.quarterly_financials.T
            if variable in fin.columns:
                h = fin[variable]
            else:
                continue
                
        h.name = nombre
        df_combined = pd.concat([df_combined, h], axis=1)
    
    return df_combined.sort_index()

# --- INTERFAZ ---
st.title("🏛️ Terminal de Inteligencia Corporativa")

df = cargar_datos_completos()

# --- 1. TABLA MONITOR (CON PUNTOS Y ORDEN CORRECTO) ---
st.subheader("📋 Monitor de Mercado")
st.dataframe(
    df,
    column_config={
        "Market Cap": st.column_config.NumberColumn("Market Cap ($)", format="%d"),
        "Ingresos": st.column_config.NumberColumn("Ingresos ($)", format="%d"),
        "Empleados": st.column_config.NumberColumn("Empleados", format="%d"),
        "P/E Ratio": st.column_config.NumberColumn("P/E Ratio", format="%.2f"),
        "Precio": st.column_config.NumberColumn("Precio ($)", format="%.2f"),
        "Margen Neto (%)": st.column_config.ProgressColumn("Margen Neto", min_value=0, max_value=60, format="%.1f%%"),
    },
    hide_index=True,
    use_container_width=True
)

st.divider()

# --- 2. COMPARADOR TEMPORAL TOTAL ---
col_ctrl, col_viz = st.columns([1, 3])

with col_ctrl:
    st.markdown("### 🛠️ Configuración")
    empresas_selec = st.multiselect("Empresas:", df['Empresa'].unique(), default=["Nvidia", "Apple", "Microsoft"])
    
    # Mapeo de variables para el histórico
    opciones_var = {
        "Precio": "Precio",
        "Market Cap": "Market Cap",
        "Ingresos": "Total Revenue",
        "EBITDA": "EBITDA"
    }
    var_sel = st.selectbox("Variable Temporal:", list(opciones_var.keys()))
    
    dias = st.slider("Días atrás:", 30, 1825, 365)
    f_inicio = datetime.now() - timedelta(days=dias)

with col_viz:
    if empresas_selec:
        dict_tickers = dict(zip(df[df['Empresa'].isin(empresas_selec)]['Empresa'], 
                                df[df['Empresa'].isin(empresas_selec)]['Ticker']))
        
        hist_data = cargar_historico_variable(dict_tickers, opciones_var[var_sel], f_inicio)
        
        if not hist_data.empty:
            # Limpiar para que Plotly no falle con fechas
            hist_data.index = pd.to_datetime(hist_data.index)
            fig = px.line(hist_data, title=f"Evolución Temporal: {var_sel}", template="plotly_dark")
            fig.update_layout(hovermode="x unified", yaxis_title=var_sel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay suficientes datos históricos para esta combinación.")

# --- 3. GLOSARIO RECUPERADO ---
st.divider()
st.markdown("### 📖 Glosario Técnico")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Market Cap:** Valor total de la empresa (Acciones x Precio).")
    st.markdown("**Ingresos:** Facturación total declarada en balances.")
with c2:
    st.markdown("**P/E Ratio:** Ratio de valoración (Precio / Beneficio).")
    st.markdown("**EBITDA:** Resultado operativo bruto.")
with c3:
    st.markdown("**Margen Neto:** Porcentaje de ingresos que se convierte en beneficio real.")
    st.markdown("**Empleados:** Tamaño de la fuerza laboral operativa.")

st.caption(f"Terminal v4.0 | Datos de Yahoo Finance | Separador de miles: Automático (Punto)")
