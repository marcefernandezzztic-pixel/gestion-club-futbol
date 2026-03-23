import streamlit as st
import pandas as pd
from gspread_pandas import Spread, Conf
from fpdf import FPDF
import datetime
import urllib.parse

# Configuración de la página para celular
st.set_page_config(page_title="Club Manager", layout="centered")

# --- CONEXIÓN CON GOOGLE SHEETS ---
SHEET_NAME = "Socios Club"

try:
    # 1. Creamos el diccionario de configuración desde los Secrets de Streamlit
    creds_dict = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    }
    
    # 2. Configuramos la conexión usando ese diccionario
    config = Conf.from_dict(creds_dict)
    spread = Spread(SHEET_NAME, config=config) # <--- IMPORTANTE: pasar el config aquí
    df = spread.sheet_to_df(index=0)
    
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.title("⚽ Gestión de Cobros")

# --- BUSCADOR ---
busqueda = st.text_input("Buscar por DNI o Apellido")

if busqueda:
    # Filtramos en el DataFrame de Pandas
    resultado = df[(df['DNI'].str.contains(busqueda, case=False)) | 
                   (df['Apellido'].str.contains(busqueda, case=False))]

    if not resultado.empty:
        for index, row in resultado.iterrows():
            with st.container():
                st.write(f"### {row['Apellido']}, {row['Nombre']}")
                st.write(f"**DNI:** {row['DNI']} | **Cuota:** ${row['Valor Cuota']}")
                
                mes_pago = st.date_input("Mes que abona", value=datetime.date.today(), key=f"date_{index}")
                
                if st.button(f"Registrar Pago de {row['Nombre']}", key=f"btn_{index}"):
                    # Lógica para actualizar el Excel
                    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
                    # Actualizar en el DataFrame y subirlo
                    df.at[index, 'Mes que abona'] = mes_pago.strftime("%m/%Y")
                    df.at[index, 'Fecha de Pago'] = fecha_hoy
                    spread.df_to_sheet(df, index=False, replace=True)
                    
                    # Generar Link de WhatsApp con recibo (simulado con texto)
                    texto_wa = f"Hola {row['Nombre']}, confirmamos tu pago de cuota mes {mes_pago.strftime('%m/%Y')}. Gracias!"
                    link_wa = f"https://wa.me/{row['Nro Celular']}?text={urllib.parse.quote(texto_wa)}"
                    
                    st.success("¡Pago registrado!")
                    st.markdown(f"[📲 Enviar Comprobante por WhatsApp]({link_wa})")
    else:
        # --- FORMULARIO PARA NUEVO SOCIO ---
        st.warning("Socio no encontrado. ¿Deseas darlo de alta?")
        with st.form("nuevo_socio"):
            nuevo_dni = st.text_input("DNI")
            nuevo_ape = st.text_input("Apellido")
            nuevo_nom = st.text_input("Nombre")
            nuevo_cel = st.text_input("Celular (con código de área)")
            nueva_cat = st.text_input("Categoría")
            nuevo_val = st.number_input("Valor Cuota", format="%.2f")
            
            if st.form_submit_button("Guardar Nuevo Socio"):
                nuevo_registro = {
                    "DNI": nuevo_dni, "Apellido": nuevo_ape, "Nombre": nuevo_nom,
                    "Nro Celular": nuevo_cel, "Categoría": nueva_cat, "Valor Cuota": nuevo_val,
                    "Mes que abona": "", "Fecha de Pago": ""
                }
                df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
                spread.df_to_sheet(df, index=False, replace=True)
                st.success("Socio agregado correctamente.")
                st.rerun()
