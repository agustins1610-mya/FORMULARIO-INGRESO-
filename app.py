import io
import os
import re
from datetime import datetime

import streamlit as st
from docxtpl import DocxTemplate
from fpdf import FPDF

# -----------------------------
# 1) CONFIGURACIÓN DE PÁGINA
# -----------------------------
st.set_page_config(
    page_title="Sistema de Demandas",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# 2) CÓDIGOS (tu dict completo)
# -----------------------------
CODIGOS_RAW = {
    # ... (SIN CAMBIOS) ...
}

# -----------------------------
# 3) UTILIDADES
# -----------------------------
PLANTILLA_DOCX = "formulario ingreso demanda.docx"

def safe_filename(text: str, maxlen: int = 40) -> str:
    """Sanitiza para nombres de archivo (Windows-friendly)."""
    if not text:
        return "NN"
    text = text.strip()
    text = re.sub(r"[^\w\s.-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text).strip("_")
    return text[:maxlen] or "NN"

def normalizar_monto(m: str) -> str:
    if not m:
        return "INDETERMINADO"
    m = m.strip()
    return m if m else "INDETERMINADO"

def init_state_list(key: str) -> None:
    if key not in st.session_state or not isinstance(st.session_state[key], list) or len(st.session_state[key]) == 0:
        st.session_state[key] = [{"id": 0}]

def add_row(key: str) -> None:
    st.session_state[key].append({"id": len(st.session_state[key])})

def remove_row(key: str) -> None:
    if len(st.session_state[key]) > 1:
        st.session_state[key].pop()

@st.cache_data(show_spinner=False)
def codigos_ordenados(codigos: dict) -> list[str]:
    return sorted([f"{k} - {v}" for k, v in codigos.items()])

def split_codigo(seleccion: str) -> tuple[str, str]:
    if " - " in seleccion:
        return seleccion.split(" - ", 1)
    return "", seleccion

def validar_datos(actores: list[dict], demandados: list[dict]) -> tuple[bool, str]:
    if not actores:
        return False, "Debe consignar al menos un Actor (Nombre)."
    # Si querés endurecer: exigir DNI y domicilio del primer actor
    if not actores[0].get("nombre"):
        return False, "El primer Actor debe tener Nombre."
    if not demandados:
        # No siempre es obligatorio, pero usualmente sí
        return False, "Debe consignar al menos un Demandado (Nombre)."
    return True, ""

def build_word_context(datos: dict) -> dict:
    actores = datos.get("actores", [])
    demandados = datos.get("demandados", [])

    return {
        "FUERO": datos.get("fuero", ""),
        "actor_nombre": "\n".join([x.get("nombre", "") for x in actores]),
        "actor_dni": "\n".join([x.get("dni", "") for x in actores]),
        "actor_domicilio": "\n".join([x.get("domicilio", "") for x in actores]),
        "demandado_nombre": "\n".join([x.get("nombre", "") for x in demandados]),
        "demandado_tipo_doc": "\n".join([x.get("tipo", "") for x in demandados]),
        "demandado_nro_doc": "\n".join([x.get("nro", "") for x in demandados]),
        "demandado_domicilio": "\n".join([x.get("domicilio", "") for x in demandados]),
        "datos_abogado": datos.get("abogado", ""),
        "código_matricula": datos.get("matricula", ""),
        "codigo_nro": datos.get("cod_nro", ""),
        "codigo_desc": datos.get("cod_desc", ""),
        "monto": datos.get("monto", ""),
        "fecha": datos.get("fecha", ""),
    }

# -----------------------------
# 4) CSS / TEMA
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    tema = st.radio("Apariencia", ["Claro (Clásico)", "Oscuro (Moderno)"], index=0)
    st.markdown("---")
    st.info("ℹ️ Generador de formularios oficiales.")

if tema == "Claro (Clásico)":
    css_variables = """
        --bg-app: #F5F7FA; --bg-card: #FFFFFF; --text-main: #1A1A1A;
        --primary: #1B263B; --accent: #C5A065; --input-bg: #FFFFFF;
        --input-text: #000000; --input-border: #333333; --card-border: #E2E8F0;
    """
else:
    css_variables = """
        --bg-app: #0F172A; --bg-card: #1E293B; --text-main: #E2E8F0;
        --primary: #38BDF8; --accent: #C5A065; --input-bg: #334155;
        --input-text: #FFFFFF; --input-border: #475569; --card-border: #334155;
    """

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    :root {{ {css_variables} }}
    [data-testid="stAppViewContainer"] {{ background-color: var(--bg-app); font-family: 'Inter', sans-serif; color: var(--text-main); }}
    [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    [data-testid="stSidebar"] {{ background-color: var(--bg-card); border-right: 1px solid var(--card-border); }}
    input[type="text"], input[type="number"], .stTextInput input, div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important; color: var(--input-text) !important;
        border: 1px solid var(--input-border) !important; border-radius: 6px !important; min-height: 45px !important;
    }}
    div[data-baseweb="select"] span {{ color: var(--input-text) !important; }}
    ul[data-baseweb="menu"] {{ background-color: var(--input-bg) !important; }}
    li[data-baseweb="option"] {{ color: var(--input-text) !important; }}
    .stTextInput label, .stSelectbox label, h1, h2, h3, h4, p {{ color: var(--text-main) !important; }}
    .data-card {{
        background-color: var(--bg-card); padding: 25px; border-radius: 12px;
        border: 1px solid var(--card-border); box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }}
    .card-title {{
        font-size: 1.1rem; font-weight: 700; color: var(--primary);
        border-bottom: 2px solid var(--accent); padding-bottom: 8px; margin-bottom: 20px; display: inline-block;
    }}
    hr.separator {{ border: 0; border-top: 1px dashed var(--input-border); opacity: 0.3; margin: 20px 0; }}
    div.stButton > button {{ border-radius: 6px; font-weight: 600; border: none; transition: 0.2s; }}
    .footer {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: var(--bg-card); border-top: 1px solid var(--card-border);
        text-align: center; padding: 12px; font-size: 14px; font-weight: 600;
        color: var(--text-main); opacity: 0.9; z-index: 999;
    }}
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# 5) PDF
# -----------------------------
class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        pass

    def generar_formulario(self, datos: dict):
        self.add_page()
        self.set_auto_page_break(False)

        fuero = datos.get("fuero", "")

        # ENCABEZADO
        self.set_font("Arial", "", 8)
        self.set_xy(10, 10)
        self.cell(60, 4, "ANEXO RESOLUCIÓN Nº 231.", 0, 1)
        self.cell(60, 4, "DISTRITO JUDICIAL DEL NORTE", 0, 1)
        self.cell(60, 4, "CIRCUNSCRIPCIÓN ORÁN", 0, 1)
        self.cell(60, 4, "PODER JUDICIAL DE LA PROVINCIA DE SALTA", 0, 1)
        self.cell(60, 4, f"MESA DISTRIBUIDORA DE EXPEDIENTES {fuero}", 0, 1)

        # TITULO
        self.set_xy(10, 35)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "FORMULARIO PARA INGRESO DE DEMANDAS", 0, 1, "C")

        # Expediente
        self.set_xy(150, 20)
        self.set_font("Arial", "", 10)
        self.cell(40, 6, "EXPEDIENTE Nº .................", 0, 1)

        # Helpers para tomar hasta 3 (formulario)
        actores = (datos.get("actores") or [])[:3]
        demandados = (datos.get("demandados") or [])[:3]

        # 1. ACTORES
        y_start = 50
        self.set_xy(10, y_start)
        self.set_font("Arial", "B", 10)
        self.cell(10, 8, "1", 1, 0, "C")
        self.cell(180, 8, "ACTORES", 1, 1, "L")

        self.set_font("Arial", "", 9)
        self.cell(70, 6, "APELLIDO Y NOMBRE", 1, 0, "C")
        self.cell(70, 6, "Domicilio Real", 1, 0, "C")
        self.cell(20, 6, "Tipo Doc", 1, 0, "C")
        self.cell(30, 6, "Número", 1, 1, "
