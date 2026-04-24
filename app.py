import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Terminal Pro Tech v4.1", layout="wide")

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
            if not inf: continue
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
    
    df = pd.DataFrame(data)
    # Si por algún motivo la API falla y el DF está vacío, creamos uno de estructura
    if df.empty:
        return pd.DataFrame(columns=["Empresa", "Ticker", "Market Cap", "Ingresos", "P/E Ratio", "Empleados", "Precio", "EBITDA", "Margen Neto (%)"])
    return df

@st.cache_data(ttl=3600)
def cargar_historico_variable(tickers_dict, variable, fecha_inicio):
    df_combined = pd.DataFrame()
    for nombre, t in tickers_dict.items():
        try:
            tk = yf.Ticker(t)
            if variable == "Precio":
                h = tk.history(start=fecha_inicio)['Close']
            elif variable == "Market Cap":
                hist = tk.history(start=fecha_inicio)['Close']
                shares = tk.info.get('sharesOutstanding', 1)
                h = hist * shares
            else:
                # Obtenemos fundamentales trimestrales
                fin = tk.quarterly_financials.T
                if variable in fin.columns:
                    h = fin[variable]
                else: continue
            
            h.name = nombre
            df_combined = pd.concat([df_combined, h], axis=1)
        except: continue
    return df_combined.sort_index()

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 Terminal de Inteligencia Corporativa")

df = cargar_datos_completos()

if df.empty:
    st.error("Error crítico: No se pudieron obtener datos de la API. Reintenta en unos minutos.")
else:
    # --- 1. MONITOR DE MERCADO ---
    st.subheader("📋 Monitor de Mercado")
    st.dataframe(
        df,
        column_config={
            "Empresa": st.column_config.TextColumn("Empresa"),
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
    st.caption("💡 Haz clic en cualquier cabecera para ordenar. Los miles llevan punto de forma automática.")

    st.divider()

    # --- 2. COMPARADOR TEMPORAL ---
    col_ctrl, col_viz = st.columns([1, 3])

    with col_ctrl:
        st.markdown("### 🛠️ Configuración")
        # Aseguramos que los nombres existan antes de ponerlos como default
        options_emp = df['Empresa'].unique().tolist()
        defaults = [e for e in ["Nvidia", "Apple", "Microsoft"] if e in options_emp]
        
        empresas_selec = st.multiselect("Empresas a comparar:", options_emp, default=defaults)
        
        opciones_var = {
            "Precio": "Precio",
            "Market Cap": "Market Cap",
            "Ingresos": "Total Revenue",
            "EBITDA": "EBITDA"
        }
        var_sel = st.selectbox("Variable para el gráfico:", list(opciones_var.keys()))
        
        dias = st.slider("Historial (días):", 30, 1825, 365)
        f_inicio = datetime.now() - timedelta(days=dias)

    with col_viz:
        if empresas_selec:
            dict_tickers = dict(zip(df[df['Empresa'].isin(empresas_selec)]['Empresa'], 
                                    df[df['Empresa'].isin(empresas_selec)]['Ticker']))
            
            with st.spinner('Cargando historial...'):
                hist_data = cargar_historico_variable(dict_tickers, opciones_var[var_sel], f_inicio)
            
            if not hist_data.empty:
                # Limpieza de fechas para Plotly
                hist_data.index = pd.to_datetime(hist_data.index)
                
                # Para Ingresos y EBITDA que son trimestrales, usamos marcadores (puntos)
                mode = 'lines+markers' if var_sel in ["Ingresos", "EBITDA"] else 'lines'
                
                fig = px.line(hist_data, title=f"Evolución: {var_sel}", template="plotly_dark")
                fig.update_traces(mode=mode)
                fig.update_layout(hovermode="x unified", yaxis_title=var_sel, legend_title="Empresa")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos históricos suficientes para esta variable en el periodo elegido.")

    # --- 3. GLOSARIO TÉCNICO ---
    st.divider()
    st.markdown("### 📖 Glosario Técnico")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Market Cap:** Valor total de la empresa en bolsa (Acciones x Precio).")
        st.markdown("**Ingresos:** Facturación total bruta (Revenue) declarada.")
    with c2:
        st.markdown("**P/E Ratio:** Ratio de valoración. Cuántas veces se paga el beneficio anual.")
        st.markdown("**EBITDA:** Beneficio operativo bruto antes de impuestos y amortizaciones.")
    with c3:
        st.markdown("**Margen Neto:** Porcentaje de cada dólar de venta que se convierte en beneficio puro.")
        st.markdown("**Empleados:** Fuerza laboral total según el último reporte anual.")

st.caption(f"Terminal v4.1 | Fuente: Yahoo Finance | Actualizado: {datetime.now().strftime('%H:%M:%S')}")
