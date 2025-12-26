import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Demandas - Estudio Molina",
    page_icon="⚖️",
    layout="wide",
)

# --- ESTILOS VISUALES (ESTUDIO MOLINA) ---
st.markdown("""
    <style>
    :root {
        --brand-navy: #1B263B;
        --brand-gold: #C5A065;
        --brand-bg: #F5F7FA;
        --card-bg: #FFFFFF;
        --card-border: #E2E8F0;
    }
    .stApp {
        background-color: var(--brand-bg);
    }
    h1, h2, h3, h4 {
        color: var(--brand-navy) !important;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }
    .subtitle {
        color: #6C757D;
        font-size: 1rem;
        margin-top: -10px;
    }
    .section-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        background-color: var(--brand-navy);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 24px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: var(--brand-gold);
        color: white;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: var(--brand-navy);
        color: white;
        text-align: center;
        padding: 8px;
        font-size: 13px;
        z-index: 999;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
c_hero_txt, c_hero_info = st.columns([3, 1])
with c_hero_txt:
    st.title("⚖️ Sistema de Ingreso de Demandas")
    st.markdown("<div class='subtitle'><strong>Estudio Molina & Asociados</strong> · Gestión de Expedientes Judiciales</div>", unsafe_allow_html=True)

with c_hero_info:
    st.info("💡 Complete los datos para generar la carátula automática.")

st.markdown("---")

# --- VARIABLES ---
ABOGADO_DEFECTO = "SALAS AGUSTÍN GABRIEL"
MATRICULA_DEFECTO = "7093"

# --- BASE DE DATOS DE CÓDIGOS ---
CODIGOS_RAW = {
    # LABORAL
    "507": "ACUERDO TRANSACCIONAL – HOMOLOGACIÓN",
    # CIVIL Y COMERCIAL
    "100": "ACCION CONFESORIA - C",
    "112": "ORDINARIO - C",
    "240": "COBRO DE PESOS - C",
    "293": "DAÑOS Y PERJUICIOS - C",
    "237": "DESALOJO - C",
    "125": "AMPARO - C",
    "259": "EJECUCION DE HONORARIOS - C",
    "192": "SUCESORIO - C",
    "290": "SUCESION AB INTESTATO - C",
    # FAMILIA
    "602": "ALIMENTOS - F",
    "721": "DIVORCIO BILATERAL - F",
    "720": "DIVORCIO UNILATERAL - F",
    "901": "VIOLENCIA FAMILIAR - V",
    "902": "VIOLENCIA DE GENERO - V",
    "611": "FILIACION - F",
    "728": "CUIDADO PERSONAL - F",
    "726": "REGIMEN DE COMUNICACION - F",
    # EJECUTIVOS
    "355": "EJECUTIVO - E",
    "356": "EJECUCION PRENDARIA - E",
    "357": "EJECUCION HIPOTECARIA - E",
    # CONCURSOS
    "564": "CONCURSO PREVENTIVO - Q",
    "509": "QUIEBRA DIRECTA - Q",
}
# Lista invertida
LISTA_CODIGOS = sorted([f"{v} - {k}" for k, v in CODIGOS_RAW.items()])

# --- 1. DATOS DEL EXPEDIENTE ---
st.markdown("<div class='section-card'>", unsafe_allow_html=True)
st.subheader("1. Datos del Expediente")
c1, c2 = st.columns(2)
with c1:
    fuero = st.selectbox("Fuero / Mesa", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox(
        "Objeto del Juicio (Buscar)",
        LISTA_CODIGOS,
        index=None,
        placeholder="Escriba aquí (ej: Divorcio, Cobro...)"
    )
monto = st.text_input("Monto del Juicio", value="INDETERMINADO")
st.markdown("</div>", unsafe_allow_html=True)

# --- 2. PARTES ---
c_partes_1, c_partes_2 = st.columns(2)

with c_partes_1:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("2. Parte Actora")
    df_actores = st.data_editor(
        pd.DataFrame([{"Apellido y Nombre": "", "DNI": "", "Domicilio": ""}]),
        num_rows="dynamic", use_container_width=True, key="actores_edit"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c_partes_2:
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("3. Parte Demandada")
    col_cfg = {"Tipo": st.column_config.SelectboxColumn("Doc", options=["CUIT", "DNI"], required=True, default="CUIT")}
    
    df_demandados = st.data_editor(
        pd.DataFrame([{"Apellido / Razón Social": "", "Tipo": "CUIT", "Número": "", "Domicilio": ""}]),
        column_config=col_cfg,
        num_rows="dynamic",
        use_container_width=True,
        key="demandados_edit"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# --- 3. PROFESIONAL ---
with st.expander("4. Datos del Profesional", expanded=True):
    ca, cb = st.columns(2)
    nombre_abog = ca.text_input("Abogado", value=ABOGADO_DEFECTO)
    mat_abog = cb.text_input("Matrícula", value=MATRICULA_DEFECTO)

# --- GENERACIÓN ---
st.markdown("###")
c_izq, c_btn, c_der = st.columns([1, 2, 1])

if c_btn.button("GENERAR DOCUMENTO WORD", type="primary", use_container_width=True):
    # Validaciones
    valid_act = df_actores.iloc[0]["Apellido y Nombre"].strip() != ""
    valid_dem = df_demandados.iloc[0]["Apellido / Razón Social"].strip() != ""
    valid_obj = objeto_seleccionado is not None
    
    if not (valid_act and valid_dem and valid_obj):
        st.error("⚠️ Complete al menos un Actor, un Demandado y seleccione el Objeto.")
    else:
        # Preparación de datos
        act_clean = df_actores[df_actores["Apellido y Nombre"] != ""]
        dem_clean = df_demandados[df_demandados["Apellido / Razón Social"] != ""]
        
        if " - " in objeto_seleccionado:
            parts = objeto_seleccionado.rsplit(" - ", 1)
            cod_desc = parts[0]
            cod_nro = parts[1]
        else:
            cod_desc = objeto_seleccionado
            cod_nro = ""
            
        contexto = {
            'FUERO': fuero,
            'actor_nombre': "\n".join(act_clean["Apellido y Nombre"].astype(str)),
            'actor_dni': "\n".join(act_clean["DNI"].astype(str)),
            'actor_domicilio': "\n".join(act_clean["Domicilio"].astype(str)),
            'demandado_nombre': "\n".join(dem_clean["Apellido / Razón Social"].astype(str)),
            'demandado_tipo_doc': "\n".join(dem_clean["Tipo"].astype(str)),
            'demandado_nro_doc': "\n".join(dem_clean["Número"].astype(str)),
            'demandado_cuit': "\n".join(dem_clean["Número"].astype(str)),
            'demandado_domicilio': "\n".join(dem_clean["Domicilio"].astype(str)),
            'datos_abogado': nombre_abog,
            'código_matricula': mat_abog,
            'firma_abogado': f"{nombre_abog} - M.P. {mat_abog}",
            'codigo_nro': cod_nro,
            'codigo_desc': cod_desc,
            'monto': monto,
            'fecha': datetime.now().strftime("%d/%m/%Y")
        }
        
        # Guardar archivo en memoria
        plantilla = "formulario ingreso demanda.docx"
        if os.path.exists(plantilla):
            try:
                doc = DocxTemplate(plantilla)
                doc.render(contexto)
                bio = io.BytesIO()
                doc.save(bio)
                bio.seek(0)
                
                fname = f"Ingreso_{act_clean.iloc[0]['Apellido y Nombre'].replace(' ', '_')[:15]}.docx"
                
                st.success("✅ Documento generado correctamente.")
                st.download_button("📥 DESCARGAR CARÁTULA", data=bio, file_name=fname, 
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            except Exception as e:
                st.error(f"Error técnico: {e}")
        else:
            st.error("Error: No se encuentra la plantilla .docx en el servidor.")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
    Desarrollado por Agustín Salas de Estudio Molina & Asociados <br>
    Orán, Salta - Argentina
    </div>
    """, unsafe_allow_html=True)