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
    initial_sidebar_state="expanded"
)

# --- BARRA LATERAL (SELECTOR DE TEMA) ---
with st.sidebar:
    st.header("⚙️ Configuración")
    tema = st.radio("Apariencia", ["Claro (Clásico)", "Oscuro (Moderno)"], index=0)
    st.markdown("---")
    st.info("ℹ️ Si no logra leer algún texto, cambie al modo 'Claro'.")

# --- LÓGICA DE ESTILOS CSS SEGÚN TEMA ---
if tema == "Claro (Clásico)":
    # MODO CLARO FORZADO (Texto oscuro sobre fondo blanco)
    css_variables = """
        --bg-app: #F5F7FA;
        --bg-card: #FFFFFF;
        --text-main: #1A1A1A;
        --text-sub: #4A4A4A;
        --border-color: #E2E8F0;
        --primary: #1B263B;
        --accent: #C5A065;
        --input-bg: #FFFFFF;
        --input-text: #1A1A1A;
    """
else:
    # MODO OSCURO (Texto claro sobre fondo azul profundo)
    css_variables = """
        --bg-app: #0F172A;
        --bg-card: #1E293B;
        --text-main: #E2E8F0;
        --text-sub: #94A3B8;
        --border-color: #334155;
        --primary: #38BDF8;
        --accent: #C5A065;
        --input-bg: #334155;
        --input-text: #FFFFFF;
    """

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    :root {{
        {css_variables}
    }}

    /* APLICACIÓN GLOBAL */
    [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }}
    
    [data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0);
    }}

    /* INPUTS Y SELECTORES (Forzados para coincidir con el tema) */
    input, .stTextInput input, .stNumberInput input {{
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--border-color) !important;
    }}
    
    div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--border-color) !important;
    }}
    
    div[data-baseweb="select"] span {{
        color: var(--input-text) !important;
    }}
    
    /* MENÚS DESPLEGABLES */
    ul[data-baseweb="menu"] {{
        background-color: var(--input-bg) !important;
    }}
    li[data-baseweb="option"] {{
        color: var(--input-text) !important;
    }}

    /* LABELS */
    .stTextInput label, .stSelectbox label, p, h1, h2, h3, h4 {{
        color: var(--text-main) !important;
    }}

    /* TARJETAS (DATA BLOCKS) */
    .data-block {{
        background-color: var(--bg-card);
        padding: 25px;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }}
    
    .section-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--primary) !important;
        border-bottom: 2px solid var(--accent);
        padding-bottom: 8px;
        margin-bottom: 15px;
        display: inline-block;
    }}

    /* BOTÓN */
    div.stButton > button {{
        background: linear-gradient(135deg, #C5A065 0%, #B8860B 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        font-weight: bold;
        transition: transform 0.2s;
        border-radius: 8px;
    }}
    div.stButton > button:hover {{
        transform: scale(1.02);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }}

    /* FOOTER */
    .footer {{
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: var(--bg-card);
        border-top: 1px solid var(--border-color);
        color: var(--text-sub);
        text-align: center;
        padding: 10px;
        font-size: 12px;
        z-index: 999;
    }}
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 2.8rem; margin-bottom: 0;">⚖️ Sistema de Demandas</h1>
        <p style="opacity: 0.8; font-size: 1.1rem;">Formulario Oficial de Ingreso - Poder Judicial de Salta</p>
    </div>
""", unsafe_allow_html=True)

# --- DATOS BASE ---
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

# --- BLOQUE 1: EXPEDIENTE ---
st.markdown('<div class="data-block"><div class="section-title">📂 1. DATOS DEL EXPEDIENTE</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.2, 2, 0.8])
with c1:
    fuero = st.selectbox("Fuero / Mesa", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox("Objeto del Juicio", LISTA_CODIGOS, index=None, placeholder="Busque el código...")
with c3:
    monto = st.text_input("Monto ($)", value="INDETERMINADO")
st.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 2: PARTES (CORREGIDO) ---
st.markdown('<div class="data-block"><div class="section-title">👥 2. PARTES INTERVINIENTES</div>', unsafe_allow_html=True)

col_actor, col_sep, col_demandado = st.columns([1, 0.05, 1])

# --- PARTE ACTORA ---
with col_actor:
    st.markdown("#### 👤 Parte Actora")
    st.caption("Quien reclama / inicia la demanda")
    
    df_actores = st.data_editor(
        pd.DataFrame([{"Apellido y Nombre": "", "DNI": "", "Domicilio": ""}]),
        column_config={
            "Apellido y Nombre": st.column_config.TextColumn(
                "👤 Apellido y Nombre",
                width="large",
                required=True,
                help="Ingrese Apellido y Nombre completos"
            ),
            "DNI": st.column_config.TextColumn(
                "🆔 DNI / CUIT",
                width="small",
                required=True,
                help="Ingrese números sin puntos ni guiones"
            ),
            "Domicilio": st.column_config.TextColumn(
                "📍 Domicilio Real",
                width="large",
                required=True
            ),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_actores"
    )

# --- SEPARADOR VISUAL ---
with col_sep:
    st.markdown("") 

# --- PARTE DEMANDADA ---
with col_demandado:
    st.markdown("#### 🛑 Parte Demandada")
    st.caption("Contra quien se dirige la acción")
    
    df_demandados = st.data_editor(
        pd.DataFrame([{"Apellido/Razón": "", "Tipo": "CUIT", "Doc N°": "", "Domicilio": ""}]),
        column_config={
            "Apellido/Razón": st.column_config.TextColumn(
                "🏢 Nombre / Razón Social",
                width="large",
                required=True,
                help="Nombre de la persona o empresa demandada"
            ),
            "Tipo": st.column_config.SelectboxColumn(
                "📄 Tipo",
                options=["CUIT", "DNI"],
                width="small",
                required=True
            ),
            "Doc N°": st.column_config.TextColumn(
                "🔢 N° Doc",
                width="small"
            ),
            "Domicilio": st.column_config.TextColumn(
                "📍 Domicilio",
                width="large"
            ),
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="editor_demandados"
    )

st.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 3: PROFESIONAL ---
st.markdown('<div class="data-block"><div class="section-title">🎓 3. DATOS DEL PROFESIONAL</div>', unsafe_allow_html=True)
c_prof1, c_prof2 = st.columns(2)
with c_prof1:
    nombre_abog = st.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
with c_prof2:
    mat_abog = st.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
st.markdown('</div>', unsafe_allow_html=True)

# --- BOTÓN GENERAR ---
st.markdown("###")
col_izq, col_centro, col_der = st.columns([1, 2, 1])

with col_centro:
    if st.button("✨ GENERAR DOCUMENTO WORD", use_container_width=True):
        # Validaciones
        valid_act = df_actores.iloc[0]["Apellido y Nombre"].strip() != ""
        valid_dem = df_demandados.iloc[0]["Apellido/Razón"].strip() != ""
        valid_obj = objeto_seleccionado is not None
        
        if not (valid_act and valid_dem and valid_obj):
            st.error("⚠️ Faltan datos obligatorios. Revise Actor, Demandado u Objeto.")
        else:
            # Procesar datos limpios
            act_clean = df_actores[df_actores["Apellido y Nombre"] != ""]
            dem_clean = df_demandados[df_demandados["Apellido/Razón"] != ""]
            
            # Separar código y descripción
            if objeto_seleccionado and " - " in objeto_seleccionado:
                parts = objeto_seleccionado.rsplit(" - ", 1)
                cod_desc = parts[0]
                cod_nro = parts[1]
            else:
                cod_desc = objeto_seleccionado if objeto_seleccionado else ""
                cod_nro = ""
            
            # Contexto para Jinja2 (DocxTemplate)
            contexto = {
                'FUERO': fuero,
                # Actores
                'actor_nombre': "\n".join(act_clean["Apellido y Nombre"].astype(str)),
                'actor_dni': "\n".join(act_clean["DNI"].astype(str)),
                'actor_domicilio': "\n".join(act_clean["Domicilio"].astype(str)),
                # Demandados (Asegurar mapeo correcto de nombres de columna)
                'demandado_nombre': "\n".join(dem_clean["Apellido/Razón"].astype(str)),
                'demandado_tipo_doc': "\n".join(dem_clean["Tipo"].astype(str)),
                'demandado_nro_doc': "\n".join(dem_clean["Doc N°"].astype(str)),
                'demandado_domicilio': "\n".join(dem_clean["Domicilio"].astype(str)),
                # Abogado y otros
                'datos_abogado': nombre_abog,
                'código_matricula': mat_abog,
                'firma_abogado': f"{nombre_abog} - M.P. {mat_abog}",
                'codigo_nro': cod_nro,
                'codigo_desc': cod_desc,
                'monto': monto,
                'fecha': datetime.now().strftime("%d/%m/%Y")
            }
            
            # Generación del archivo
            plantilla = "formulario ingreso demanda.docx"
            if os.path.exists(plantilla):
                try:
                    doc = DocxTemplate(plantilla)
                    doc.render(contexto)
                    bio = io.BytesIO()
                    doc.save(bio)
                    bio.seek(0)
                    
                    nombre_archivo = f"Ingreso_{act_clean.iloc[0]['Apellido y Nombre'].replace(' ', '_')[:10]}.docx"
                    
                    st.success("✅ ¡Documento generado correctamente!")
                    st.download_button(
                        label="📥 DESCARGAR CARÁTULA",
                        data=bio,
                        file_name=nombre_archivo,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Error técnico: {e}")
            else:
                st.error("❌ Error: No se encuentra la plantilla .docx en el servidor.")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
    Estudio Molina & Asociados | Orán, Salta
    </div>
    """, unsafe_allow_html=True)
