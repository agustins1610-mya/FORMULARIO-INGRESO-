import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Demandas",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. GESTIÓN DE ESTADO (MEMORIA PARA AGREGAR/QUITAR PERSONAS) ---
if 'actores' not in st.session_state:
    st.session_state.actores = [{"id": 0}] # Empieza con un actor
if 'demandados' not in st.session_state:
    st.session_state.demandados = [{"id": 0}] # Empieza con un demandado

def agregar_actor():
    st.session_state.actores.append({"id": len(st.session_state.actores)})

def quitar_actor():
    if len(st.session_state.actores) > 1:
        st.session_state.actores.pop()

def agregar_demandado():
    st.session_state.demandados.append({"id": len(st.session_state.demandados)})

def quitar_demandado():
    if len(st.session_state.demandados) > 1:
        st.session_state.demandados.pop()

# --- 3. ESTILOS CSS (DISEÑO DE TARJETAS BLANCAS CON BORDE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    :root {
        --bg-app: #F5F7FA;
        --border-input: #333333; /* Borde oscuro que pediste */
    }

    /* Fondo general */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
    }
    
    /* Títulos */
    h1, h2, h3 { color: #1B263B !important; }

    /* ESTILO DE LOS INPUTS (Cuadros de texto) */
    /* Esto fuerza que se vean como cajas blancas con borde negro fino */
    input[type="text"], input[type="number"], .stTextInput input, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid var(--border-input) !important;
        border-radius: 6px !important;
        min-height: 45px !important;
    }

    /* Etiquetas de los inputs */
    .stTextInput label, .stSelectbox label {
        color: #1A1A1A !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
    }

    /* CONTENEDORES (TARJETAS) */
    .data-card {
        background-color: white;
        padding: 25px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .card-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1B263B;
        border-bottom: 2px solid #C5A065;
        padding-bottom: 8px;
        margin-bottom: 20px;
        display: block;
    }

    /* Separador visual entre personas */
    hr.persona-separator {
        border: 0;
        border-top: 1px dashed #CBD5E1;
        margin: 20px 0;
    }

    /* BOTONES */
    .stButton button {
        border-radius: 6px;
        font-weight: 600;
    }
    
    /* Footer */
    .footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: white; border-top: 1px solid #E2E8F0;
        text-align: center; padding: 10px; font-size: 12px; color: #666;
        z-index: 999;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. CABECERA ---
st.markdown("<div style='text-align: center; margin-bottom: 20px;'>", unsafe_allow_html=True)
st.title("⚖️ Sistema de Demandas")
st.markdown("**VERSIÓN: TARJETAS INDIVIDUALES** (Si ves esto, el código se actualizó)")
st.markdown("</div>", unsafe_allow_html=True)

# --- 5. CONSTANTES ---
ABOGADO_DEFECTO = "SALAS AGUSTÍN GABRIEL"
MATRICULA_DEFECTO = "7093"
CODIGOS_RAW = {
    "507": "ACUERDO TRANSACCIONAL – HOMOLOGACIÓN",
    "100": "ACCION CONFESORIA - C", "112": "ORDINARIO - C", "240": "COBRO DE PESOS - C",
    "293": "DAÑOS Y PERJUICIOS - C", "237": "DESALOJO - C", "125": "AMPARO - C",
    "259": "EJECUCION DE HONORARIOS - C", "192": "SUCESORIO - C", "290": "SUCESION AB INTESTATO - C",
    "602": "ALIMENTOS - F", "721": "DIVORCIO BILATERAL - F", "720": "DIVORCIO UNILATERAL - F",
    "901": "VIOLENCIA FAMILIAR - V", "902": "VIOLENCIA DE GENERO - V", "611": "FILIACION - F",
    "728": "CUIDADO PERSONAL - F", "726": "REGIMEN DE COMUNICACION - F",
    "355": "EJECUTIVO - E", "356": "EJECUCION PRENDARIA - E", "357": "EJECUCION HIPOTECARIA - E",
    "564": "CONCURSO PREVENTIVO - Q", "509": "QUIEBRA DIRECTA - Q",
}
LISTA_CODIGOS = sorted([f"{v} - {k}" for k, v in CODIGOS_RAW.items()])

# --- 6. BLOQUE 1: EXPEDIENTE ---
st.markdown('<div class="data-card"><span class="card-header">📂 1. Datos del Expediente</span>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 0.8])
with c1:
    fuero = st.selectbox("Fuero", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox("Objeto del Juicio", LISTA_CODIGOS, index=None, placeholder="Seleccione...")
with c3:
    monto = st.text_input("Monto ($)", value="INDETERMINADO")
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. BLOQUE 2: PARTES (AQUÍ ESTÁ EL CAMBIO) ---
st.markdown('<div class="data-card"><span class="card-header">👥 2. Partes Intervinientes</span>', unsafe_allow_html=True)

col_izq, col_espacio, col_der = st.columns([1, 0.1, 1])

# --- LADO IZQUIERDO: ACTORES ---
with col_izq:
    st.markdown("#### 👤 Parte Actora")
    actores_data = [] # Lista para guardar lo que escribas
    
    # Bucle para generar tarjetas por cada actor
    for i, _ in enumerate(st.session_state.actores):
        if i > 0: st.markdown('<hr class="persona-separator">', unsafe_allow_html=True)
        
        st.markdown(f"**Actor #{i+1}**")
        # Inputs individuales (NO SON TABLAS)
        nombre = st.text_input(f"Apellido y Nombre", key=f"a_nom_{i}")
        
        c_dni, c_dom = st.columns([0.4, 0.6])
        dni = c_dni.text_input(f"DNI", key=f"a_dni_{i}")
        dom = c_dom.text_input(f"Domicilio Real", key=f"a_dom_{i}")
        
        actores_data.append({"nombre": nombre, "dni": dni, "domicilio": dom})

    # Botones pequeños
    c_btn1, c_btn2 = st.columns(2)
    if c_btn1.button("➕ Otro Actor", key="add_act"): agregar_actor()
    if c_btn2.button("➖ Quitar", key="del_act"): quitar_actor()

# --- LADO DERECHO: DEMANDADOS ---
with col_der:
    st.markdown("#### 🛑 Parte Demandada")
    demandados_data = []
    
    for i, _ in enumerate(st.session_state.demandados):
        if i > 0: st.markdown('<hr class="persona-separator">', unsafe_allow_html=True)
        
        st.markdown(f"**Demandado #{i+1}**")
        
        nombre = st.text_input(f"Nombre / Razón Social", key=f"d_nom_{i}")
        
        c_tipo, c_doc = st.columns([0.3, 0.7])
        tipo = c_tipo.selectbox("Tipo", ["CUIT", "DNI"], key=f"d_tipo_{i}", label_visibility="collapsed")
        nro = c_doc.text_input("N° Documento", key=f"d_nro_{i}")
        
        dom = st.text_input("Domicilio", key=f"d_dom_{i}")
        
        demandados_data.append({"nombre": nombre, "tipo": tipo, "nro": nro, "domicilio": dom})

    c_btn3, c_btn4 = st.columns(2)
    if c_btn3.button("➕ Otro Demandado", key="add_dem"): agregar_demandado()
    if c_btn4.button("➖ Quitar", key="del_dem"): quitar_demandado()

st.markdown('</div>', unsafe_allow_html=True)

# --- 8. BLOQUE 3: PROFESIONAL ---
st.markdown('<div class="data-card"><span class="card-header">🎓 3. Datos del Profesional</span>', unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1:
    nombre_abog = st.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
with cp2:
    mat_abog = st.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
st.markdown('</div>', unsafe_allow_html=True)

# --- 9. GENERAR ---
st.markdown("###")
c_vacio, c_boton, c_vacio2 = st.columns([1, 2, 1])

with c_boton:
    if st.button("✨ GENERAR DOCUMENTO WORD", type="primary", use_container_width=True):
        # Filtramos los vacíos
        actores_validos = [x for x in actores_data if x['nombre'].strip()]
        demandados_validos = [x for x in demandados_data if x['nombre'].strip()]
        
        if not actores_validos or not demandados_validos or not objeto_seleccionado:
            st.error("⚠️ Faltan datos: Complete al menos un Actor, un Demandado y el Objeto.")
        else:
            # Lógica
            if " - " in objeto_seleccionado:
                parts = objeto_seleccionado.rsplit(" - ", 1)
                cod_desc = parts[0]
                cod_nro = parts[1]
            else:
                cod_desc = objeto_seleccionado
                cod_nro = ""
            
            contexto = {
                'FUERO': fuero,
                'actor_nombre': "\n".join([x['nombre'] for x in actores_validos]),
                'actor_dni': "\n".join([x['dni'] for x in actores_validos]),
                'actor_domicilio': "\n".join([x['domicilio'] for x in actores_validos]),
                'demandado_nombre': "\n".join([x['nombre'] for x in demandados_validos]),
                'demandado_tipo_doc': "\n".join([x['tipo'] for x in demandados_validos]),
                'demandado_nro_doc': "\n".join([x['nro'] for x in demandados_validos]),
                'demandado_cuit': "\n".join([x['nro'] for x in demandados_validos]),
                'demandado_domicilio': "\n".join([x['domicilio'] for x in demandados_validos]),
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
                    fname = f"Ingreso_{actores_validos[0]['nombre'].replace(' ', '_')[:10]}.docx"
                    st.success("✅ ¡Documento generado!")
                    st.download_button("📥 DESCARGAR", data=bio, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Falta la plantilla .docx")

# --- FOOTER ---
st.markdown('<div class="footer">Estudio Molina & Asociados</div>', unsafe_allow_html=True)
