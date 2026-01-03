Voy a entregarte un script completo, listo para copiar/pegar, incorporando: layout con tabs, validación en vivo, resumen ejecutivo, action bar inferior, mejoras CSS, botones consistentes y correcciones de bugs (incluida la variable mal escrita).


```python
# -*- coding: utf-8 -*-
"""
Sistema de Ingreso de Demandas (Streamlit)
Versión UI mejorada: tabs, validación en vivo, resumen ejecutivo, action bar fija,
estética consistente (CSS), y corrección de bug demandados_filtrtrados.
"""

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
    initial_sidebar_state="expanded",
)

# -----------------------------
# 2) CÓDIGOS (PEGÁ TU DICT COMPLETO)
# -----------------------------
CODIGOS_RAW = {
    # ... (PEGÁ ACÁ TU DICT REAL) ...
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
    return (text[:maxlen] or "NN").strip("_") or "NN"


def normalizar_monto(m: str) -> str:
    if not m:
        return "INDETERMINADO"
    m = m.strip()
    return m if m else "INDETERMINADO"


def init_state_list(key: str) -> None:
    if (
        key not in st.session_state
        or not isinstance(st.session_state[key], list)
        or len(st.session_state[key]) == 0
    ):
        st.session_state[key] = [{"id": 0}]


def add_row(key: str) -> None:
    st.session_state[key].append({"id": len(st.session_state[key])})


def remove_row(key: str) -> None:
    if len(st.session_state[key]) > 1:
        st.session_state[key].pop()


@st.cache_data(show_spinner=False)
def codigos_ordenados(codigos: dict) -> list[str]:
    """Devuelve lista ordenada de strings tipo '100 - ORDINARIO - C'."""
    opciones = []
    for k, v in (codigos or {}).items():
        if k is None or v is None:
            continue
        ks = str(k).strip()
        vs = str(v).strip()
        if not ks or not vs:
            continue
        opciones.append(f"{ks} - {vs}")
    return sorted(opciones)


def split_codigo(seleccion) -> tuple[str, str]:
    """Devuelve (codigo, descripcion) desde '100 - ORDINARIO - C'."""
    if not isinstance(seleccion, str):
        return "", ""
    s = seleccion.strip()
    if not s or s == "Seleccione...":
        return "", ""
    if " - " in s:
        a, b = s.split(" - ", 1)
        return a.strip(), b.strip()
    return "", s


def validar_datos(actores: list[dict], demandados: list[dict], seleccion: str) -> tuple[bool, str]:
    if not actores:
        return False, "Debe consignar al menos un Actor (Nombre)."
    if not (actores[0].get("nombre") or "").strip():
        return False, "El primer Actor debe tener Nombre."
    if not demandados:
        return False, "Debe consignar al menos un Demandado (Nombre)."
    if seleccion == "Seleccione..." or not seleccion:
        return False, "Debe seleccionar un Objeto del Juicio válido."
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
# 4) PDF
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

        self.set_font("Arial", "", 8)
        self.set_xy(10, 10)
        self.cell(60, 4, "ANEXO RESOLUCIÓN Nº 231.", 0, 1)
        self.cell(60, 4, "DISTRITO JUDICIAL DEL NORTE", 0, 1)
        self.cell(60, 4, "CIRCUNSCRIPCIÓN ORÁN", 0, 1)
        self.cell(60, 4, "PODER JUDICIAL DE LA PROVINCIA DE SALTA", 0, 1)
        self.cell(60, 4, f"MESA DISTRIBUIDORA DE EXPEDIENTES {fuero}", 0, 1)

        self.set_xy(10, 35)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "FORMULARIO PARA INGRESO DE DEMANDAS", 0, 1, "C")

        self.set_xy(150, 20)
        self.set_font("Arial", "", 10)
        self.cell(40, 6, "EXPEDIENTE Nº .................", 0, 1)

        actores = (datos.get("actores") or [])[:3]
        demandados = (datos.get("demandados") or [])[:3]

        y_start = 50
        self.set_xy(10, y_start)
        self.set_font("Arial", "B", 10)
        self.cell(10, 8, "1", 1, 0, "C")
        self.cell(180, 8, "ACTORES", 1, 1, "L")

        self.set_font("Arial", "", 9)
        self.cell(70, 6, "APELLIDO Y NOMBRE", 1, 0, "C")
        self.cell(70, 6, "Domicilio Real", 1, 0, "C")
        self.cell(20, 6, "Tipo Doc", 1, 0, "C")
        self.cell(30, 6, "Número", 1, 1, "C")

        for i in range(3):
            row = actores[i] if i < len(actores) else {}
            nom = row.get("nombre", "") or ""
            dom = row.get("domicilio", "") or ""
            dni = row.get("dni", "") or ""
            self.cell(70, 8, str(nom), 1, 0, "L")
            self.cell(70, 8, str(dom), 1, 0, "L")
            self.cell(20, 8, "DNI" if nom else "", 1, 0, "C")
            self.cell(30, 8, str(dni), 1, 1, "C")

        self.ln(2)
        self.set_font("Arial", "B", 10)
        self.cell(10, 8, "2", 1, 0, "C")
        self.cell(180, 8, "DEMANDADOS", 1, 1, "L")

        self.set_font("Arial", "", 9)
        self.cell(70, 6, "APELLIDO Y NOMBRE", 1, 0, "C")
        self.cell(70, 6, "Domicilio Real", 1, 0, "C")
        self.cell(20, 6, "Tipo", 1, 0, "C")
        self.cell(30, 6, "Número", 1, 1, "C")

        for i in range(3):
            row = demandados[i] if i < len(demandados) else {}
            nom = row.get("nombre", "") or ""
            dom = row.get("domicilio", "") or ""
            nro = row.get("nro", "") or ""
            tipo = row.get("tipo", "") if nom else ""
            self.cell(70, 8, str(nom), 1, 0, "L")
            self.cell(70, 8, str(dom), 1, 0, "L")
            self.cell(20, 8, str(tipo), 1, 0, "C")
            self.cell(30, 8, str(nro), 1, 1, "C")

        self.ln(2)
        self.set_font("Arial", "B", 10)
        self.cell(10, 8, "3", 1, 0, "C")
        self.cell(180, 8, "DATOS DEL ABOGADO", 1, 1, "L")
        self.set_font("Arial", "", 9)
        self.cell(50, 6, "Nº MATRICULA", 1, 0, "C")
        self.cell(140, 6, "APELLIDO Y NOMBRE", 1, 1, "C")
        self.set_font("Arial", "B", 10)
        self.cell(50, 8, str(datos.get("matricula", "")), 1, 0, "C")
        self.cell(140, 8, str(datos.get("abogado", "")), 1, 1, "L")

        self.ln(2)
        self.set_font("Arial", "B", 10)
        self.cell(10, 8, "4", 1, 0, "C")
        self.cell(180, 8, "OBJETO DEL JUICIO", 1, 1, "L")
        self.set_font("Arial", "", 9)
        self.cell(40, 6, "Nº CODIGO", 1, 0, "C")
        self.cell(150, 6, "DESCRIPCION", 1, 1, "C")
        self.set_font("Arial", "B", 10)
        self.cell(40, 8, str(datos.get("cod_nro", "")), 1, 0, "C")
        self.cell(150, 8, str(datos.get("cod_desc", "")), 1, 1, "L")

        self.ln(2)
        self.cell(10, 8, "5", 1, 0, "C")
        self.cell(30, 8, "MONTO:", 1, 0, "L")
        self.cell(55, 8, str(datos.get("monto", "")), 1, 0, "L")
        self.cell(10, 8, "6", 1, 0, "C")
        self.cell(30, 8, "CONEXIDAD:", 1, 0, "L")
        self.cell(55, 8, "", 1, 1, "L")

        self.ln(4)
        self.set_font("Arial", "", 9)
        self.cell(
            0,
            5,
            "Observaciones: (consignar, si corresponde, alguna de las excepciones del Anexo Ac. 10.911)",
            0,
            1,
        )
        self.rect(self.get_x(), self.get_y(), 190, 20)
        self.ln(25)

        self.set_font("Arial", "", 10)
        self.cell(20, 10, f"Fecha: {datos.get('fecha', '')}", 0, 0)
        self.set_xy(120, 230)
        self.cell(70, 5, ".......................................................", 0, 1, "C")
        self.set_x(120)
        self.cell(70, 5, "FIRMA Y SELLO LETRADO", 0, 1, "C")
        self.set_x(120)
        self.set_font("Arial", "B", 9)
        self.cell(70, 5, str(datos.get("abogado", "")), 0, 1, "C")
        self.set_x(120)
        self.cell(70, 5, f"M.P. {datos.get('matricula', '')}", 0, 1, "C")


# -----------------------------
# 5) ESTADO INICIAL
# -----------------------------
init_state_list("actores")
init_state_list("demandados")

# -----------------------------
# 6) SIDEBAR (CONFIG + AYUDA)
# -----------------------------
with st.sidebar:
    st.header("⚙️ Configuración")
    tema = st.radio("Apariencia", ["Claro (Clásico)", "Oscuro (Moderno)"], index=0)
    st.markdown("---")

    st.subheader("Acciones")
    csa1, csa2 = st.columns(2)

    def reset_form():
        # Resetea filas
        st.session_state.actores = [{"id": 0}]
        st.session_state.demandados = [{"id": 0}]
        # Resetea inputs conocidos (por prefijos de keys)
        for k in list(st.session_state.keys()):
            if k.startswith(("an_", "ad_", "am_", "dn_", "dt_", "dd_", "dm_")):
                del st.session_state[k]
        # Campos de expediente/profesional
        for k in ["fuero_sel", "objeto_sel", "monto_in", "abogado_in", "matricula_in"]:
            if k in st.session_state:
                del st.session_state[k]

    if csa1.button("🧹 Limpiar", use_container_width=True):
        reset_form()

    def cargar_ejemplo():
        reset_form()
        # Carga un ejemplo mínimo
        st.session_state["an_0"] = "PÉREZ, JUAN"
        st.session_state["ad_0"] = "12345678"
        st.session_state["am_0"] = "Av. Ejemplo 123 - Orán"
        st.session_state["dn_0"] = "ACME S.A."
        st.session_state["dt_0"] = "CUIT"
        st.session_state["dd_0"] = "30-00000000-0"
        st.session_state["dm_0"] = "Calle Empresa 456 - Orán"
        st.session_state["monto_in"] = "INDETERMINADO"
        st.session_state["abogado_in"] = "SALAS AGUSTÍN GABRIEL"
        st.session_state["matricula_in"] = "7093"
        st.session_state["fuero_sel"] = "CIVIL Y COMERCIAL"

    if csa2.button("🧪 Ejemplo", use_container_width=True):
        cargar_ejemplo()

    st.markdown("---")
    st.info(
        "Generación de formulario oficial (Word/PDF) para Mesa Distribuidora.\n\n"
        "Nota: el PDF incorpora hasta 3 actores y 3 demandados."
    )

# -----------------------------
# 7) CSS / TEMA (MEJORADO)
# -----------------------------
if tema == "Claro (Clásico)":
    css_variables = """
        --bg-app: #F5F7FA; --bg-card: #FFFFFF; --text-main: #111827;
        --primary: #1B263B; --accent: #C5A065; --input-bg: #FFFFFF;
        --input-text: #111827; --input-border: rgba(120,120,120,.35); --card-border: #E5E7EB;
        --muted: rgba(17,24,39,.70);
    """
else:
    css_variables = """
        --bg-app: #0B1220; --bg-card: #111B2E; --text-main: #E5E7EB;
        --primary: #38BDF8; --accent: #C5A065; --input-bg: #0F172A;
        --input-text: #E5E7EB; --input-border: rgba(148,163,184,.35); --card-border: rgba(148,163,184,.20);
        --muted: rgba(229,231,235,.72);
    """

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    :root {{ {css_variables} }}

    /* App shell */
    [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-app);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }}
    [data-testid="stHeader"] {{ background-color: rgba(0,0,0,0); }}
    [data-testid="stSidebar"] {{
        background-color: var(--bg-card);
        border-right: 1px solid var(--card-border);
    }}
    .block-container {{
        padding-top: 1.0rem;
        padding-bottom: 5.0rem; /* espacio para actionbar */
    }}

    /* Typography */
    h1, h2, h3, h4, p, label, span {{
        color: var(--text-main) !important;
    }}
    .muted {{ color: var(--muted); }}

    /* Cards */
    .data-card {{
        background-color: var(--bg-card);
        padding: 22px 22px 18px 22px;
        border-radius: 14px;
        border: 1px solid var(--card-border);
        box-shadow: 0 10px 20px rgba(0,0,0,0.06);
        margin-bottom: 18px;
    }}
    .card-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--primary);
        border-bottom: 2px solid rgba(197,160,101,.55);
        padding-bottom: 8px;
        margin-bottom: 16px;
        display: inline-block;
        letter-spacing: .2px;
    }}
    .badge {{
        display:inline-block;
        font-size: .75rem;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid var(--card-border);
        background: rgba(197,160,101,.12);
        color: var(--text-main);
        margin-left: 8px;
    }}
    hr.separator {{
        border: 0;
        border-top: 1px dashed var(--input-border);
        opacity: 0.5;
        margin: 14px 0;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 10px !important;
        min-height: 44px !important;
    }}
    div[data-baseweb="select"] span {{ color: var(--input-text) !important; }}
    ul[data-baseweb="menu"] {{ background-color: var(--input-bg) !important; }}
    li[data-baseweb="option"] {{ color: var(--input-text) !important; }}
    .stTextInput input:focus, div[data-baseweb="select"] > div:focus-within {{
        outline: 2px solid rgba(197,160,101,0.30) !important;
        border-color: rgba(197,160,101,0.55) !important;
        box-shadow: 0 0 0 3px rgba(197,160,101,0.10) !important;
    }}

    /* Buttons */
    div.stButton > button {{
        border-radius: 10px;
        font-weight: 650;
        border: none;
        transition: 0.15s ease;
        min-height: 44px;
    }}
    div.stButton > button:hover {{
        transform: translateY(-1px);
        filter: brightness(1.02);
    }}

    /* Tabs */
    button[data-baseweb="tab"] {{
        font-weight: 650;
    }}

    /* Action bar */
    .actionbar {{
        position: fixed;
        left: 0; right: 0; bottom: 0;
        padding: 12px 18px;
        background: color-mix(in srgb, var(--bg-card) 92%, transparent);
        border-top: 1px solid var(--card-border);
        backdrop-filter: blur(8px);
        z-index: 999;
    }}

    /* Hide Streamlit chrome */
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 8) CABECERA (BRAND HEADER)
# -----------------------------
st.markdown(
    """
    <div style="text-align:center; margin-bottom: 8px;">
        <h1 style="margin-bottom: 4px;">⚖️ Sistema de Ingreso de Demandas</h1>
        <div class="muted" style="font-size: 0.98rem;">
            Generación de formulario oficial (Word/PDF) para Mesa Distribuidora
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 9) TABS (UI PRINCIPAL)
# -----------------------------
tab_partes, tab_expediente, tab_prof, tab_resultados = st.tabs(
    ["👥 Partes", "📂 Expediente", "🎓 Profesional", "✅ Resultados"]
)

# Variables de trabajo (se definen globalmente para actionbar y generación)
actores_data: list[dict] = []
demandados_data: list[dict] = []

fuero = "CIVIL Y COMERCIAL"
seleccion = "Seleccione..."
cod_nro, cod_desc = "", ""
monto = "INDETERMINADO"
abogado = "SALAS AGUSTÍN GABRIEL"
matricula = "7093"


with tab_partes:
    st.markdown('<div class="data-card"><div class="card-title">👥 1. Partes<span class="badge">Carga mínima: Actor #1 y Demandado #1</span></div>', unsafe_allow_html=True)
    st.caption("Parte actora (hasta 3 para el formulario)")

    for i, _ in enumerate(st.session_state.actores):
        if i > 0:
            st.markdown('<hr class="separator">', unsafe_allow_html=True)

        st.markdown(f"<div class='muted' style='font-weight:650; margin-bottom:6px;'>Actor #{i+1}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([0.62, 0.38])

        nom = c1.text_input(
            "Nombre",
            key=f"an_{i}",
            placeholder="APELLIDO, NOMBRE",
            label_visibility="collapsed",
        )
        dni = c2.text_input(
            "DNI",
            key=f"ad_{i}",
            placeholder="DNI",
            label_visibility="collapsed",
        )
        dom = st.text_input(
            "Domicilio",
            key=f"am_{i}",
            placeholder="Domicilio real",
            label_visibility="collapsed",
        )

        actores_data.append(
            {
                "nombre": (nom or "").strip(),
                "dni": (dni or "").strip(),
                "domicilio": (dom or "").strip(),
            }
        )

    ca1, ca2 = st.columns(2)
    ca1.button("➕ Agregar actor", on_click=add_row, args=("actores",), use_container_width=True)
    ca2.button("➖ Quitar actor", on_click=remove_row, args=("actores",), use_container_width=True)

    st.markdown('<hr class="separator">', unsafe_allow_html=True)
    st.caption("Parte demandada (hasta 3 para el formulario)")

    for i, _ in enumerate(st.session_state.demandados):
        if i > 0:
            st.markdown('<hr class="separator">', unsafe_allow_html=True)

        st.markdown(f"<div class='muted' style='font-weight:650; margin-bottom:6px;'>Demandado #{i+1}</div>", unsafe_allow_html=True)

        c1, c2 = st.columns([0.65, 0.35])
        nom = c1.text_input(
            "Demandado",
            key=f"dn_{i}",
            placeholder="Razón social / Apellido y nombre",
            label_visibility="collapsed",
        )

        tipo = c2.selectbox(
            "Tipo",
            ["CUIT", "DNI"],
            key=f"dt_{i}",
            help="Seleccione tipo de identificación.",
        )

        c3, c4 = st.columns([0.35, 0.65])
        nro = c3.text_input(
            "Número",
            key=f"dd_{i}",
            placeholder="N°",
            label_visibility="collapsed",
        )
        dom = c4.text_input(
            "Domicilio",
            key=f"dm_{i}",
            placeholder="Domicilio real",
            label_visibility="collapsed",
        )

        demandados_data.append(
            {
                "nombre": (nom or "").strip(),
                "tipo": tipo,
                "nro": (nro or "").strip(),
                "domicilio": (dom or "").strip(),
            }
        )

    cd1, cd2 = st.columns(2)
    cd1.button("➕ Agregar demandado", on_click=add_row, args=("demandados",), use_container_width=True)
    cd2.button("➖ Quitar demandado", on_click=remove_row, args=("demandados",), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


with tab_expediente:
    st.markdown('<div class="data-card"><div class="card-title">📂 2. Expediente<span class="badge">Objeto y monto</span></div>', unsafe_allow_html=True)

    fuero = st.selectbox(
        "Fuero / Jurisdicción",
        ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"],
        key="fuero_sel",
        help="Seleccione el fuero para la Mesa Distribuidora.",
    )

    lista_ordenada = codigos_ordenados(CODIGOS_RAW)
    opciones_objeto = ["Seleccione..."] + (lista_ordenada or [])
    seleccion = st.selectbox(
        "Objeto del Juicio",
        opciones_objeto,
        key="objeto_sel",
        help="Debe seleccionar un código válido para generar documentos.",
    )
    cod_nro, cod_desc = split_codigo(seleccion)

    monto = st.text_input(
        "Monto reclamado ($)",
        value=st.session_state.get("monto_in", "INDETERMINADO"),
        key="monto_in",
        help="Si el monto es indeterminado, consignar 'INDETERMINADO'.",
    )
    monto = normalizar_monto(monto)

    # Vista previa breve (estética funcional)
    st.markdown('<hr class="separator">', unsafe_allow_html=True)
    st.markdown("<div class='muted' style='font-weight:650; margin-bottom:6px;'>Vista previa</div>", unsafe_allow_html=True)
    st.write(
        f"**Fuero:** {fuero}  \n"
        f"**Objeto:** {cod_nro or '—'} — {cod_desc or '—'}  \n"
        f"**Monto:** {monto}"
    )

    st.markdown("</div>", unsafe_allow_html=True)


with tab_prof:
    st.markdown('<div class="data-card"><div class="card-title">🎓 3. Profesional<span class="badge">Firma y matrícula</span></div>', unsafe_allow_html=True)

    abogado = st.text_input(
        "Abogado firmante",
        value=st.session_state.get("abogado_in", "SALAS AGUSTÍN GABRIEL"),
        key="abogado_in",
        help="Apellido y nombre tal como desea que figure en el formulario.",
    ).strip()

    matricula = st.text_input(
        "Matrícula",
        value=st.session_state.get("matricula_in", "7093"),
        key="matricula_in",
        help="Número de matrícula profesional.",
    ).strip()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# 10) VALIDACIÓN EN VIVO + ESTADO
# -----------------------------
actores_filtrados = [a for a in actores_data if (a.get("nombre") or "").strip()]
demandados_filtrados = [d for d in demandados_data if (d.get("nombre") or "").strip()]

ok_live, msg_live = validar_datos(actores_filtrados, demandados_filtrados, seleccion)

# Estado (badge textual)
estado_texto = "Listo para generar" if ok_live else "Borrador (incompleto)"
estado_detalle = "" if ok_live else msg_live

# -----------------------------
# 11) TAB RESULTADOS (BOTÓN + DESCARGAS)
# -----------------------------
with tab_resultados:
    st.markdown('<div class="data-card"><div class="card-title">✅ 4. Resultados<span class="badge">Word y PDF</span></div>', unsafe_allow_html=True)

    # Resumen ejecutivo
    actor_ppal = (actores_filtrados[0]["nombre"] if actores_filtrados else "—").strip() if actores_filtrados else "—"
    st.write(
        f"**Estado:** {estado_texto}  \n"
        f"**Actor principal:** {actor_ppal}  \n"
        f"**Fuero:** {fuero}  \n"
        f"**Objeto:** {cod_nro or '—'} — {cod_desc or '—'}  \n"
        f"**Monto:** {monto}"
    )
    if not ok_live:
        st.warning(estado_detalle)

    st.markdown('<hr class="separator">', unsafe_allow_html=True)

    # Generación dentro del tab Resultados
    generar = st.button("✨ GENERAR DOCUMENTOS", type="primary", use_container_width=True, disabled=not ok_live)

    if generar:
        # Validación final (por seguridad)
        ok, msg = validar_datos(actores_filtrados, demandados_filtrados, seleccion)
        if not ok:
            st.error(msg)
            st.stop()

        fecha = datetime.now().strftime("%d/%m/%Y")

        datos_comunes = {
            "actores": actores_filtrados,
            "demandados": demandados_filtrados,
            "abogado": abogado,
            "matricula": matricula,
            "cod_nro": cod_nro,
            "cod_desc": cod_desc,
            "monto": monto,
            "fuero": fuero,
            "fecha": fecha,
        }

        actor_base = safe_filename(actores_filtrados[0].get("nombre", "Actor"))
        demanda_base = safe_filename(cod_desc or cod_nro or "Objeto")
        base_name = f"{actor_base}_{demanda_base}_{datetime.now().strftime('%Y%m%d_%H%M')}"

        # A) WORD
        buffer_word = io.BytesIO()
        word_ok = False
        word_err = ""

        if os.path.exists(PLANTILLA_DOCX):
            try:
                doc = DocxTemplate(PLANTILLA_DOCX)
                doc.render(build_word_context(datos_comunes))
                doc.save(buffer_word)
                buffer_word.seek(0)
                word_ok = True
            except Exception as e:
                word_err = str(e)
        else:
            word_err = f"No se encuentra la plantilla DOCX: '{PLANTILLA_DOCX}'."

        # B) PDF
        buffer_pdf = io.BytesIO()
        pdf_ok = False
        pdf_err = ""

        try:
            pdf = PDF()
            pdf.generar_formulario(datos_comunes)
            pdf_output = pdf.output(dest="S").encode("latin-1", "replace")
            buffer_pdf.write(pdf_output)
            buffer_pdf.seek(0)
            pdf_ok = True
        except Exception as e:
            pdf_err = str(e)

        st.markdown("#### Descargas")
        cdl1, cdl2 = st.columns(2)

        with cdl1:
            if word_ok:
                st.success("Word generado correctamente.")
                st.download_button(
                    "⬇️ Descargar Word",
                    data=buffer_word,
                    file_name=f"{base_name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            else:
                st.error(f"Error generando Word: {word_err}")

        with cdl2:
            if pdf_ok:
                st.success("PDF generado correctamente.")
                st.download_button(
                    "⬇️ Descargar PDF",
                    data=buffer_pdf,
                    file_name=f"{base_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.error(f"Error generando PDF: {pdf_err}")

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# 12) ACTION BAR (RESUMEN FIJO)
# -----------------------------
count_act = len(actores_filtrados)
count_dem = len(demandados_filtrados)
obj_short = (cod_nro or "—")
estado_color = "✅" if ok_live else "⚠️"
actor_short = (actores_filtrados[0]["nombre"] if actores_filtrados else "—")

st.markdown(
    f"""
    <div class="actionbar">
      <div style="display:flex; gap:12px; align-items:center; justify-content:space-between;">
        <div style="font-size:.92rem; opacity:.92;">
          {estado_color} <b>{estado_texto}</b>
          &nbsp;&nbsp;|&nbsp;&nbsp; Actor: <b>{actor_short}</b>
          &nbsp;&nbsp;|&nbsp;&nbsp; Fuero: <b>{fuero}</b>
          &nbsp;&nbsp;|&nbsp;&nbsp; Objeto: <b>{obj_short}</b>
          &nbsp;&nbsp;|&nbsp;&nbsp; Actores: <b>{count_act}</b>
          &nbsp;&nbsp;|&nbsp;&nbsp; Demandados: <b>{count_dem}</b>
        </div>
        <div style="font-size:.86rem; opacity:.75;">
          {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
```
