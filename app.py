import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import pandas as pd
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ingreso de Demandas",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. GESTIÓN DE ESTADO (Para agregar/quitar partes) ---
if 'actores' not in st.session_state:
    st.session_state.actores = [{"id": 0}] # Inicia con uno
if 'demandados' not in st.session_state:
    st.session_state.demandados = [{"id": 0}] # Inicia con uno

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

# --- 3. ESTILOS CSS (DISEÑO UNIFICADO) ---
# Forzamos un diseño limpio tipo "Papel Legal" para todo
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap');
    
    :root {
        --bg-app: #F5F7FA;
        --bg-card: #FFFFFF;
        --text-color: #1A1A1A;
        --primary: #1B263B;
        --accent: #C5A065;
        --border-input: #333333;
    }

    /* Fondo Global */
    [data-testid="stAppViewContainer"] {
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
    }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }

    /* ESTILO DE TODOS LOS INPUTS (Cajas blancas con borde negro) */
    input[type="text"], input[type="number"], .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid var(--border-input) !important;
        border-radius: 6px !important;
        height: 45px;
    }

    /* Títulos de los inputs (Labels) */
    .stTextInput label, .stSelectbox label {
        color: #1A1A1A !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    /* TARJETAS (Bloques Blancos) */
    .data-block {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    
    .section-header {
        color: var(--primary);
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 3px solid var(--accent);
        display: inline-block;
        margin-bottom: 20px;
        padding-bottom: 5px;
    }

    /* Separador visual dentro de las tarjetas */
    .item-separator {
        border-top: 1px dashed #CBD5E1;
        margin: 15px 0;
    }

    /* BOTONES */
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
        border: none;
        transition: 0.2s;
    }
    
    /* Botón Principal (Generar) */
    .primary-btn button {
        background: linear-gradient(135deg, #1B263B 0%, #2C3E50 100%) !important;
        color: white !important;
        padding: 15px 30px !important;
        font-size: 1.1rem !important;
        width: 100%;
        box-shadow: 0 4px 10px rgba(27, 38, 59, 0.3);
    }
    
    /* Botones de Agregar/Quitar (Pequeños) */
    .small-btn button {
        background-color: #E2E8F0 !important;
        color: #1B263B !important;
        font-size: 0.8rem !important;
        padding: 5px 10px !important;
        border: 1px solid #CBD5E1 !important;
    }

    /* Footer */
    .footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #FFFFFF; border-top: 1px solid #E2E8F0;
        text-align: center; padding: 10px; font-size: 12px; color: #64748B;
        z-index: 999;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. CABECERA ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color:#1B263B; margin-bottom: 5px;">⚖️ Ingreso de Demandas</h1>
        <p style="color:#64748B;">Estudio Molina & Asociados · Formulario Oficial</p>
    </div>
""", unsafe_allow_html=True)

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

# --- 6. DATOS DEL EXPEDIENTE ---
st.markdown('<div class="data-block"><div class="section-header">📂 1. Datos del Expediente</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.2, 2, 0.8])
with c1:
    fuero = st.selectbox("Fuero", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox("Objeto del Juicio", LISTA_CODIGOS, index=None, placeholder="Seleccione...")
with c3:
    monto = st.text_input("Monto ($)", value="INDETERMINADO")
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. PARTES (DISEÑO DINÁMICO MEJORADO) ---
# Aquí es donde ocurre la magia: Usamos Inputs normales en lugar de la tabla fea
st.markdown('<div class="data-block"><div class="section-header">👥 2. Partes Intervinientes</div>', unsafe_allow_html=True)

col_actor_main, col_spacer, col_demandado_main = st.columns([1, 0.1, 1])

# --- COLUMNA ACTOR ---
with col_actor_main:
    st.markdown("#### 👤 Parte Actora")
    
    # Contenedor para inputs
    actores_data = []
    for i, _ in enumerate(st.session_state.actores):
        if i > 0: st.markdown('<div class="item-separator"></div>', unsafe_allow_html=True)
        
        st.markdown(f"**Solicitante #{i+1}**")
        a_nom = st.text_input(f"Apellido y Nombre", key=f"act_nom_{i}", placeholder="Apellido y Nombres Completos")
        c_doc, c_dom = st.columns([0.4, 0.6])
        a_dni = c_doc.text_input(f"DNI", key=f"act_dni_{i}")
        a_dom = c_dom.text_input(f"Domicilio Real", key=f"act_dom_{i}")
        
        # Guardar en lista temporal
        actores_data.append({"nombre": a_nom, "dni": a_dni, "domicilio": a_dom})

    # Botones de control
    st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
    cb1, cb2 = st.columns(2)
    if cb1.button("➕ Agregar otro Actor"): agregar_actor()
    if cb2.button("➖ Quitar último"): quitar_actor()
    st.markdown("</div>", unsafe_allow_html=True)

# --- COLUMNA DEMANDADO ---
with col_demandado_main:
    st.markdown("#### 🛑 Parte Demandada")
    
    demandados_data = []
    for i, _ in enumerate(st.session_state.demandados):
        if i > 0: st.markdown('<div class="item-separator"></div>', unsafe_allow_html=True)
        
        st.markdown(f"**Demandado #{i+1}**")
        d_nom = st.text_input(f"Nombre / Razón Social", key=f"dem_nom_{i}")
        
        c_tipo, c_nro, c_dom = st.columns([0.25, 0.35, 0.4])
        d_tipo = c_tipo.selectbox("Tipo", ["CUIT", "DNI"], key=f"dem_tipo_{i}", label_visibility="collapsed")
        d_nro = c_nro.text_input("N° Doc", key=f"dem_nro_{i}", placeholder="N° Doc")
        d_dom = c_dom.text_input("Domicilio", key=f"dem_dom_{i}", placeholder="Domicilio")
        
        demandados_data.append({"nombre": d_nom, "tipo": d_tipo, "nro": d_nro, "domicilio": d_dom})

    st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
    cb3, cb4 = st.columns(2)
    if cb3.button("➕ Agregar otro Demandado"): agregar_demandado()
    if cb4.button("➖ Quitar último"): quitar_demandado()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 8. PROFESIONAL ---
st.markdown('<div class="data-block"><div class="section-header">🎓 3. Datos del Profesional</div>', unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1:
    nombre_abog = st.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
with cp2:
    mat_abog = st.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
st.markdown('</div>', unsafe_allow_html=True)

# --- 9. GENERACIÓN ---
st.markdown("###")
_, col_btn, _ = st.columns([1, 2, 1])

st.markdown("<div class='primary-btn'>", unsafe_allow_html=True)
with col_btn:
    if st.button("✨ GENERAR DOCUMENTO WORD"):
        # Filtrar datos vacíos
        actores_validos = [a for a in actores_data if a['nombre'].strip()]
        demandados_validos = [d for d in demandados_data if d['nombre'].strip()]
        
        if not actores_validos or not demandados_validos or not objeto_seleccionado:
            st.error("⚠️ Error: Complete al menos un Actor (Nombre), un Demandado (Nombre) y el Objeto.")
        else:
            # Lógica de códigos
            if " - " in objeto_seleccionado:
                parts = objeto_seleccionado.rsplit(" - ", 1)
                cod_desc = parts[0]
                cod_nro = parts[1]
            else:
                cod_desc = objeto_seleccionado
                cod_nro = ""
            
            # Preparar contexto juntando listas con saltos de línea
            contexto = {
                'FUERO': fuero,
                'actor_nombre': "\n".join([x['nombre'] for x in actores_validos]),
                'actor_dni': "\n".join([x['dni'] for x in actores_validos]),
                'actor_domicilio': "\n".join([x['domicilio'] for x in actores_validos]),
                'demandado_nombre': "\n".join([x['nombre'] for x in demandados_validos]),
                'demandado_tipo_doc': "\n".join([x['tipo'] for x in demandados_validos]),
                'demandado_nro_doc': "\n".join([x['nro'] for x in demandados_validos]),
                'demandado_cuit': "\n".join([x['nro'] for x in demandados_validos]), # Mapeo redundante por seguridad
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
                    st.download_button("📥 DESCARGAR AHORA", data=bio, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                except Exception as e:
                    st.error(f"Error técnico: {e}")
            else:
                st.error("Falta la plantilla .docx")
st.markdown("</div>", unsafe_allow_html=True)

# --- FOOTER ---
st.markdown('<div class="footer">Estudio Molina & Asociados | Orán, Salta</div>', unsafe_allow_html=True)
