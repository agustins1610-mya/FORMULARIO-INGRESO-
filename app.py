import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ingreso de Demandas - Estudio Molina",
    page_icon="⚖️",
    layout="wide",
)

# --- ESTILOS VISUALES MODERNOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    :root {
        --primary-color: #1B263B;    /* Navy */
        --accent-color: #C5A065;     /* Gold */
        --bg-color: #F8F9FA;         /* Light Grey */
        --card-bg: #FFFFFF;
        --text-color: #2C3E50;
    }
    
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: var(--primary-color) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    
    /* Header Styling */
    .header-container {
        padding-bottom: 2rem;
        border-bottom: 2px solid #E9ECEF;
        margin-bottom: 2rem;
    }
    
    .main-title {
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #6C757D;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Card Styling */
    .section-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        transition: transform 0.2s ease;
        border: 1px solid rgba(0,0,0,0.02);
    }
    
    .section-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }
    
    /* Custom Badge for Fuero */
    .badge {
        background-color: #E9ECEF;
        color: var(--primary-color);
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Button Styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, var(--primary-color) 0%, #2C3E50 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 16px 32px;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(27, 38, 59, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, var(--accent-color) 0%, #D4AF37 100%);
        box-shadow: 0 6px 20px rgba(197, 160, 101, 0.4);
        transform: translateY(-1px);
        color: white;
    }

    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: var(--primary-color);
        color: rgba(255,255,255,0.8);
        text-align: center;
        padding: 10px;
        font-size: 12px;
        z-index: 999;
        backdrop-filter: blur(10px);
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
with st.container():
    st.markdown("""
        <div class="header-container">
            <h1 class="main-title">⚖️ Sistema de Ingreso de Demandas</h1>
            <div class='subtitle'>
                <strong>Estudio Molina & Asociados</strong> <br>
                <span style='font-size: 0.95rem; opacity: 0.8;'>Formulario Oficial - Poder Judicial de Salta</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

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
st.markdown("### 📂 1. Datos del Expediente")
st.markdown("<br>", unsafe_allow_html=True) # Spacer
c1, c2 = st.columns(2)
with c1:
    fuero = st.selectbox("Fuero / Mesa Distribuidora", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox(
        "Objeto del Juicio",
        LISTA_CODIGOS,
        index=None,
        placeholder="🔍 Buscar objeto (ej: Divorcio, Cobro...)"
    )
monto = st.text_input("Monto del Juicio", value="INDETERMINADO")
st.markdown("</div>", unsafe_allow_html=True)

# --- 2. PARTES ---
c_partes_1, c_partes_2 = st.columns(2)

with c_partes_1:
    st.markdown("<div class='section-card' style='height: 100%;'>", unsafe_allow_html=True)
    st.markdown("### 👤 2. Parte Actora")
    st.info("Ingrese los datos del/los solicitantes")
    df_actores = st.data_editor(
        pd.DataFrame([{"Apellido y Nombre": "", "DNI": "", "Domicilio": ""}]),
        num_rows="dynamic", use_container_width=True, key="actores_edit"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c_partes_2:
    st.markdown("<div class='section-card' style='height: 100%;'>", unsafe_allow_html=True)
    st.markdown("### 🏢 3. Parte Demandada")
    st.info("Ingrese los datos del/los demandados")
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
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🎓 4. Datos del Profesional (Click para editar)", expanded=False):
    st.markdown("<div style='padding: 10px;'>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    nombre_abog = ca.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
    mat_abog = cb.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
    st.markdown("</div>", unsafe_allow_html=True)

# --- GENERACIÓN ---
st.markdown("###")
c_izq, c_btn, c_der = st.columns([1, 2, 1])

with c_btn:
    if st.button("✨ GENERAR DOCUMENTO WORD", type="primary", use_container_width=True):
        # Validaciones
        valid_act = df_actores.iloc[0]["Apellido y Nombre"].strip() != ""
        valid_dem = df_demandados.iloc[0]["Apellido / Razón Social"].strip() != ""
        valid_obj = objeto_seleccionado is not None
        
        if not (valid_act and valid_dem and valid_obj):
            st.error("⚠️ Faltan datos obligatorios: Complete al menos un Actor, un Demandado y seleccione el Objeto.")
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
                    
                    st.success("✅ Documento generado correctamente. Listo para descargar.")
                    st.download_button("📥 DESCARGAR CARÁTULA", data=bio, file_name=fname, 
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                except Exception as e:
                    st.error(f"Error técnico al generar el archivo: {e}")
            else:
                st.error("Error: No se encuentra la plantilla 'formulario ingreso demanda.docx' en el directorio.")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
    Desarrollado por Agustín Salas | Estudio Molina & Asociados <br>
    Orán, Salta - Argentina
    </div>
    """, unsafe_allow_html=True)
