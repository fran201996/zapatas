import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from fpdf import FPDF

# Configuración de la página
st.set_page_config(page_title="Diseño de Zapatas Aisladas", layout="wide")

# Estilos personalizados (CSS para tarjetas y colores)
st.markdown("""
    <style>
    .metric-card-success {
        background-color: #d4edda;
        border-left: 6px solid #28a745;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .metric-card-danger {
        background-color: #f8d7da;
        border-left: 6px solid #dc3545;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ENCABEZADO Y DATOS GENERALES
# ---------------------------------------------------------
st.title("DISEÑO DE ZAPATAS AISLADAS")

st.subheader("Datos del Proyecto")
col_p1, col_p2 = st.columns(2)
with col_p1:
    nombre_proyecto = st.text_input("Nombre del Proyecto", value="Edificio Residencial San Martín")
with col_p2:
    nombre_zapata = st.text_input("Etiqueta / Nombre de Zapata", value="Z-1")

st.markdown("---")

# ---------------------------------------------------------
# PANEL LATERAL DE INGRESO DE DATOS
# ---------------------------------------------------------
st.sidebar.header("⚙️ Parámetros de Entrada")

# 1. Datos de la Columna
st.sidebar.subheader("1. Columna")
cx = st.sidebar.number_input("Ancho de Columna (cx) [m]", value=0.40, step=0.05)
cy = st.sidebar.number_input("Largo de Columna (cy) [m]", value=0.40, step=0.05)
P_serv = st.sidebar.number_input("Carga Axial Servicio (P) [tn]", value=45.0, step=1.0)
P_ult = st.sidebar.number_input("Carga Axial Última (Pu) [tn]", value=63.0, step=1.0)
Mx_ult = st.sidebar.number_input("Momento Último X (Mux) [tn-m]", value=2.0, step=0.5)
My_ult = st.sidebar.number_input("Momento Último Y (Muy) [tn-m]", value=1.5, step=0.5)

# 2. Datos del Suelo
st.sidebar.subheader("2. Suelo")
q_adm = st.sidebar.number_input("Capacidad Admisible (q_adm) [kg/cm²]", value=1.50, step=0.10)
df = st.sidebar.number_input("Profundidad de Cimentación (Df) [m]", value=1.50, step=0.10)

# 3. Datos de Materiales
st.sidebar.subheader("3. Materiales")
fc = st.sidebar.number_input("f'c [kg/cm²]", value=210.0, step=10.0)
fy = st.sidebar.number_input("fy [kg/cm²]", value=4200.0, step=100.0)
rec = st.sidebar.number_input("Recubrimiento [m]", value=0.075, step=0.005)

# 4. Modificar / Propuesta de Zapata
st.sidebar.subheader("4. Dimensiones Propuestas de Zapata")
B = st.sidebar.number_input("Ancho Zapata (B) [m]", value=1.80, step=0.05)
L = st.sidebar.number_input("Largo Zapata (L) [m]", value=1.80, step=0.05)
hz = st.sidebar.number_input("Peralte Total (hz) [m]", value=0.50, step=0.05)

# ---------------------------------------------------------
# CÁLCULOS Y VERIFICACIONES
# ---------------------------------------------------------
d = hz - rec  # Peralte efectivo

# A. Presión del suelo
q_act = P_serv / (B * L * 10)  # Convertir a kg/cm² aprox
cumple_suelo = q_act <= q_adm

# B. Verificación por Punzonamiento
# Perímetro crítico
bo = 2 * (cx + d) + 2 * (cy + d)
Area_critica = (cx + d) * (cy + d)
Vu_punz = P_ult - (P_ult / (B * L)) * Area_critica
# Capacidad al corte por punzonamiento (NTE E.060 aprox en tn)
phi_v = 0.85
Vc_punz = phi_v * 0.53 * np.sqrt(fc) * (bo * 100) * (d * 100) / 1000
cumple_punzonamiento = Vu_punz <= Vc_punz

# C. Verificación por Flexión / Acero (Dirección X)
cantilever_x = (B - cx) / 2
Mu_x = (P_ult / (B * L)) * L * (cantilever_x**2) / 2
# Acero aproximado
As_req_x = (Mu_x * 10**5) / (0.9 * fy * 0.9 * d * 100)
As_min_x = 0.0018 * (L * 100) * (hz * 100)
As_dis_x = max(As_req_x, As_min_x)

# ---------------------------------------------------------
# PANELES PRINCIPALES (RESULTADOS & FÓRMULAS)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Verificaciones & Fórmulas", "📐 Gráficos (Planta y 3D)", "📄 Exportar Reporte"])

with tab1:
    st.subheader("Resultados de las Verificaciones")

    # Tarjeta 1: Presión en el Suelo
    class_suelo = "metric-card-success" if cumple_suelo else "metric-card-danger"
    estado_suelo = "CUMPLE" if cumple_suelo else "NO CUMPLE (Aumentar B x L)"
    st.markdown(f"""
    <div class="{class_suelo}">
        <h4>1. Pressión de Contacto sobre el Suelo: {estado_suelo}</h4>
        <p><b>Presión Actuante (q_act):</b> {q_act:.2f} kg/cm² | <b>Presión Admisible (q_adm):</b> {q_adm:.2f} kg/cm²</p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Ver Fórmulas - Presión en Suelo"):
        st.latex(r"q_{act} = \frac{P_{servicio}}{B \cdot L}")
        st.latex(r"q_{act} \le q_{adm}")

    # Tarjeta 2: Punzonamiento
    class_punz = "metric-card-success" if cumple_punzonamiento else "metric-card-danger"
    estado_punz = "CUMPLE" if cumple_punzonamiento else "NO CUMPLE (Aumentar peralte hz)"
    st.markdown(f"""
    <div class="{class_punz}">
        <h4>2. Verificación por Punzonamiento: {estado_punz}</h4>
        <p><b>Cortante Actuante (Vu):</b> {Vu_punz:.2f} tn | <b>Resistencia Concreto (ΦVc):</b> {Vc_punz:.2f} tn</p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Ver Fórmulas - Punzonamiento"):
        st.latex(r"b_o = 2(c_x + d) + 2(c_y + d)")
        st.latex(r"V_{u,punz} = P_u - q_u \cdot (c_x + d)(c_y + d)")
        st.latex(r"\phi V_c = \phi \cdot 0.53 \cdot \sqrt{f'c} \cdot b_o \cdot d")

    # Tarjeta 3: Flexión y Acero
    st.markdown(f"""
    <div class="metric-card-success">
        <h4>3. Diseño por Flexión (Dirección X)</h4>
        <p><b>Momento Último (Mu_x):</b> {Mu_x:.2f} tn-m | <b>Área de Acero (As):</b> {As_dis_x:.2f} cm²</p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Ver Fórmulas - Diseño por Flexión"):
        st.latex(r"M_u = q_u \cdot L \cdot \frac{x^2}{2}")
        st.latex(r"A_{s,min} = 0.0018 \cdot B \cdot h_z")

with tab2:
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Vista en Planta")
        fig_2d, ax = plt.subplots(figsize=(5, 5))
        # Zapata
        rect_z = plt.Rectangle((-B/2, -L/2), B, L, color='lightgray', ec='black', lw=2, label="Zapata")
        # Columna
        rect_c = plt.Rectangle((-cx/2, -cy/2), cx, cy, color='darkred', label="Columna")
        # Zona Crítica Punzonamiento
        rect_p = plt.Rectangle((-(cx+d)/2, -(cy+d)/2), cx+d, cy+d, fill=False, color='blue', linestyle='--', label="Sección Crítica (d)")

        ax.add_patch(rect_z)
        ax.add_patch(rect_p)
        ax.add_patch(rect_c)

        ax.set_xlim(-B*0.7, B*0.7)
        ax.set_ylim(-L*0.7, L*0.7)
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':')
        ax.legend(loc="upper right")
        st.pyplot(fig_2d)

    with col_g2:
        st.subheader("Vista en 3D Interactiva")
        # Generar bloques 3D con Plotly
        fig_3d = go.Figure()

        # Cubo Zapata
        fig_3d.add_trace(go.Mesh3d(
            x=[-B/2, B/2, B/2, -B/2, -B/2, B/2, B/2, -B/2],
            y=[-L/2, -L/2, L/2, L/2, -L/2, -L/2, L/2, L/2],
            z=[0, 0, 0, 0, hz, hz, hz, hz],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 5, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            opacity=0.5, color='gray', name='Zapata'
        ))

        # Cubo Columna
        h_col = 0.8
        fig_3d.add_trace(go.Mesh3d(
            x=[-cx/2, cx/2, cx/2, -cx/2, -cx/2, cx/2, cx/2, -cx/2],
            y=[-cy/2, -cy/2, cy/2, cy/2, -cy/2, -cy/2, cy/2, cy/2],
            z=[hz, hz, hz, hz, hz+h_col, hz+h_col, hz+h_col, hz+h_col],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 5, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            opacity=0.8, color='brown', name='Columna'
        ))

        fig_3d.update_layout(scene=dict(aspectmode='data'))
        st.plotly_chart(fig_3d, use_container_width=True)

with tab3:
    st.subheader("Generar PDF del Memoria de Cálculo")

    def crear_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "REPORTE DE CÁLCULO - ZAPATA AISLADA", ln=True, align='C')
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, f"Proyecto: {nombre_proyecto}", ln=True)
        pdf.cell(0, 8, f"Zapata: {nombre_zapata}", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "1. Parámetros Principales:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, f"- Dimensiones Columna: {cx} m x {cy} m", ln=True)
        pdf.cell(0, 6, f"- Dimensiones Zapata: {B} m x {L} m x {hz} m", ln=True)
        pdf.cell(0, 6, f"- Carga de Servicio (P): {P_serv} tn", ln=True)
        pdf.cell(0, 6, f"- Capacidad Suelo (q_adm): {q_adm} kg/cm2", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, "2. Resultados de Verificación:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, f"- Presión Actuante: {q_act:.2f} kg/cm2 | Estado: {'CUMPLE' if cumple_suelo else 'NO CUMPLE'}", ln=True)
        pdf.cell(0, 6, f"- Cortante Punzonamiento (Vu): {Vu_punz:.2f} tn / Capacidad (Phi_Vc): {Vc_punz:.2f} tn", ln=True)
        pdf.cell(0, 6, f"- Acero Requerido (Dir X): {As_dis_x:.2f} cm2", ln=True)

        return pdf.output(dest='S').encode('latin-1')

    pdf_bytes = crear_pdf()
    st.download_button(
        label="📥 Descargar Reporte en PDF",
        data=pdf_bytes,
        file_name=f"Reporte_{nombre_zapata}.pdf",
        mime="application/pdf"
    )