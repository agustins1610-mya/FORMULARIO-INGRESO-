import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ingreso de Demandas",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS VISUALES (FORZADO MODO CLARO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    /* 1. FORZAR VARIABLES DE COLOR (MODO CLARO) */
    :root {
        --primary: #1B263B;
        --accent: #C5A065;
        --bg-app: #F0F2F6;
        --bg-card: #FFFFFF;
        --text-main: #212529;
        --text-light: #6C757D;
    }

    /* 2. FONDO GENERAL */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-app);
        font-family: 'Roboto', sans-serif;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    /* 3. ARREGLAR INPUTS Y SELECTS (ELIMINAR EL FONDO NEGRO) */
    /* Esto fuerza a que los casilleros sean blancos con texto negro siempre */
    
    /* Inputs de texto y número */
    input[type="text"], input[type="number"], .stTextInput input {
        background-color: #FFFFFF !important;
        color: #212529 !important;
        border: 1px solid #CED4DA !important;
        border-radius: 6px !important;
    }
    
    /* Listas desplegables (Selectbox) - El problema principal de la foto */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #212529 !important;
        border: 1px solid #CED4DA !important;
        border-radius: 6px !important;
    }
    
    /* Texto dentro del select */
    div[data-baseweb="select"] span {
        color: #212529 !important;
    }

    /* El menú desplegable (las opciones cuando haces click) */
    ul[data-baseweb="menu"] {
        background-color: #FFFFFF !important;
    }
    
    li[data-baseweb="option"] {
        color: #212529 !important; 
    }

    /* Etiquetas (Labels) encima de los inputs */
    .stTextInput label, .stSelectbox label, .stNumberInput label, p {
        color: #212529 !important;
        font-weight: 500 !important;
    }

    /* 4. ESTILO DE TARJETAS (DATA BLOCKS) */
    .data-block {
        background-color: var(--bg-card);
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #E9ECEF;
        margin-bottom: 20px;
    }
    
    .block-header {
        color: var(--primary);
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 15px;
        border-bottom: 2px solid var(--accent);
        padding-bottom: 8px;
        display: inline-block;
    }

    /* 5. TÍTULOS PRINCIPALES */
    h1 {
        color: var(--primary) !important;
        font-weight: 800 !important;
    }
    
    .subtitle {
        color: var(--text-light);
        font-size: 1rem;
    }

    /* 6. BOTÓN */
    div.stButton > button {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        padding: 15px 30px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    
    div.stButton > button:hover {
        background-color: var(--accent) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(197, 160, 101, 0.4) !important;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: var(--primary);
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 12px;
        z-index: 9999;
    }
    
    /* Ocultar elementos nativos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="margin-bottom: 5px;">⚖️ Ingreso de Demandas</h1>
        <div class="subtitle">Formulario Oficial - Poder Judicial de Salta</div>
    </div>
""", unsafe_allow_html=True)

# --- VARIABLES Y DATOS ---
ABOGADO_DEFECTO = "SALAS AGUSTÍN GABRIEL"
MATRICULA_DEFECTO = "7093"

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
LISTA_CODIGOS = sorted([f"{v} - {k}" for k, v in CODIGOS_RAW.items()])

# --- BLOQUE 1: DATOS DEL EXPEDIENTE ---
st.markdown('<div class="data-block"><div class="block-header">📂 1. Datos del Expediente</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    fuero = st.selectbox("Fuero / Mesa", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox("Objeto del Juicio", LISTA_CODIGOS, index=None, placeholder="Seleccione el objeto...")
with c3:
    monto = st.text_input("Monto ($)", value="INDETERMINADO")
st.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 2: PARTES ---
c_left, c_right = st.columns(2)

with c_left:
    st.markdown('<div class="data-block" style="height: 100%;">', unsafe_allow_html=True)
    st.markdown('<div class="block-header">👤 2. Parte Actora</div>', unsafe_allow_html=True)
    st.caption("Ingrese los datos de quien demanda:")
    df_actores = st.data_editor(
        pd.DataFrame([{"Apellido y Nombre": "", "DNI": "", "Domicilio": ""}]),
        num_rows="dynamic", use_container_width=True, key="actores", hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with c_right:
    st.markdown('<div class="data-block" style="height: 100%;">', unsafe_allow_html=True)
    st.markdown('<div class="block-header">🛑 3. Parte Demandada</div>', unsafe_allow_html=True)
    st.caption("Ingrese los datos de a quien se demanda:")
    col_cfg = {
        "Tipo": st.column_config.SelectboxColumn("Doc", options=["CUIT", "DNI"], required=True, default="CUIT", width="small"),
        "Número": st.column_config.TextColumn("Nro Doc", width="medium"),
        "Apellido / Razón Social": st.column_config.TextColumn("Nombre / Razón", width="large")
    }
    df_demandados = st.data_editor(
        pd.DataFrame([{"Apellido / Razón Social": "", "Tipo": "CUIT", "Número": "", "Domicilio": ""}]),
        column_config=col_cfg, num_rows="dynamic", use_container_width=True, key="demandados", hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 3: PROFESIONAL ---
st.markdown('<br>', unsafe_allow_html=True)
st.markdown('<div class="data-block"><div class="block-header">🎓 4. Datos del Profesional</div>', unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1:
    nombre_abog = st.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
with cp2:
    mat_abog = st.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
st.markdown('</div>', unsafe_allow_html=True)

# --- GENERACIÓN ---
st.markdown("###")
col_spacer, col_btn, col_spacer2 = st.columns([1, 2, 1])

with col_btn:
    if st.button("GENERAR FORMULARIO WORD"):
        # Validaciones
        valid_act = df_actores.iloc[0]["Apellido y Nombre"].strip() != ""
        valid_dem = df_demandados.iloc[0]["Apellido / Razón Social"].strip() != ""
        valid_obj = objeto_seleccionado is not None
        
        if not (valid_act and valid_dem and valid_obj):
            st.error("⚠️ Faltan datos: Complete Actor, Demandado y Objeto.")
        else:
            # Procesar datos
            act_clean = df_actores[df_actores["Apellido y Nombre"] != ""]
            dem_clean = df_demandados[df_demandados["Apellido / Razón Social"] != ""]
            
            if objeto_seleccionado and " - " in objeto_seleccionado:
                parts = objeto_seleccionado.rsplit(" - ", 1)
                cod_desc = parts[0]
                cod_nro = parts[1]
            else:
                cod_desc = objeto_seleccionado if objeto_seleccionado else ""
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
            
            # Generar
            plantilla = "formulario ingreso demanda.docx"
            if os.path.exists(plantilla):
                try:
                    doc = DocxTemplate(plantilla)
                    doc.render(contexto)
                    bio = io.BytesIO()
                    doc.save(bio)
                    bio.seek(0)
                    fname = f"Ingreso_{act_clean.iloc[0]['Apellido y Nombre'].replace(' ', '_')[:10]}.docx"
                    
                    st.success("✅ Documento listo.")
                    st.download_button("📥 DESCARGAR AHORA", data=bio, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Falta la plantilla .docx")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
    Estudio Molina & Asociados | Orán, Salta
    </div>
    """, unsafe_allow_html=True)
