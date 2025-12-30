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
    """
    Devuelve lista ordenada de strings tipo '100 - ORDINARIO - C'.
    Robusto: ignora entradas con claves/valores no string o vacías.
    """
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
    """
    Devuelve (codigo, descripcion) a partir de un string tipo '100 - ORDINARIO - C'.
    Robusto: si seleccion es None u otro tipo, devuelve ("", "").
    """
    if not isinstance(seleccion, str):
        return "", ""
    seleccion = seleccion.strip()
    if not seleccion:
        return "", ""
    if " - " in seleccion:
        cod_nro, cod_desc = seleccion.split(" - ", 1)
        return cod_nro.strip(), cod_desc.strip()
    return "", seleccion


def validar_datos(actores: list[dict], demandados: list[dict]) -> tuple[bool, str]:
    if not actores:
        return False, "Debe consignar al menos un Actor (Nombre)."
    if not actores[0].get("nombre"):
        return False, "El primer Actor debe tener Nombre."
    if not demandados:
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
    #MainMenu, footer, header {{visibility: hidden;}}
    </style>
    """,
    unsafe_allow_html=True,
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

        # 2. DEMANDADOS
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

        # 3. ABOGADO
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

        # 4. OBJETO
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

        # 5. MONTO / 6. CONEXIDAD
        self.ln(2)
        self.cell(10, 8, "5", 1, 0, "C")
        self.cell(30, 8, "MONTO:", 1, 0, "L")
        self.cell(55, 8, str(datos.get("monto", "")), 1, 0, "L")
        self.cell(10, 8, "6", 1, 0, "C")
        self.cell(30, 8, "CONEXIDAD:", 1, 0, "L")
        self.cell(55, 8, "", 1, 1, "L")

        # OBSERVACIONES
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

        # FIRMA
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
# 6) ESTADO
# -----------------------------
init_state_list("actores")
init_state_list("demandados")

# -----------------------------
# 7) CABECERA
# -----------------------------
st.markdown("<div style='text-align: center; margin-bottom: 30px;'>", unsafe_allow_html=True)
st.markdown("<h1>⚖️ Sistema de Ingreso de Demandas</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# 8) INTERFAZ
# -----------------------------
col_izq, col_der = st.columns([1, 1])

with col_izq:
    st.markdown('<div class="data-card"><div class="card-title">👥 1. PARTES</div>', unsafe_allow_html=True)

    # Actores
    st.caption("Parte Actora (Solicitantes)")
    actores_data: list[dict] = []

    for i, _ in enumerate(st.session_state.actores):
        if i > 0:
            st.markdown('<hr class="separator">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.6, 0.4])
        nom = c1.text_input(f"Nombre #{i+1}", key=f"an_{i}")
        dni = c2.text_input(f"DNI #{i+1}", key=f"ad_{i}")
        dom = st.text_input(f"Domicilio #{i+1}", key=f"am_{i}")
        actores_data.append({"nombre": (nom or "").strip(), "dni": (dni or "").strip(), "domicilio": (dom or "").strip()})

    cb1, cb2 = st.columns(2)
    cb1.button("➕ Actor", on_click=add_row, args=("actores",), key="btn_add_a")
    cb2.button("➖ Quitar", on_click=remove_row, args=("actores",), key="btn_del_a")

    st.markdown('<hr class="separator">', unsafe_allow_html=True)

    # Demandados
    st.caption("Parte Demandada")
    demandados_data: list[dict] = []

    for i, _ in enumerate(st.session_state.demandados):
        if i > 0:
            st.markdown('<hr class="separator">', unsafe_allow_html=True)
        c1, c2 = st.columns([0.6, 0.4])
        nom = c1.text_input(f"Demandado #{i+1}", key=f"dn_{i}")
        tipo = c2.selectbox("Tipo", ["CUIT", "DNI"], key=f"dt_{i}", label_visibility="collapsed")
        c3, c4 = st.columns([0.4, 0.6])
        nro = c3.text_input(f"N° Doc #{i+1}", key=f"dd_{i}")
        dom = c4.text_input(f"Dom #{i+1}", key=f"dm_{i}")
        demandados_data.append(
            {"nombre": (nom or "").strip(), "tipo": tipo, "nro": (nro or "").strip(), "domicilio": (dom or "").strip()}
        )

    cb3, cb4 = st.columns(2)
    cb3.button("➕ Demandado", on_click=add_row, args=("demandados",), key="btn_add_d")
    cb4.button("➖ Quitar", on_click=remove_row, args=("demandados",), key="btn_del_d")

    st.markdown("</div>", unsafe_allow_html=True)

with col_der:
    st.markdown('<div class="data-card"><div class="card-title">📂 2. EXPEDIENTE</div>', unsafe_allow_html=True)

    fuero = st.selectbox(
        "Fuero / Jurisdicción",
        ["LABORAL", "CIVIL Y COMERCIAL", "PERSONAS Y FAMILIA", "VIOLENCIA FAMILIAR"],
    )

    lista_ordenada = codigos_ordenados(CODIGOS_RAW)
    if not lista_ordenada:
        st.error("No hay códigos cargados en CODIGOS_RAW. Verifique el diccionario.")
        st.stop()

    # Si querés permitir “sin seleccionar”, descomentá:
    # lista_ordenada = [""] + lista_ordenada

    seleccion = st.selectbox("Objeto del Juicio", lista_ordenada)
    cod_nro, cod_desc = split_codigo(seleccion)

    # Blindaje: si algo viene inválido, no seguimos
    if not cod_nro and not cod_desc:
        st.warning("Seleccione un objeto del juicio válido.")
        st.stop()

    monto = st.text_input("Monto Reclamado ($)", "INDETERMINADO")
    monto = normalizar_monto(monto)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="data-card"><div class="card-title">🎓 3. PROFESIONAL</div>', unsafe_allow_html=True)
    abogado = st.text_input("Abogado Firmante", "SALAS AGUSTÍN GABRIEL").strip()
    matricula = st.text_input("Matrícula", "7093").strip()
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# 9) GENERACIÓN
# -----------------------------
st.markdown("###")
if st.button("✨ GENERAR DOCUMENTOS", type="primary", use_container_width=True):
    actores_filtrados = [a for a in actores_data if a.get("nombre")]
    demandados_filtrados = [d for d in demandados_data if d.get("nombre")]

    ok, msg = validar_datos(actores_filtrados, demandados_filtrados)
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

    # Nombre base archivos
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

    # Resultados
    st.markdown("#### Resultados")
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
