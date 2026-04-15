import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import wbgapi as wb
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Big Tech & AI Intelligence", layout="wide", page_icon="🤖")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .plot-container { border: 1px solid #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUENTES DE DATOS (CACHÉ) ---

@st.cache_data(ttl=86400)
def get_macro_pib():
    """Obtiene el PIB de los principales países para comparar"""
    paises = ['ESP', 'MEX', 'ARG', 'COL', 'CHL', 'DNK', 'NOR', 'PRT']
    d = wb.data.DataFrame('NY.GDP.MKTP.CD', paises, mrv=1)
    d.columns = ['PIB_USD']
    return d

@st.cache_data(ttl=3600)
def get_tech_data():
    # Diccionario de Tickers y categorías
    tickers = {
        "Apple": "AAPL", "Microsoft": "MSFT", "Google": "GOOGL", 
        "Amazon": "AMZN", "Nvidia": "NVDA", "Meta": "META",
        "TSMC": "TSM", "Alibaba": "BABA", "Tencent": "TCEHY", "Baidu": "BIDU"
    }
    
    results = []
    for nombre, t in tickers.items():
        try:
            tk = yf.Ticker(t)
            inf = tk.info
            results.append({
                "Empresa": nombre,
                "Ticker": t,
                "Ecosistema": "USA" if t not in ["BABA", "TCEHY", "BIDU", "TSM"] else "Asia",
                "Market Cap": inf.get('marketCap', 0),
                "Ingresos": inf.get('totalRevenue', 0),
                "Beneficio": inf.get('ebitda', 0),
                "Empleados": inf.get('fullTimeEmployees', 0),
                "Deuda": inf.get('totalDebt', 0),
                "Cloud_Major": "AWS" if t=="AMZN" else ("Azure" if t=="MSFT" else ("Google Cloud" if t=="GOOGL" else "N/A"))
            })
        except: continue
        
    # Añadimos Empresas Privadas (Estimaciones de mercado 2024/2025)
    privadas = [
        {"Empresa": "Anthropic", "Ticker": "Privada", "Ecosistema": "IA Pura", 
         "Market Cap": 18000000000, "Ingresos": 800000000, "Beneficio": 0, "Empleados": 500, "Deuda": 0, "Cloud_Major": "N/A"},
        {"Empresa": "xAI", "Ticker": "Privada", "Ecosistema": "IA Pura", 
         "Market Cap": 24000000000, "Ingresos": 100000000, "Beneficio": 0, "Empleados": 200, "Deuda": 0, "Cloud_Major": "N/A"}
    ]
    
    df = pd.DataFrame(results + privadas)
    return df

# --- LÓGICA DE LA APP ---

st.title("🛰️ Terminal de Inteligencia Competitiva Tech & IA")
st.markdown("---")

df = get_tech_data()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Análisis de Segmentos")
    modo = st.radio("Ver por:", ["Mapa de Poder", "Guerra de Nubes", "Cronología IA", "Empresa vs Países"])
    st.divider()
    comparar_privadas = st.toggle("Incluir Anthropic y xAI", value=True)

if not comparar_privadas:
    df = df[df['Ticker'] != "Privada"]

# --- MÓDULOS ---

if modo == "Mapa de Poder":
    st.subheader("Dominancia del Ecosistema Tech")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.scatter(df, x="Empleados", y="Ingresos", size="Market Cap", color="Ecosistema",
                         hover_name="Empresa", log_x=True, log_y=True, template="plotly_dark",
                         title="Eficiencia: Ingresos por Empleado (Tamaño = Market Cap)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.dataframe(df[['Empresa', 'Market Cap', 'Ingresos']].sort_values(by="Market Cap", ascending=False))

elif modo == "Guerra de Nubes":
    st.subheader("Infraestructura Cloud: El motor de la IA")
    # Datos estimados de cuota de mercado cloud
    cloud_data = pd.DataFrame({
        "Proveedor": ["AWS (Amazon)", "Azure (Microsoft)", "Google Cloud", "Otros"],
        "Ingresos Est. ($B)": [90, 65, 33, 50]
    })
    fig_pie = px.pie(cloud_data, values="Ingresos Est. ($B)", names="Proveedor", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie)
    st.info("Nota: AWS y Azure dominan la infraestructura donde se entrenan Anthropic y xAI.")

elif modo == "Empresa vs Países":
    st.subheader("¿Qué tan grandes son comparadas con naciones?")
    df_pib = get_macro_pib()
    
    # Unimos datos
    comp_data = []
    for _, row in df.iterrows():
        comp_data.append({"Entidad": row['Empresa'], "Valor_USD": row['Ingresos'], "Tipo": "Empresa (Ingresos)"})
    for idx, row in df_pib.iterrows():
        comp_data.append({"Entidad": idx, "Valor_USD": row['PIB_USD'], "Tipo": "País (PIB)"})
        
    df_comp = pd.DataFrame(comp_data).sort_values(by="Valor_USD", ascending=False)
    fig_bar = px.bar(df_comp, x="Entidad", y="Valor_USD", color="Tipo", template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

elif modo == "Cronología IA":
    st.subheader("Hitos y Valoración")
    cronologia = pd.DataFrame([
        {"Fecha": "2022-11", "Evento": "Lanzamiento ChatGPT", "Impacto": "Explosión NVDA"},
        {"Fecha": "2023-01", "Evento": "Inversión MSFT en OpenAI", "Impacto": "Carrera Azure"},
        {"Fecha": "2023-03", "Evento": "Fundación xAI (Elon Musk)", "Impacto": "Nace competidor"},
        {"Fecha": "2024-03", "Evento": "Claude 3 (Anthropic)", "Impacto": "Supera a GPT-4"}
    ])
    st.table(cronologia)
    
    # Gráfico de Nvidia como proxy de la IA
    nvda = yf.download("NVDA", period="2y")['Close']
    st.line_chart(nvda)

st.divider()
st.caption("Terminal v2.0 - Datos Híbridos (Mercado + Estimaciones Privadas + Banco Mundial)")