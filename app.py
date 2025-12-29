import streamlit as st
from datetime import datetime
import io
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Demandas - Estudio Molina", page_icon="⚖️", layout="wide")

# --- 2. BASE DE DATOS DE CÓDIGOS (EXTRAÍDA DEL PDF) ---
CODIGOS_RAW = {
    # CIVIL Y COMERCIAL - ORDINARIOS
    "100": "ACCION CONFESORIA - C", "101": "ACCION DE REDUCCION - C", "102": "ACCION SUBROGATORIA - C",
    "103": "COLACION - C", "104": "CUMPLIMIENTO DE CONTRATO - C", "112": "ORDINARIO - C",
    "113": "PETICION DE HERENCIA - C", "115": "REDARGUCION - C", "117": "REIVINDICACION - C",
    "118": "REPETICION DE PAGO - C", "120": "RESTITUCION DE BIENES - C", "121": "SIMULACION - C",
    "227": "NULIDAD DE ACTO JURIDICO - C", "255": "ACCION REVOCATORIA - C", "256": "ACCION NEGATORIA - C",
    "266": "FILIACION POST MORTEM - C", "292": "ACCION DE DESLINDE - C",
    
    # CIVIL Y COMERCIAL - SUMARIOS
    "122": "ACCION MERAMENTE DECLARATIVA - C", "124": "ACCION REDHIBITORIA - C", "126": "CANCELACION DE HIPOTECA - C",
    "127": "CANCELACION DE PRENDA - C", "131": "PAGO POR CONSIGNACION - C", "133": "DIVISION DE CONDOMINIO - C",
    "134": "ESCRITURACION - C", "135": "FIJACION DE PLAZO - C", "137": "MEDIANERIA - C",
    "141": "PRESCRIPCION ADQUISITIVA DE DERECHOS REALES - C", "145": "RENDICION DE CUENTAS - C",
    "147": "RESCISION O RESOLUCION DE CONTRATO - C", "148": "RESTITUCION MUEBLE EN COMODATO - C",
    "150": "TERCERIA - C", "240": "COBRO DE PESOS - C", "243": "SUMARIO - C",
    "295": "ACCION DE SUSPENSIÓN DEL CUMPLIMIENTO DEL CONTRATO - C",

    # DAÑOS Y PERJUICIOS
    "293": "DAÑOS Y PERJUICIOS - C",

    # SUMARISIMOS Y OTROS CIVILES
    "125": "AMPARO - C", "175": "SUMARISIMO O VERBAL - C", "236": "HABEAS CORPUS - C",
    "251": "HABEAS DATA - C", "296": "INTERDICTOS - C", "297": "ACCIONES DERIVADAS DEL MEDIO AMBIENTE - C",
    "123": "ACCION POSESORIA - C", "282": "ACCIONES LEY DE DEFENSA DEL CONSUMIDOR - C",
    "237": "DESALOJO - C", "183": "ACCIONES DE PROPIEDAD HORIZONTAL - C",

    # EJECUCIONES CIVILES
    "165": "EJECUCION DE SENTENCIA - C", "259": "EJECUCION DE HONORARIOS - C",

    # SUCESORIOS
    "191": "HERENCIA VACANTE - C", "192": "SUCESORIO - C", "245": "ADMINISTRACION - C",
    "269": "SUCESION TESTAMENTARIA - C", "290": "SUCESION AB INTESTATO - C",

    # MEDIDAS CAUTELARES Y VOLUNTARIOS (CIVIL)
    "244": "MEDIDA CAUTELAR - C", "294": "ACCION PREVENTIVA - C",
    "196": "BENEFICIO DE LITIGAR SIN GASTOS - C", "197": "CANCELACION DE TITULO - C",
    "198": "COPIA Y/O RENOVACION DE TITULO - C", "199": "EMBARGO VOLUNTARIO - C", "201": "HOMOLOGACION - C",
    "203": "INSCRIPCION DE MARTILLERO - C", "238": "INFORMACION SUMARIA - C", "241": "AUTORIZACION JUDICIAL - C",
    "242": "INSCRIPCION JUDICIAL - C", "258": "EXPEDICION DE NUEVAS COPIAS DE ESCRITURA PUBLICA - C",
    
    # PROCEDIMIENTOS ESPECIALES Y VARIOS (CIVIL)
    "156": "DILIGENCIAS PREPARATORIAS - C", "189": "MENSURA Y DESLINDE - C", "291": "PRUEBA ANTICIPADA - C",
    "226": "OFICIO LEY 22172 - C", "234": "REGULACION DE HONORARIOS - C", "235": "EXHORTO - C",
    "249": "VARIOS - C", "253": "RECURSO DE APELACION DIRECTA - C", "246": "INHIBITORIA - C",
    "277": "OFICIO - CIVIL - C", "223": "QUEJA - C", "815": "INAPLICABILIDAD DE LA LEY - C",
    "215": "INCIDENTES - C", "268": "PIEZAS PERTENECIENTES - C", "298": "INCIDENTE DE OPOSICION A EXCUSACION - C",
    "299": "INCIDENTE DE RECUSACION - C",

    # VIOLENCIA FAMILIAR Y DE GENERO
    "901": "VIOLENCIA FAMILIAR - V", "902": "VIOLENCIA DE GENERO - V", "903": "AMPARO - V",
    "904": "HABEAS CORPUS - V", "905": "HABEAS DATA - V", "906": "OFICIO - EXORTO - V",
    "907": "REGULACION DE HONORARIOS - V", "908": "EJECUCION DE HONORARIOS - V",
    "909": "BENEFICIO DE LITIGAR SIN GASTOS - V", "914": "EJECUCION DE SENTENCIA - V",
    "910": "QUEJA - V", "911": "INCIDENTES - V", "912": "PIEZAS PERTENECIENTES - V", "913": "NO VIOLENCIA - V",

    # PERSONAS Y FAMILIA
    "602": "ALIMENTOS - F", "709": "ALIMENTOS VOLUNTARIOS - F", "720": "DIVORCIO UNILATERAL - F",
    "721": "DIVORCIO BILATERAL - F", "674": "SUMARIO - F", "657": "RESTITUCION DE MENOR - F",
    "677": "EXCLUSION DEL HOGAR - F", "620": "AMPARO - F", "632": "NULIDAD DE MATRIMONIO - F",
    "653": "HABEAS CORPUS - F", "668": "ORDINARIO - F", "669": "HABEAS DATA - F",
    "722": "LIQUIDACION DE LA COMUNIDAD - F", "723": "LIQUIDACION DEL REGIMEN PATRIMONIAL - F",
    "724": "PRIVACION DE LA RESPONSABILIDAD PARENTAL - F", "725": "SUSPENSIÓN DE LA RESPONSABILIDAD PARENTAL - F",
    
    # VOLUNTARIOS (FAMILIA)
    "606": "CURATELA - F", "613": "GUARDA JUDICIAL - F", "616": "TUTELA - F",
    "622": "AUTORIZACION PARA CONTRAER MATRIMONIO - F", "624": "HOMOLOGACION - F", "626": "INSCRIPCION JUDICIAL - F",
    "630": "RECTIFICACION DE PARTIDA - F", "634": "AUSENCIA CON PRESUNCION DE FALLECIMIENTO - F",
    "635": "BENEFICIO DE LITIGAR SIN GASTOS - F", "636": "CAMBIO DE NOMBRE Y SEXO - F",
    "648": "DECLARACION DE INHABILITACION - F", "659": "HOMOLOGACION ACUERDOS MEDIACION - F",
    "661": "AUTORIZACION JUDICIAL - F", "670": "AUSENCIA POR DESAPARICION FORZADA - F",
    "707": "GUARDA CON FINES DE ADOPCION - F", "731": "CESE DE LA RESTRICCION DE LA CAPACIDAD - F",
    "732": "AUSENCIA SIMPLE - F", "733": "ACCIONES REFERIDAS AL NOMBRE - F",
    "736": "ACCION DECLARACION ADOPTABILIDAD - F", "737": "CAMBIO DE NOMBRE - F",
    "625": "INFORMACION SUMARIA - F", "730": "CONTROL DE LEGALIDAD - F",
    "619": "PROTECCION DE PERSONAS - F", "604": "ADOPCION - F",
    
    # CAPACIDAD Y FILIACION (FAMILIA)
    "715": "PROCESO DE RESTRICCION DE LA CAPACIDAD - F", "741": "REVISION SENTENCIA RESTRICCION CAPACIDAD - F",
    "611": "FILIACION - F", "645": "RECONOCIMIENTO DE FILIACION - F", "697": "IMPUGNACION DE FILIACION - F",
    "738": "NULIDAD DE FILIACION - F",

    # CUIDADO Y COMUNICACION (FAMILIA)
    "726": "REGIMEN DE COMUNICACION - F", "727": "MODIFICACION DEL REGIMEN DE COMUNICACION - F",
    "728": "CUIDADO PERSONAL - F", "729": "MODIFICACION DEL CUIDADO PERSONAL - F",

    # OTROS FAMILIA
    "651": "EJECUCION DE HONORARIOS - F", "652": "EJECUCION DE SENTENCIA - F",
    "665": "INCIDENTE - F", "672": "TERCERIA - F", "681": "AUMENTO DE CUOTA ALIMENTARIA - F",
    "682": "DISMINUCION DE CUOTA ALIMENTARIA - F", "683": "MODIFICACION DE CUOTA ALIMENTARIA - F",
    "684": "CESE DE CUOTA ALIMENTARIA - F", "686": "INCIDENTE DE LEVANTAMIENTO DE EMBARGO - F",
    "690": "PIEZAS PERTENECIENTES - F", "705": "PIEZAS PERTENECIENTES (VIOL FLIAR) - F",
    "734": "INCIDENTE DE OPOSICION A EXCUSACION - F", "735": "INCIDENTE DE RECUSACION - F",
    "656": "QUEJA - F", "644": "MEDIDAS CAUTELARES - F", "654": "REGULACION DE HONORARIOS - F",
    "658": "OFICIO EXHORTO - F", "662": "PRUEBA ANTICIPADA - F", "664": "DILIGENCIAS PREPARATORIAS - F",
    "676": "VARIOS - F", "693": "EMBARGO PREVENTIVO - F",
    "739": "VIOLENCIA FAMILIAR - F", "740": "VIOLENCIA DE GENERO - F",

    # PROCESOS EJECUTIVOS
    "394": "DILIGENCIAS PREPARATORIAS - E", "350": "EJECUCION DE SENTENCIA - E", "351": "SECUESTRO ARTICULO 39 - E",
    "352": "OFICIO LEY 22172 S/EJECUTIVOS - E", "353": "EJECUCION DE HONORARIOS - E", "354": "PREPARACION VIA EJECUTIVA - E",
    "355": "EJECUTIVO - E", "356": "EJECUCION PRENDARIA - E", "357": "EJECUCION HIPOTECARIA - E",
    "358": "EJECUCION FISCAL - E", "360": "CREDITO POR EXPENSAS COMUNES - E", "362": "AMPARO - E",
    "363": "HABEAS DATA - E", "364": "HABEAS CORPUS - E", "382": "DEMANDA DE JUICIO ARBITRAL - E",
    "390": "MEDIDA CAUTELAR EJECUTIVO - E", "391": "MEDIDA CAUTELAR PREPARA VIA - E",
    "361": "MEDIDA CAUTELAR - E", "377": "EMBARGO PREVENTIVO - E", "365": "TERCERIA - E",
    "366": "BENEFICIO DE LITIGAR SIN GASTOS - E", "367": "INCIDENTE - E", "368": "PIEZAS PERTENECIENTES - E",
    "380": "INCIDENTE DE OPOSICION A EXCUSACION - E", "381": "INCIDENTE DE RECUSACION - E", "376": "QUEJA - E",

    # MINAS
    "951": "MANIFESTACION DESCUBRIMIENTO CANTERA - M", "952": "MANIFESTACION DESCUBRIMIENTO MINA - M",
    "953": "SOLICITUD CATEO 1º Y 2º CATEGORIA - M", "954": "SERVIDUMBRE - M", "955": "DEMASIA - M",
    "956": "ESTABLECIMIENTO FIJO - M", "957": "COMERCIAL DE REGISTRO - M", "958": "QUEJA - M",
    "959": "OTROS - M", "960": "NULIDAD - M", "961": "VARIOS - M", "962": "REGULACION DE HONORARIOS - M",
    "963": "SUMARIO CESION DE CUOTAS SOCIALES - M", "964": "INCIDENTES (MINAS) - M",

    # CONCURSOS Y QUIEBRAS
    "564": "CONCURSO PREVENTIVO - Q", "471": "ACCION DECLARATIVA (CONCURSO) - Q", "480": "CONCURSO PREV. POR CONVERSION - Q",
    "592": "MEDIDAS CAUTELARES CONCURSO PREV - Q", "402": "ACCION DE INEFICACIA CONCURSAL - Q",
    "406": "REVOCATORIA ORDINARIA - Q", "408": "SIMULACION - Q", "409": "ACCION DE RESPONSABILIDAD - Q",
    "410": "DILIGENCIAS PREPARATORIAS - Q", "413": "MEDIDAS CAUTELARES QUIEBRA - Q", "509": "QUIEBRA DIRECTA - Q",
    "512": "QUIEBRA INDIRECTA - Q", "513": "PEDIDO DE EXTENSION DE QUIEBRA - Q", "542": "ACCION DECLARATIVA (QUIEBRA) - Q",
    "579": "PRUEBA ANTICIPADA (QUIEBRAS) - Q", "423": "FIDEICOMISO LEY 25284 - Q",
    "407": "DISOLUCION DE SOCIEDAD - Q", "411": "NULIDAD DE ASAMBLEA - Q", "414": "RECONOCIMIENTO SOCIEDAD DE HECHO - Q",
    "425": "AMPARO - Q", "428": "DILIGENCIAS PREPARATORIAS - Q", "432": "NULIDAD DECISION ADMINISTRADORES - Q",
    "435": "NULIDAD TRANSFERENCIA PARTE SOCIAL - Q", "436": "NULIDAD SUSCRIPCON DE CAPITAL - Q",
    "439": "RENDICION DE CUENTAS - Q", "442": "MEDIDAS CAUTELARES - Q", "459": "INTERVENCION Y ADM JUDICIAL - Q",
    "484": "CONVOCATORIA DE ASAMBLEA - Q", "486": "EXCLUSION DE SOCIO - Q", "500": "EXAMEN DE LIBRO POR SOCIO - Q",
    "536": "HABEAS CORPUS - Q", "551": "HABEAS DATA - Q", "580": "PRUEBA ANTICIPADA (SOCIEDADES) - Q",
    "585": "INFORMACION SUMARIA - Q", "586": "HOMOLOGACION - Q", "803": "NULIDAD SOCIEDAD O COOPERATIVA - Q",
    "809": "NULIDAD DECISION ASAMBLEA - Q", "812": "ACCION DE REMOCION - Q", "813": "ACCION DE RESPONSABILIDAD - Q",
    "814": "IMPUGNACION ASAMBLEA - Q", "443": "SUCESORIO - Q", "452": "EJECUTIVOS - Q", "479": "LABORALES - Q",
    "481": "CIVILES - Q", "515": "INCIDENTES - Q", "568": "PIEZAS PERTENECIENTES - Q", "572": "CONCURSO ESPECIAL - Q",
    "573": "INCIDENTE DE VERIFICACION - Q", "574": "INCIDENTE DE REVISION - Q", "575": "INCIDENTE OPOSICION EXCUSACION - Q",
    "576": "INCIDENTE DE RECUSACION - Q", "577": "INCIDENTE DE PRONTO PAGO - Q", "578": "INCIDENTE DE INVESTIGACION - Q",
    "588": "INCIDENTE REMOCIÓN SÍNDICO - Q", "589": "INCIDENTE EXCLUSIÓN BIEN QUIEBRA - Q", "523": "QUEJA - Q",
    "438": "EJECUCION DE HONORARIOS - Q", "440": "EJECUCION DE SENTENCIA - Q", "526": "OFICIO LEY 22172 - Q",
    "478": "BENEFICIO DE LITIGAR SIN GASTOS - Q", "590": "PEDIDO DE PROPIA QUIEBRA - Q",
    "591": "PEDIDO QUIEBRA POR ACREEDOR - Q", "593": "LIQUIDACION JUDICIAL FIDEICOMISO - Q"
}

# --- 3. CLASE PDF QUE DIBUJA EL FORMULARIO EXACTO (Res. 231) ---
class PDF(FPDF):
    def header(self):
        # No usamos header automático para controlar posición absoluta
        pass

    def footer(self):
        # Pie de página solicitado
        self.set_y(-15)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(50, 50, 50)
        texto = "Creado por Agustín Salas Estudio Molina & Asociados | Orán, Salta - Belgrano N° 517 Orán - 3878 413039"
        self.cell(0, 10, texto, 0, 0, 'C')

    def generar_formulario(self, datos):
        self.add_page()
        self.set_auto_page_break(False)
        
        # --- ENCABEZADO ---
        self.set_font('Arial', '', 8)
        self.set_xy(10, 10)
        self.cell(60, 4, "ANEXO RESOLUCIÓN Nº 231.", 0, 1)
        self.cell(60, 4, "DISTRITO JUDICIAL DEL NORTE", 0, 1)
        self.cell(60, 4, "CIRCUNSCRIPCIÓN ORÁN", 0, 1)
        self.cell(60, 4, "PODER JUDICIAL DE LA PROVINCIA DE SALTA", 0, 1)
        self.cell(60, 4, "MESA DISTRIBUIDORA DE EXPEDIENTES LABORAL", 0, 1)
        
        # Título Grande
        self.set_xy(10, 35)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, "FORMULARIO PARA INGRESO DE DEMANDAS", 0, 1, 'C')
        
        # Expediente Nro (Arriba a la derecha)
        self.set_xy(150, 20)
        self.set_font('Arial', '', 10)
        self.cell(40, 6, "EXPEDIENTE Nº .................", 0, 1)

        # --- 1. ACTORES ---
        y_start = 50
        self.set_xy(10, y_start)
        self.set_font('Arial', 'B', 10)
        self.cell(10, 8, "1", 1, 0, 'C')
        self.cell(180, 8, "ACTORES", 1, 1, 'L')
        
        # Cabecera Tabla Actores
        self.set_font('Arial', '', 9)
        self.cell(70, 6, "APELLIDO Y NOMBRE", 1, 0, 'C')
        self.cell(70, 6, "Domicilio Real", 1, 0, 'C')
        self.cell(20, 6, "Tipo Doc", 1, 0, 'C')
        self.cell(30, 6, "Número", 1, 1, 'C')
        
        # Filas Actores (Dibujamos 3 filas fijas como el formulario)
        for i in range(3):
            # Recuperar datos si existen
            nom = datos['actores'][i]['nombre'] if i < len(datos['actores']) else ""
            dom = datos['actores'][i]['domicilio'] if i < len(datos['actores']) else ""
            dni = datos['actores'][i]['dni'] if i < len(datos['actores']) else ""
            
            self.cell(70, 8, str(nom), 1, 0, 'L')
            self.cell(70, 8, str(dom), 1, 0, 'L')
            self.cell(20, 8, "DNI" if nom else "", 1, 0, 'C')
            self.cell(30, 8, str(dni), 1, 1, 'C')

        # --- 2. DEMANDADOS ---
        self.ln(2)
        self.set_font('Arial', 'B', 10)
        self.cell(10, 8, "2", 1, 0, 'C')
        self.cell(180, 8, "DEMANDADOS", 1, 1, 'L')
        
        # Cabecera Tabla Demandados
        self.set_font('Arial', '', 9)
        self.cell(70, 6, "APELLIDO Y NOMBRE", 1, 0, 'C')
        self.cell(70, 6, "Domicilio Real", 1, 0, 'C')
        self.cell(20, 6, "Tipo", 1, 0, 'C')
        self.cell(30, 6, "Número", 1, 1, 'C')
        
        # Filas Demandados (3 filas fijas)
        for i in range(3):
            nom = datos['demandados'][i]['nombre'] if i < len(datos['demandados']) else ""
            dom = datos['demandados'][i]['domicilio'] if i < len(datos['demandados']) else ""
            nro = datos['demandados'][i]['nro'] if i < len(datos['demandados']) else ""
            tipo = datos['demandados'][i]['tipo'] if nom else ""
            
            self.cell(70, 8, str(nom), 1, 0, 'L')
            self.cell(70, 8, str(dom), 1, 0, 'L')
            self.cell(20, 8, str(tipo), 1, 0, 'C')
            self.cell(30, 8, str(nro), 1, 1, 'C')

        # --- 3. ABOGADO ---
        self.ln(2)
        self.set_font('Arial', 'B', 10)
        self.cell(10, 8, "3", 1, 0, 'C')
        self.cell(180, 8, "DATOS DEL ABOGADO", 1, 1, 'L')
        
        self.set_font('Arial', '', 9)
        self.cell(50, 6, "Nº MATRICULA", 1, 0, 'C')
        self.cell(140, 6, "APELLIDO Y NOMBRE", 1, 1, 'C')
        
        self.set_font('Arial', 'B', 10)
        self.cell(50, 8, datos['matricula'], 1, 0, 'C')
        self.cell(140, 8, datos['abogado'], 1, 1, 'L')

        # --- 4. OBJETO ---
        self.ln(2)
        self.set_font('Arial', 'B', 10)
        self.cell(10, 8, "4", 1, 0, 'C')
        self.cell(180, 8, "OBJETO DEL JUICIO", 1, 1, 'L')
        
        self.set_font('Arial', '', 9)
        self.cell(40, 6, "Nº CODIGO", 1, 0, 'C')
        self.cell(150, 6, "DESCRIPCION", 1, 1, 'C')
        
        self.set_font('Arial', 'B', 10)
        self.cell(40, 8, datos['cod_nro'], 1, 0, 'C')
        self.cell(150, 8, datos['cod_desc'], 1, 1, 'L')

        # --- 5. MONTO y 6. CONEXIDAD (Lado a lado) ---
        self.ln(2)
        # Monto
        self.cell(10, 8, "5", 1, 0, 'C')
        self.cell(30, 8, "MONTO:", 1, 0, 'L')
        self.cell(55, 8, datos['monto'], 1, 0, 'L') # Valor del monto
        
        # Conexidad
        self.cell(10, 8, "6", 1, 0, 'C')
        self.cell(30, 8, "CONEXIDAD:", 1, 0, 'L')
        self.cell(55, 8, "", 1, 1, 'L') # Espacio vacío para llenar a mano si hace falta

        # --- OBSERVACIONES ---
        self.ln(4)
        self.set_font('Arial', '', 9)
        self.cell(0, 5, "Observaciones: (consignar, si corresponde, alguna de las excepciones del Anexo Ac. 10.911)", 0, 1)
        self.rect(self.get_x(), self.get_y(), 190, 20) # Caja vacía grande
        self.ln(25)

        # --- FIRMA ---
        self.set_font('Arial', '', 10)
        self.cell(20, 10, f"Fecha: {datos['fecha']}", 0, 0)
        
        # Espacio para firma a la derecha
        self.set_xy(120, 230)
        self.cell(70, 5, ".......................................................", 0, 1, 'C')
        self.set_x(120)
        self.cell(70, 5, "FIRMA Y SELLO LETRADO", 0, 1, 'C')
        self.set_x(120)
        self.set_font('Arial', 'B', 9)
        self.cell(70, 5, datos['abogado'], 0, 1, 'C')
        self.set_x(120)
        self.cell(70, 5, f"M.P. {datos['matricula']}", 0, 1, 'C')

# --- 4. MEMORIA DE ESTADO ---
if 'actores' not in st.session_state: st.session_state.actores = [{"id": 0}]
if 'demandados' not in st.session_state: st.session_state.demandados = [{"id": 0}]

def agregar(k): st.session_state[k].append({"id": len(st.session_state[k])})
def quitar(k): 
    if len(st.session_state[k]) > 1: st.session_state[k].pop()

# --- 5. INTERFAZ VISUAL ---
st.markdown("<h2 style='text-align: center;'>⚖️ Generador de Carátulas - Estudio Molina</h2>", unsafe_allow_html=True)

col_datos, col_preview = st.columns([1, 1])

with col_datos:
    st.subheader("1. Partes")
    # Actores
    st.markdown("**Actores (Solicitantes)**")
    actores_data = []
    for i, _ in enumerate(st.session_state.actores):
        c1, c2, c3 = st.columns([2, 1, 1.5])
        nom = c1.text_input(f"Nombre Actor {i+1}", key=f"an_{i}")
        dni = c2.text_input("DNI", key=f"ad_{i}")
        dom = c3.text_input("Domicilio", key=f"am_{i}")
        actores_data.append({'nombre': nom, 'dni': dni, 'domicilio': dom})
    c_btn1, c_btn2 = st.columns(2)
    c_btn1.button("➕ Actor", on_click=agregar, args=('actores',))
    c_btn2.button("➖ Quitar", on_click=quitar, args=('actores',))

    st.markdown("---")
    # Demandados
    st.markdown("**Demandados**")
    demandados_data = []
    for i, _ in enumerate(st.session_state.demandados):
        c1, c2, c3, c4 = st.columns([2, 0.8, 1, 1.5])
        nom = c1.text_input(f"Nombre Demandado {i+1}", key=f"dn_{i}")
        tipo = c2.selectbox("Tipo", ["CUIT", "DNI"], key=f"dt_{i}", label_visibility="collapsed")
        nro = c3.text_input("N° Doc", key=f"dd_{i}")
        dom = c4.text_input("Domicilio", key=f"dm_{i}")
        demandados_data.append({'nombre': nom, 'tipo': tipo, 'nro': nro, 'domicilio': dom})
    c_btn3, c_btn4 = st.columns(2)
    c_btn3.button("➕ Demandado", on_click=agregar, args=('demandados',))
    c_btn4.button("➖ Quitar", on_click=quitar, args=('demandados',))

with col_preview:
    st.subheader("2. Datos del Juicio")
    
    # Preparamos la lista ordenada para el Selectbox
    lista_ordenada = sorted([f"{k} - {v}" for k, v in CODIGOS_RAW.items()])
    
    seleccion = st.selectbox("Objeto (Busque por código o nombre)", lista_ordenada)
    
    # Lógica para separar el número de la descripción
    if " - " in seleccion:
        cod_nro, cod_desc = seleccion.split(" - ", 1)
    else:
        cod_nro, cod_desc = "", seleccion
        
    monto = st.text_input("Monto ($)", "INDETERMINADO")
    
    st.markdown("---")
    st.subheader("3. Profesional")
    c_prof1, c_prof2 = st.columns(2)
    abogado = c_prof1.text_input("Abogado", "SALAS AGUSTÍN GABRIEL")
    matricula = c_prof2.text_input("Matrícula", "7093")

# --- 6. BOTÓN DE GENERACIÓN ---
st.markdown("###")
if st.button("✨ GENERAR FORMULARIO OFICIAL (PDF)", type="primary", use_container_width=True):
    
    # Preparamos el diccionario de datos
    datos_pdf = {
        'actores': [a for a in actores_data if a['nombre']],
        'demandados': [d for d in demandados_data if d['nombre']],
        'abogado': abogado,
        'matricula': matricula,
        'cod_nro': cod_nro,
        'cod_desc': cod_desc,
        'monto': monto,
        'fecha': datetime.now().strftime("%d/%m/%Y")
    }

    try:
        # Instanciamos el PDF y dibujamos
        pdf = PDF()
        pdf.generar_formulario(datos_pdf)
        
        # Guardar en memoria RAM
        buffer = io.BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        buffer.write(pdf_output)
        buffer.seek(0)
        
        st.success("✅ Formulario generado correctamente.")
        st.download_button(
            label="📥 DESCARGAR FORMULARIO PDF",
            data=buffer,
            file_name=f"Ingreso_Demanda_{datos_pdf['actores'][0]['nombre'] if datos_pdf['actores'] else 'NN'}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
