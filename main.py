import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Portfolio Pro Cloud", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# Esto permite que la app lea y escriba en tu Google Drive
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN: OBTENER COTIZACIONES (CON PROTECCIÓN) ---
@st.cache_data(ttl=600)
def obtener_cotizaciones():
    cot = {"MEP": {"compra": 1140.0, "venta": 1170.0}, "Blue": {"compra": 1190.0, "venta": 1220.0}, 
           "Cripto": {"compra": 1185.0, "venta": 1215.0}, "Oficial": {"compra": 980.0, "venta": 1020.0}}
    try:
        res = requests.get("https://dolarapi.com/v1/dolares", timeout=5).json()
        for d in res:
            nombre = d['casa'].capitalize()
            if nombre in cot: cot[nombre] = {"compra": d['compra'], "venta": d['venta']}
    except: pass
    return cot

cotizaciones = obtener_cotizaciones()

# --- MENÚ LATERAL ---
st.sidebar.title("💰 Portfolio Cloud")
df_cot = pd.DataFrame([{"Dólar": k, "Compra": v['compra'], "Venta": v['venta']} for k, v in cotizaciones.items()])
st.sidebar.table(df_cot)

val_choice = st.sidebar.selectbox("Valuar en:", ["MEP", "Blue", "Cripto"])
DOLAR_VAL = cotizaciones[val_choice]["venta"]

menu = st.sidebar.radio("Navegación", ["Resumen General", "Bolsa", "Cripto", "Real Estate", "Campo", "Préstamos"])

# --- FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS ---
def guardar_en_gsheets(datos, hoja):
    # Lee los datos actuales
    df_existente = conn.read(worksheet=hoja)
    df_nuevo = pd.DataFrame([datos])
    # Une y actualiza la planilla
    df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    conn.update(worksheet=hoja, data=df_final)
    st.cache_data.clear() # Limpia cache para ver los datos nuevos al instante

# --- SECCIÓN: RESUMEN GENERAL ---
if menu == "Resumen General":
    st.header(f"📊 Dashboard en la Nube ({val_choice})")
    try:
        # Lee todas las hojas y las une
        hojas = ["Bolsa", "Cripto", "Real Estate", "Campo", "Prestamos"]
        lista_dfs = []
        for h in hojas:
            df_h = conn.read(worksheet=h)
            if not df_h.empty: lista_dfs.append(df_h)
        
        if lista_dfs:
            df_total = pd.concat(lista_dfs, ignore_index=True)
            
            # Cálculo de patrimonio
            total_ars = 0
            for _, r in df_total.iterrows():
                monto = pd.to_numeric(r['Monto'], errors='coerce') or 0
                factor = DOLAR_VAL if r['Moneda'] == "USD" else 1
                op = -1 if r['Operación'] == "Venta" else 1
                total_ars += (monto * factor) * op

            c1, c2 = st.columns(2)
            c1.metric("Total ARS", f"$ {total_ars:,.2f}")
            c2.metric(f"Total USD", f"u$s {total_ars/DOLAR_VAL:,.2f}")
            
            st.dataframe(df_total.sort_values(by="Fecha", ascending=False), use_container_width=True)
    except:
        st.info("Carga tu primera inversión para activar la base de datos en Google Sheets.")

# --- FORMULARIO DE BOLSA (EJEMPLO) ---
elif menu == "Bolsa":
    st.header("📈 Carga de Bolsa")
    st.info("💡 Recordá: `.BA` para Argentina y ticker simple para USA.")
    with st.form("f_bolsa"):
        col1, col2 = st.columns(2)
        with col1:
            activo = st.text_input("Ticker").upper()
            broker = st.selectbox("Broker", ["Inversiones Andinas", "Yont", "Matriz", "Inviu 1", "Inviu 2", "BMB", "IOL", "Balanz"])
        with col2:
            cantidad = st.number_input("Cantidad", min_value=0.0)
            precio = st.number_input("Precio Unitario", min_value=0.0)
        moneda = st.radio("Moneda", ["USD", "ARS"], horizontal=True)
        comen = st.text_area("Comentarios")
        if st.form_submit_button("Guardar en Google Sheets"):
            datos = {
                "Fecha": str(datetime.now().date()), "Activo": activo, "Monto": precio*cantidad, 
                "Moneda": moneda, "Cantidad": cantidad, "Broker": broker, 
                "Sector": "Bolsa", "Operación": "Compra", "Comentarios": comen
            }
            guardar_en_gsheets(datos, "Bolsa")
            st.success("✅ ¡Sincronizado con Google Drive!")