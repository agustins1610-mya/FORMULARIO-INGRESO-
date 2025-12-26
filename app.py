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
)

# --- ESTILOS VISUALES (CORREGIDOS PARA LEGIBILIDAD) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    /* Variables de color */
    :root {
        --primary: #1B263B;      /* Navy Profundo */
        --secondary: #415A77;    /* Azul Acero */
        --accent: #C5A065;       /* Dorado */
        --background: #F0F2F6;   /* Gris muy claro para fondo global */
        --card-bg: #FFFFFF;      /* Blanco puro para tarjetas */
        --text-dark: #1A1A1A;    /* Casi negro para lectura óptima */
        --text-grey: #4A4A4A;    /* Gris oscuro para subtítulos */
    }
    
    /* Fondo general */
    .stApp {
        background-color: var(--background);
        font-family: 'Roboto', sans-serif;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: var(--primary) !important;
        font-weight: 700;
    }
    
    /* Estilo de los BLOQUES (Cards) */
    .data-block {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid #E0E0E0; /* Borde sutil para definir el bloque */
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); /* Sombra suave */
        color: var(--text-dark); /* FORZAR COLOR DE TEXTO OSCURO */
    }
    
    .data-block h4 {
        color: var(--secondary);
        font-size: 1.1rem;
        margin-bottom: 15px;
        border-bottom: 2px solid var(--accent);
        padding-bottom: 5px;
        display: inline-block;
    }

    /* Forzar color de texto en inputs y tablas de streamlit para contraste */
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: var(--text-dark) !important;
        font-weight: 500;
    }
    
    /* Botón Principal */
    div.stButton > button:first-child {
        background: var(--primary);
        color: white;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 1.1rem;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.2s;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background: var(--accent);
        color: var(--primary);
        font-weight: bold;
        transform: scale(1.01);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: var(--text-grey);
        font-size: 0.8rem;
        opacity: 0.8;
    }
    
    /* Ocultar menú de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="margin:0; font-size: 2.5rem;">⚖️ Ingreso de Demandas</h1>
        <p style="color: #555; font-size: 1.1rem;">Formulario Oficial - Poder Judicial de Salta</p>
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
LISTA_CODIGOS = sorted([f"{v} - {k}" for k, v in CODIGOS_RAW.items()])

# --- BLOQUE 1: DATOS DEL EXPEDIENTE ---
st.markdown('<div class="data-block"><h4>📂 1. Datos del Expediente</h4>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 1])

with c1:
    fuero = st.selectbox(
        "Fuero / Mesa",
        ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"],
        help="Seleccione el fuero correspondiente al expediente."
    )

with c2:
    objeto_seleccionado = st.selectbox(
        "Objeto del Juicio",
        LISTA_CODIGOS,
        index=None,
        placeholder="Escriba para buscar (ej: Divorcio)...",
        help="Código y descripción del objeto de la demanda."
    )

with c3:
    monto = st.text_input(
        "Monto ($)", 
        value="INDETERMINADO",
        help="Ingrese el monto numérico o 'INDETERMINADO'."
    )
st.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 2: PARTES (ACTOR Y DEMANDADO) ---
c_actor, c_demandado = st.columns(2)

# BLOQUE ACTOR
with c_actor:
    st.markdown('<div class="data-block" style="min-height: 400px;"><h4>👤 2. Parte Actora (Quien demanda)</h4>', unsafe_allow_html=True)
    st.info("💡 Puede agregar múltiples actores agregando filas.")
    df_actores = st.data_editor(
        pd.DataFrame([{"Apellido y Nombre": "", "DNI": "", "Domicilio": ""}]),
        num_rows="dynamic",
        use_container_width=True,
        key="actores_edit",
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# BLOQUE DEMANDADO
with c_demandado:
    st.markdown('<div class="data-block" style="min-height: 400px;"><h4>🛑 3. Parte Demandada (A quien se demanda)</h4>', unsafe_allow_html=True)
    st.info("💡 Seleccione si es CUIT o DNI según corresponda.")
    col_cfg = {
        "Tipo": st.column_config.SelectboxColumn("Doc", options=["CUIT", "DNI"], required=True, default="CUIT", width="small"),
        "Número": st.column_config.TextColumn("Número", width="medium"),
        "Apellido / Razón Social": st.column_config.TextColumn("Nombre / Razón Social", width="large")
    }
    
    df_demandados = st.data_editor(
        pd.DataFrame([{"Apellido / Razón Social": "", "Tipo": "CUIT", "Número": "", "Domicilio": ""}]),
        column_config=col_cfg,
        num_rows="dynamic",
        use_container_width=True,
        key="demandados_edit",
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- BLOQUE 3: PROFESIONAL ---
st.markdown('<div class="data-block"><h4>🎓 4. Datos del Profesional</h4>', unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1:
    nombre_abog = st.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
with cp2:
    mat_abog = st.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
st.markdown('</div>', unsafe_allow_html=True)

# --- GENERACIÓN ---
st.markdown("###")
c_gen_izq, c_gen_btn, c_gen_der = st.columns([1, 2, 1])

with c_gen_btn:
    if st.button("📝 GENERAR Y DESCARGAR FORMULARIO WORD"):
        # Validaciones simples
        valid_act = df_actores.iloc[0]["Apellido y Nombre"].strip() != ""
        valid_dem = df_demandados.iloc[0]["Apellido / Razón Social"].strip() != ""
        valid_obj = objeto_seleccionado is not None
        
        if not (valid_act and valid_dem and valid_obj):
            st.error("⚠️ Faltan datos obligatorios. Por favor revise los bloques marcados.")
        else:
            # Lógica de generación (idéntica a la anterior pero limpia)
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
            
            plantilla = "formulario ingreso demanda.docx"
            if os.path.exists(plantilla):
                try:
                    doc = DocxTemplate(plantilla)
                    doc.render(contexto)
                    bio = io.BytesIO()
                    doc.save(bio)
                    bio.seek(0)
                    
                    fname = f"Ingreso_{act_clean.iloc[0]['Apellido y Nombre'].replace(' ', '_')[:10]}.docx"
                    st.success("✅ ¡Documento generado con éxito!")
                    st.download_button(
                        label="📥 DESCARGAR AHORA",
                        data=bio,
                        file_name=fname,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary" 
                    )
                except Exception as e:
                    st.error(f"Error técnico: {e}")
            else:
                st.error("Error: Falta la plantilla .docx")

# --- FOOTER ---
st.markdown('<div class="footer">Estudio Molina & Asociados - Sistema Interno</div>', unsafe_allow_html=True)
