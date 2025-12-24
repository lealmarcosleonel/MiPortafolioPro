import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Portfolio Pro Cloud", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN: COTIZACIONES ---
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

# --- FUNCIÓN PARA GUARDAR ---
def guardar_en_gsheets(datos, hoja):
    df_existente = conn.read(worksheet=hoja)
    df_nuevo = pd.DataFrame([datos])
    df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    conn.update(worksheet=hoja, data=df_final)
    st.cache_data.clear()

# --- MENÚ LATERAL ---
st.sidebar.title("💰 Portfolio Cloud")
df_cot = pd.DataFrame([{"Dólar": k, "Compra": v['compra'], "Venta": v['venta']} for k, v in cotizaciones.items()])
st.sidebar.table(df_cot)

val_choice = st.sidebar.selectbox("Valuar en:", ["MEP", "Blue", "Cripto"])
DOLAR_VAL = cotizaciones[val_choice]["venta"]

menu = st.sidebar.radio("Navegación", ["Resumen General", "Bolsa", "Cripto", "Real Estate", "Campo", "Préstamos"])

# --- 1. RESUMEN GENERAL ---
if menu == "Resumen General":
    st.header(f"📊 Dashboard Global ({val_choice})")
    try:
        hojas = ["Bolsa", "Cripto", "Real Estate", "Campo", "Prestamos"]
        lista_dfs = []
        for h in hojas:
            df_h = conn.read(worksheet=h)
            if not df_h.empty: lista_dfs.append(df_h)
        
        if lista_dfs:
            df_total = pd.concat(lista_dfs, ignore_index=True)
            total_ars = 0
            for _, r in df_total.iterrows():
                monto = pd.to_numeric(r['Monto'], errors='coerce') or 0
                factor = DOLAR_VAL if r['Moneda'] == "USD" else 1
                op = -1 if r.get('Operación') == "Venta" else 1
                total_ars += (monto * factor) * op

            c1, c2 = st.columns(2)
            c1.metric("Total Pesos", f"$ {total_ars:,.2f}")
            c2.metric(f"Total USD ({val_choice})", f"u$s {total_ars/DOLAR_VAL:,.2f}")
            st.dataframe(df_total.sort_values(by="Fecha", ascending=False), use_container_width=True)
        else:
            st.info("No hay datos en ninguna pestaña.")
    except:
        st.warning("Asegurate de que las pestañas en Google Sheets tengan los encabezados correctos.")

# --- 2. BOLSA ---
elif menu == "Bolsa":
    st.header("📈 Bolsa de Valores")
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
        if st.form_submit_button("Guardar"):
            guardar_en_gsheets({"Fecha": str(datetime.now().date()), "Activo": activo, "Monto": precio*cantidad, "Moneda": moneda, "Cantidad": cantidad, "Broker": broker, "Sector": "Bolsa", "Operación": "Compra", "Comentarios": comen}, "Bolsa")
            st.success("¡Sincronizado!")

# --- 3. CRIPTO ---
elif menu == "Cripto":
    st.header("₿ Criptomonedas")
    with st.form("f_cripto"):
        ticker = st.text_input("Ticker (Ej: BTC-USD)").upper()
        broker = st.selectbox("Exchange", ["Binance", "Nexo", "BingX", "Otro"])
        cantidad = st.number_input("Cantidad", format="%.8f")
        monto_usd = st.number_input("Inversión USD")
        comen = st.text_area("Comentarios")
        if st.form_submit_button("Guardar"):
            guardar_en_gsheets({"Fecha": str(datetime.now().date()), "Activo": ticker, "Monto": monto_usd, "Moneda": "USD", "Cantidad": cantidad, "Broker": broker, "Sector": "Cripto", "Operación": "Compra", "Comentarios": comen}, "Cripto")
            st.success("¡Guardado!")

# --- 4. REAL ESTATE ---
elif menu == "Real Estate":
    st.header("🏠 Real Estate")
    with st.form("f_re"):
        tipo = st.selectbox("Tipo", ["Departamento en Pozo", "Natania", "Terreno", "Otro"])
        nombre = st.text_input("Nombre Proyecto")
        monto = st.number_input("Monto")
        moneda = st.radio("Moneda", ["USD", "ARS"], horizontal=True)
        comen = st.text_area("Comentarios")
        if st.form_submit_button("Guardar"):
            guardar_en_gsheets({"Fecha": str(datetime.now().date()), "Activo": f"{tipo}: {nombre}", "Monto": monto, "Moneda": moneda, "Broker": "N/A", "Sector": "Real Estate", "Cantidad": 1, "Operación": "Compra", "Comentarios": comen}, "Real Estate")
            st.success("¡Guardado!")

# --- 5. CAMPO ---
elif menu == "Campo":
    st.header("🐄 Campo (Surmax)")
    with st.form("f_campo"):
        tipo = st.selectbox("Proyecto", ["Cría de Vaca", "Recría", "Trigo", "Maíz", "Soja"])
        monto = st.number_input("Capital")
        moneda = st.radio("Moneda", ["USD", "ARS"], horizontal=True)
        comen = st.text_area("Comentarios")
        if st.form_submit_button("Guardar"):
            guardar_en_gsheets({"Fecha": str(datetime.now().date()), "Activo": tipo, "Monto": monto, "Moneda": moneda, "Broker": "Surmax", "Sector": "Campo", "Cantidad": 1, "Operación": "Compra", "Comentarios": comen}, "Campo")
            st.success("¡Guardado!")

# --- 6. PRÉSTAMOS ---
elif menu == "Préstamos":
    st.header("🤝 Préstamos")
    with st.form("f_prestamo"):
        persona = st.text_input("Deudor")
        monto = st.number_input("Monto")
        moneda = st.radio("Moneda", ["USD", "ARS"], horizontal=True)
        comen = st.text_area("Comentarios")
        if st.form_submit_button("Guardar"):
            guardar_en_gsheets({"Fecha": str(datetime.now().date()), "Activo": f"Préstamo: {persona}", "Monto": monto, "Moneda": moneda, "Broker": "Personal", "Sector": "Préstamos", "Cantidad": 1, "Operación": "Compra", "Comentarios": comen}, "Prestamos")
            st.success("¡Registrado!")
