import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Demandas",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CLASE PARA EL PDF (Pie de página actualizado) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'FORMULARIO DE INGRESO DE DEMANDAS', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Posición a 1.5 cm del final
        self.set_y(-15)
        # Aumentamos tamaño a 10 para que sea más legible
        self.set_font('Arial', 'I', 10) 
        self.set_text_color(80, 80, 80) # Gris oscuro
        
        texto_pie = "Creado por Agustín Salas Estudio Molina & Asociados | Orán, Salta - Belgrano N° 517 Orán - 3878 413039"
        self.cell(0, 10, texto_pie, 0, 0, 'C')

# --- 2. GESTIÓN DE MEMORIA ---
if 'actores' not in st.session_state:
    st.session_state.actores = [{"id": 0}]
if 'demandados' not in st.session_state:
    st.session_state.demandados = [{"id": 0}]

def agregar_actor():
    st.session_state.actores.append({"id": len(st.session_state.actores)})
def quitar_actor():
    if len(st.session_state.actores) > 1: st.session_state.actores.pop()

def agregar_demandado():
    st.session_state.demandados.append({"id": len(st.session_state.demandados)})
def quitar_demandado():
    if len(st.session_state.demandados) > 1: st.session_state.demandados.pop()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    tema = st.radio("Apariencia", ["Claro (Clásico)", "Oscuro (Moderno)"], index=0)
    st.markdown("---")
    st.info("ℹ️ Sistema interno para generación de carátulas y escritos.")

# --- 4. LÓGICA DE ESTILOS (CSS) ---
# Nota: Usamos dobles llaves {{ }} en el CSS para evitar conflictos con Python
if tema == "Claro (Clásico)":
    css_variables = """
        --bg-app: #F5F7FA;
        --bg-card: #FFFFFF;
        --text-main: #1A1A1A;
        --primary: #1B263B;
        --accent: #C5A065;
        --input-bg: #FFFFFF;
        --input-text: #000000;
        --input-border: #333333;
        --card-border: #E2E8F0;
    """
else:
    css_variables = """
        --bg-app: #0F172A;
        --bg-card: #1E293B;
        --text-main: #E2E8F0;
        --primary: #38BDF8;
        --accent: #C5A065;
        --input-bg: #334155;
        --input-text: #FFFFFF;
        --input-border: #475569;
        --card-border: #334155;
    """

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    :root {{
        {css_variables}
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }}
    [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    [data-testid="stSidebar"] {{ background-color: var(--bg-card); border-right: 1px solid var(--card-border); }}

    input[type="text"], input[type="number"], .stTextInput input, div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 6px !important;
        min-height: 45px !important;
    }}
    div[data-baseweb="select"] span {{ color: var(--input-text) !important; }}
    ul[data-baseweb="menu"] {{ background-color: var(--input-bg) !important; }}
    li[data-baseweb="option"] {{ color: var(--input-text) !important; }}
    .stTextInput label, .stSelectbox label, h1, h2, h3, h4, p {{ color: var(--text-main) !important; }}

    .data-card {{
        background-color: var(--bg-card);
        padding: 25px;
        border-radius: 12px;
        border: 1px solid var(--card-border);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}
    .card-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--primary);
        border-bottom: 2px solid var(--accent);
        padding-bottom: 8px;
        margin-bottom: 20px;
        display: inline-block;
    }}
    hr.separator {{
        border: 0;
        border-top: 1px dashed var(--input-border);
        opacity: 0.3;
        margin: 20px 0;
    }}
    div.stButton > button {{
        border-radius: 6px;
        font-weight: 600;
        border: none;
        transition: 0.2s;
    }}
    
    /* --- FOOTER DE LA WEB MODIFICADO --- */
    .footer {{
        position: fixed; 
        bottom: 0; 
        left: 0; 
        width: 100%; 
        background-color: var(--bg-card);
        border-top: 1px solid var(--card-border); 
        text-align: center; 
        padding: 12px; 
        font-size: 14px; 
        font-weight: 600; 
        color: var(--text-main); 
        opacity: 0.9; 
        z-index: 999;
    }}
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# --- 5. CABECERA ---
st.markdown("<div style='text-align: center; margin-bottom: 30px;'>", unsafe_allow_html=True)
st.markdown("<h1>⚖️ Sistema de Ingreso de Demandas</h1>", unsafe_allow_html=True)
st.markdown("<p style='opacity:0.8;'>Gestión Jurídica Inteligente</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- 6. CONSTANTES ---
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

# --- 7. DATOS DEL EXPEDIENTE ---
st.markdown('<div class="data-card"><div class="card-title">📂 1. DATOS DEL EXPEDIENTE</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 2, 0.8])
with c1:
    fuero = st.selectbox("Fuero", ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"])
with c2:
    objeto_seleccionado = st.selectbox("Objeto del Juicio", LISTA_CODIGOS, index=None, placeholder="Seleccione...")
with c3:
    monto = st.text_input("Monto ($)", value="INDETERMINADO")
st.markdown('</div>', unsafe_allow_html=True)

# --- 8. PARTES ---
st.markdown('<div class="data-card"><div class="card-title">👥 2. PARTES INTERVINIENTES</div>', unsafe_allow_html=True)
col_izq, col_espacio, col_der = st.columns([1, 0.1, 1])

# ACTORES
with col_izq:
    st.markdown("#### 👤 Parte Actora")
    actores_data = []
    for i, _ in enumerate(st.session_state.actores):
        if i > 0: st.markdown('<hr class="separator">', unsafe_allow_html=True)
        st.caption(f"Solicitante #{i+1}")
        nombre = st.text_input(f"Apellido y Nombre", key=f"a_nom_{i}")
        c_dni, c_dom = st.columns([0.4, 0.6])
        dni = c_dni.text_input(f"DNI", key=f"a_dni_{i}")
        dom = c_dom.text_input(f"Domicilio Real", key=f"a_dom_{i}")
        actores_data.append({"nombre": nombre, "dni": dni, "domicilio": dom})
    c_b1, c_b2 = st.columns(2)
    if c_b1.button("➕ Actor", key="btn_add_actor"): agregar_actor()
    if c_b2.button("➖ Quitar", key="btn_del_actor"): quitar_actor()

# DEMANDADOS
with col_der:
    st.markdown("#### 🛑 Parte Demandada")
    demandados_data = []
    for i, _ in enumerate(st.session_state.demandados):
        if i > 0: st.markdown('<hr class="separator">', unsafe_allow_html=True)
        st.caption(f"Demandado #{i+1}")
        nombre = st.text_input(f"Nombre / Razón Social", key=f"d_nom_{i}")
        c_tipo, c_doc = st.columns([0.3, 0.7])
        tipo = c_tipo.selectbox("Tipo", ["CUIT", "DNI"], key=f"d_tipo_{i}", label_visibility="collapsed")
        nro = c_doc.text_input("N° Doc", key=f"d_nro_{i}")
        dom = st.text_input("Domicilio", key=f"d_dom_{i}")
        demandados_data.append({"nombre": nombre, "tipo": tipo, "nro": nro, "domicilio": dom})
    c_b3, c_b4 = st.columns(2)
    if c_b3.button("➕ Demandado", key="btn_add_demandado"): agregar_demandado()
    if c_b4.button("➖ Quitar", key="btn_del_demandado"): quitar_demandado()
st.markdown('</div>', unsafe_allow_html=True)

# --- 9. PROFESIONAL ---
st.markdown('<div class="data-card"><div class="card-title">🎓 3. DATOS DEL PROFESIONAL</div>', unsafe_allow_html=True)
cp1, cp2 = st.columns(2)
with cp1:
    nombre_abog = st.text_input("Abogado Firmante", value=ABOGADO_DEFECTO)
with cp2:
    mat_abog = st.text_input("Matrícula Profesional", value=MATRICULA_DEFECTO)
st.markdown('</div>', unsafe_allow_html=True)

# --- 10. GENERACIÓN Y DESCARGA (WORD Y PDF) ---
st.markdown("###")
st.markdown('<div style="text-align: center">', unsafe_allow_html=True)

# Botón principal para procesar datos
if st.button("✨ PROCESAR DATOS", type="primary", use_container_width=True):
    
    # 1. Validación
    actores_validos = [x for x in actores_data if x['nombre'].strip()]
    demandados_validos = [x for x in demandados_data if x['nombre'].strip()]
    
    if not actores_validos or not demandados_validos or not objeto_seleccionado:
        st.error("⚠️ Faltan datos: Complete al menos un Actor, un Demandado y el Objeto.")
    else:
        # 2. Preparar Datos
        if " - " in objeto_seleccionado:
            parts = objeto_seleccionado.rsplit(" - ", 1)
            cod_desc = parts[0]
            cod_nro = parts[1]
        else:
            cod_desc = objeto_seleccionado
            cod_nro = ""
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        fname_base = f"Ingreso_{actores_validos[0]['nombre'].replace(' ', '_')[:10]}"

        # --- A. GENERAR WORD (EXISTENTE) ---
        buffer_word = io.BytesIO()
        contexto = {
            'FUERO': fuero,
            'actor_nombre': "\n".join([x['nombre'] for x in actores_validos]),
            'actor_dni': "\n".join([x['dni'] for x in actores_validos]),
            'actor_domicilio': "\n".join([x['domicilio'] for x in actores_validos]),
            'demandado_nombre': "\n".join([x['nombre'] for x in demandados_validos]),
            'demandado_tipo_doc': "\n".join([x['tipo'] for x in demandados_validos]),
            'demandado_nro_doc': "\n".join([x['nro'] for x in demandados_validos]),
            'demandado_domicilio': "\n".join([x['domicilio'] for x in demandados_validos]),
            'datos_abogado': nombre_abog,
            'código_matricula': mat_abog,
            'codigo_nro': cod_nro,
            'codigo_desc': cod_desc,
            'monto': monto,
            'fecha': fecha_actual
        }
        
        plantilla = "formulario ingreso demanda.docx"
        word_ok = False
        if os.path.exists(plantilla):
            try:
                doc = DocxTemplate(plantilla)
                doc.render(contexto)
                doc.save(buffer_word)
                buffer_word.seek(0)
                word_ok = True
            except Exception as e:
                st.error(f"Error Word: {e}")
        else:
            st.warning("⚠️ No se encontró la plantilla .docx para generar el Word.")

        # --- B. GENERAR PDF (NUEVO) ---
        buffer_pdf = io.BytesIO()
        try:
            pdf = PDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # Título y Fecha
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Fecha: {fecha_actual}", 0, 1, 'R')
            pdf.ln(5)
            
            # Bloque Fuero y Objeto
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 8, f"FUERO: {fuero}", 1, 1, 'L', fill=True)
            pdf.cell(0, 8, f"OBJETO: {cod_desc} ({cod_nro})", 1, 1, 'L', fill=True)
            pdf.cell(0, 8, f"MONTO: {monto}", 1, 1, 'L', fill=True)
            pdf.ln(5)
            
            # Bloque Actores
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, "PARTE ACTORA (SOLICITANTES)", 0, 1, 'L')
            pdf.set_font("Arial", size=10)
            for act in actores_validos:
                texto_actor = f"- {act['nombre']} (DNI: {act['dni']}) - Dom: {act['domicilio']}"
                pdf.multi_cell(0, 6, texto_actor)
            pdf.ln(5)
            
            # Bloque Demandados
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, "PARTE DEMANDADA", 0, 1, 'L')
            pdf.set_font("Arial", size=10)
            for dem in demandados_validos:
                texto_dem = f"- {dem['nombre']} ({dem['tipo']}: {dem['nro']}) - Dom: {dem['domicilio']}"
                pdf.multi_cell(0, 6, texto_dem)
            pdf.ln(5)
            
            # Bloque Profesional
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, "PROFESIONAL INTERVINIENTE", 0, 1, 'L')
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 6, f"Abogado: {nombre_abog}", 0, 1)
            pdf.cell(0, 6, f"Matrícula: {mat_abog}", 0, 1)
            
            # Guardar en buffer
            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
            buffer_pdf.write(pdf_bytes)
            buffer_pdf.seek(0)
            pdf_ok = True
            
        except Exception as e:
            st.error(f"Error PDF: {e}")
            pdf_ok = False

        # --- MOSTRAR BOTONES DE DESCARGA ---
        st.success("✅ ¡Documentos listos!")
        col_d1, col_d2 = st.columns(2)
        
        if word_ok:
            col_d1.download_button(
                label="📥 Descargar WORD (.docx)",
                data=buffer_word,
                file_name=f"{fname_base}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        if pdf_ok:
            col_d2.download_button(
                label="📥 Descargar PDF (.pdf)",
                data=buffer_pdf,
                file_name=f"{fname_base}.pdf",
                mime="application/pdf"
            )

st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER DE LA WEB (TEXTO ACTUALIZADO Y MÁS GRANDE) ---
st.markdown(
    '<div class="footer">Creado por Agustín Salas Estudio Molina & Asociados | Orán, Salta - Belgrano N° 517 Orán - 3878 413039</div>', 
    unsafe_allow_html=True
)
