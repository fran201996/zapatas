import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

st.set_page_config(page_title='Diseño de zapata aislada', layout='wide')

# Add custom design before title
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f5f8fc; }
[data-testid="stSidebar"] { background: #eaf2fb; border-right: 1px solid #c8d9ec; }
[data-testid="stSidebar"] label { color: #174a7e !important; font-weight: 600; }
[data-testid="stSidebar"] input { background: #ffffff !important; border: 1px solid #8bb3d9 !important; border-radius: 8px !important; }
[data-testid="stDataFrame"] { border: 1px solid #8bb3d9; border-radius: 10px; overflow: hidden; }
div[data-testid="stExpander"] { border: 1px solid #b8cde3; border-radius: 8px; background: #ffffff; }
</style>
""", unsafe_allow_html=True)

st.title('DISEÑO DE ZAPATAS AISLADAS')
st.subheader('Datos del Proyecto')
col_proy1, col_proy2 = st.columns(2)
with col_proy1:
    nombre_proyecto = st.text_input('Nombre del Proyecto', value='Edificio Residencial San Martín')
with col_proy2:
    nombre_zapata = st.text_input('Etiqueta / Nombre de Zapata', value='Z-1')
st.markdown('---')
st.caption('Ingrese únicamente los datos de entrada; el programa desarrolla automáticamente los pasos del PDF.')

st.sidebar.header('Datos de entrada')
fc=st.sidebar.number_input("f'c [kgf/cm²]", value=210.0)
fy=st.sidebar.number_input('fy [kgf/cm²]', value=4200.0)
beta1=st.sidebar.number_input('β1', value=0.85)
phi_f=st.sidebar.number_input('ϕ flexión', value=0.90)
phi_v=st.sidebar.number_input('ϕ corte', value=0.85)
lcx=st.sidebar.number_input('Columna Lcx [cm]', value=45.0)
lcy=st.sidebar.number_input('Columna Lcy [cm]', value=45.0)
dbcol=st.sidebar.number_input('Acero columna [pulg]', value=1.0)
PD=st.sidebar.number_input('PD [tonf]', value=180.0)
PL=st.sidebar.number_input('PL [tonf]', value=120.0)
sc=st.sidebar.number_input('s/c [kgf/m²]', value=500.0)
gammat=st.sidebar.number_input('γt [kgf/m³]', value=1700.0)
hter=st.sidebar.number_input('h. terreno [cm]', value=20.0)
qadm=st.sidebar.number_input('qs=qadm [kgf/cm²]', value=2.50)
hpiso=st.sidebar.number_input('hpiso [cm]', value=10.0)
gammac=st.sidebar.number_input('γc [kgf/m³]', value=2400.0)
rec=st.sidebar.number_input('Recubrimiento [cm]', value=10.0)
db=st.sidebar.selectbox('Barra de flexión [pulg]', [0.5,0.625,0.75,0.875,1.0], index=2)

def ab(d):
    return math.pi*(d*2.54)**2/4

def calc(hz):
    d=hz-rec
    ldb1=0.08*(dbcol*2.54)*fy/math.sqrt(fc)
    ldb2=0.004*(dbcol*2.54)*fy
    ldb=max(ldb1,ldb2)
    qsn=qadm-hter*gammat/1000000-hz*gammac/1000000-hpiso*gammac/1000000-sc/10000
    if qsn <= 0:
        raise ValueError(f'La capacidad portante neta qsn = {qsn:.2f} kgf/cm² es menor o igual que cero. Revise los datos de qadm, γt, h.terreno, γc, hz, hpiso y s/c.')
    area=(PD+PL)*1000/qsn
    lado=math.ceil(math.sqrt(area)/10)*10
    qsact=(PD+PL)*1000/lado**2
    qsu=(1.4*PD+1.7*PL)*1000/lado**2
    xcorte=lado/2-lcx/2-d
    Vu=qsu*lado*max(xcorte,0)
    phiVc=phi_v*0.53*math.sqrt(fc)*lado*d
    A0=(lcx+d)*(lcy+d)
    b0=2*(lcx+d)+2*(lcy+d)
    Vup=qsu*(lado**2-A0)
    Vcp1=phi_v*0.27*(2+4)*math.sqrt(fc)*b0*d
    Vcp2=phi_v*1.1*math.sqrt(fc)*b0*d
    Vcp=min(Vcp1,Vcp2)
    xflex=lado/2-lcx/2
    Mu=0.5*qsu*lado*xflex**2
    A=phi_f*fy**2/(2*0.85*fc*lado)
    Bq=-phi_f*fy*d
    disc=max(Bq**2-4*A*Mu,0)
    Asreq=(-Bq-math.sqrt(disc))/(2*A)
    Asmin=0.0018*lado*hz
    As=max(Asreq,Asmin)
    separ=ab(db)*lado/As
    separ=min(separ,45,3*d)
    separ_adopt=max(5,math.floor(separ/5)*5)
    return locals()

try:
    r70=calc(70)
    hz=80 if r70['Vcp']<r70['Vup'] else 70
    r=calc(hz)
except ValueError as e:
    st.error(str(e))
    st.info('Con los datos del PDF, use: qadm=2.50 kgf/cm², γt=1700 kgf/m³, h.terreno=20 cm, γc=2400 kgf/m³, hpiso=10 cm y s/c=500 kgf/m².')
    st.stop()

st.subheader('Datos ingresados')
tabla_html = f'''<table style="width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border:1px solid #8bb3d9;border-radius:10px;background:white"><tr style="background:#1769aa;color:white"><th style="padding:11px;text-align:left">Dato</th><th style="padding:11px;text-align:left">Valor</th></tr>{''.join(f'<tr><td style="padding:10px;border-top:1px solid #d9e7f5;color:#174a7e;font-weight:600">{d}</td><td style="padding:10px;border-top:1px solid #d9e7f5">{v}</td></tr>' for d,v in [("f'c",f'{fc:.0f} kgf/cm²'),("fy",f'{fy:.0f} kgf/cm²'),("PD",f'{PD:.0f} tonf'),("PL",f'{PL:.0f} tonf'),("Columna",f'{lcx:.0f} × {lcy:.0f} cm'),("qadm",f'{qadm:.2f} kgf/cm²')])}</table>'''
st.markdown(tabla_html, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(['📊 Verificaciones & Fórmulas', '📐 Gráficos (Planta y 3D)', '📄 Exportar Reporte'])

with tab1:
    pasos=[
    ('1. Dimensionamiento del peralte',f"Ldb₁ = 0.08·db·fy/√f'c = {r['ldb1']:.2f} cm; Ldb₂ = 0.004·db·fy = {r['ldb2']:.2f} cm. Se adopta Ldb = {r['ldb']:.2f} cm.\n\nhz inicial = 70 cm; d = hz − recubrimiento = {r['d']:.2f} cm."),
    ('2. Capacidad portante neta',f"qsn = qadm − hterreno·γt/1000000 − hz·γc/1000000 − hpiso·γc/1000000 − s/c/10000\n\nqsn = {r['qsn']:.2f} kgf/cm²."),
    ('3. Dimensiones B y L',f"Área = (PD + PL)·1000/qsn = {r['area']:,.2f} cm².\nL calculado = √Área; se adopta zapata cuadrada B = L = {r['lado']:.0f} cm.\nqs.act = {r['qsact']:.2f} kgf/cm². ¿qs.act < qsn?: {'Sí' if r['qsact']<r['qsn'] else 'No'}."),
    ('4. Reacción amplificada',f"qsu = (1.4PD + 1.7PL)·1000/(B·L) = {r['qsu']:.2f} kgf/cm²."),
    ('5. Corte por flexión',f"x = L/2 − Lcx/2 − d = {r['xcorte']:.2f} cm.\nVu = {r['Vu']:,.2f} kgf.\nϕVc = {r['phiVc']:,.2f} kgf.\nResultado: {'CUMPLE' if r['phiVc']>=r['Vu'] else 'NO CUMPLE'}."),
    ('6. Punzonamiento',f"A₀ = {r['A0']:,.2f} cm²; b₀ = {r['b0']:.2f} cm.\nVup = {r['Vup']:,.2f} kgf.\nϕVcp₁ = {r['Vcp1']:,.2f} kgf; ϕVcp₂ = {r['Vcp2']:,.2f} kgf.\nSe adopta el menor: ϕVcp = {r['Vcp']:,.2f} kgf.\nResultado: {'CUMPLE' if r['Vcp']>=r['Vup'] else 'NO CUMPLE'}."),
    ('7–11. Revisión final',f"Como hz=70 cm {'no cumple punzonamiento' if r70['Vcp']<r70['Vup'] else 'cumple punzonamiento'}. Se adopta hz = {hz:.0f} cm y se recalculan qsn, dimensiones, corte y punzonamiento.\n\nResultado final de corte: {'CUMPLE' if r['phiVc']>=r['Vu'] else 'NO CUMPLE'}. Punzonamiento: {'CUMPLE' if r['Vcp']>=r['Vup'] else 'NO CUMPLE'}."),
    ('12. Diseño por flexión',f"x = {r['xflex']:.2f} cm; Mu = {r['Mu']:,.2f} kgf·cm.\nAs requerido = {r['Asreq']:.2f} cm²; As mínimo = {r['Asmin']:.2f} cm².\nAs adoptado = {r['As']:.2f} cm².\n\nAcero: Ø{db:g}\" @ {r['separ_adopt']:.0f} cm en ambas direcciones."),
    ]
    formulas = [
        [r"L_{db,1}=0.08d_b\frac{f_y}{\sqrt{f'_c}}", r"L_{db,2}=0.004d_bf_y", r"L_{db}=\max(L_{db,1},L_{db,2}),\qquad d=h_z-r"],
        [r"q_{sn}=q_{adm}-\frac{h_t\gamma_t+h_z\gamma_c+h_{piso}\gamma_c}{10^6}-\frac{s/c}{10^4}"],
        [r"A=\frac{1000(P_D+P_L)}{q_{sn}},\qquad B=L=\sqrt{A}", r"q_{act}=\frac{1000(P_D+P_L)}{BL}\leq q_{sn}"],
        [r"q_{su}=\frac{1000(1.4P_D+1.7P_L)}{BL}"],
        [r"x=\frac{L-L_{cx}}{2}-d",r"V_u=q_{su}B\max(x,0)",r"\phi V_c=\phi_v\,0.53\sqrt{f'_c}\,Bd\geq V_u"],
        [r"A_0=(L_{cx}+d)(L_{cy}+d)",r"b_0=2(L_{cx}+d)+2(L_{cy}+d)",r"V_{up}=q_{su}(BL-A_0)",r"\phi V_{cp,1}=\phi_v\,0.27(2+4)\sqrt{f'_c}\,b_0d",r"\phi V_{cp,2}=\phi_v\,1.1\sqrt{f'_c}\,b_0d",r"\phi V_{cp}=\min(\phi V_{cp,1},\phi V_{cp,2})\geq V_{up}"],
        [r"q_{act}\leq q_{sn},\qquad V_u\leq\phi V_c,\qquad V_{up}\leq\phi V_{cp}"],
        [r"x=\frac{L-L_{cx}}{2},\qquad M_u=\frac{q_{su}Bx^2}{2}",r"M_u=\phi_f A_s f_y\left(d-\frac{a}{2}\right),\qquad a=\frac{A_sf_y}{0.85f'_cB}",r"A_{s,min}=0.0018Bh_z,\qquad A_s=\max(A_{s,req},A_{s,min})",r"s=\frac{A_bB}{A_s}"]
    ]
    estados = [None, None, r['qsact'] <= r['qsn'], None,
               r['phiVc'] >= r['Vu'], r['Vcp'] >= r['Vup'],
               r['phiVc'] >= r['Vu'] and r['Vcp'] >= r['Vup'], None]
    import html
    for indice, (t, b) in enumerate(pasos):
        estado = estados[indice]
        fondo, borde = ('#dcecff','#1769aa') if estado is True else (('#fde2e2','#c62828') if estado is False else ('#dcecff','#1769aa'))
        etiqueta = ' — CUMPLE' if estado is True else (' — NO CUMPLE' if estado is False else '')
        contenido = html.escape(b).replace('\n', '<br>')
        razones = {2: ('La presión actuante supera la capacidad del suelo.', 'Aumente B y L o revise qadm y las cargas.'), 4: (f'Vu = {r["Vu"]:,.2f} kgf supera ϕVc = {r["phiVc"]:,.2f} kgf.', "Aumente hz, revise B, f'c o las cargas."), 5: (f'Vup = {r["Vup"]:,.2f} kgf supera ϕVcp = {r["Vcp"]:,.2f} kgf.', "Aumente hz, B y L, f'c o revise la columna."), 6: ('La revisión final no cumple.', 'Aumente hz o B y L y vuelva a verificar.')}
        extra = ''
        if estado is False and indice in razones:
            motivo, sugerencia = razones[indice]
            extra = f'<div style="background:#fff5f5;border:1px solid #e5a6a6;border-radius:6px;padding:12px;margin-top:14px"><b style="color:#b71c1c">¿Por qué no cumple?</b><br>{html.escape(motivo)}<br><br><b style="color:#1769aa">Sugerencia:</b><br>{html.escape(sugerencia)}</div>'
        st.markdown(f'<div style="background:{fondo};border-left:6px solid {borde};padding:18px 20px;border-radius:5px;margin:14px 0 10px;color:#243746"><h3 style="color:#243746;margin:0 0 14px">{html.escape(t)}{etiqueta}</h3><div style="line-height:1.7">{contenido}</div>{extra}</div>', unsafe_allow_html=True)
        with st.expander(f'Ver Fórmulas - {t.split(". ", 1)[-1]}', expanded=True):
            st.caption('Unidades: longitudes en cm; cargas PD y PL en tonf; presiones en kgf/cm²; pesos unitarios en kgf/m³.')
            explicaciones = [
                'Primero se calcula la longitud de desarrollo de las barras de la columna mediante dos expresiones. Se adopta el valor mayor porque garantiza un anclaje suficiente del acero dentro de la zapata. Luego se calcula d = hz − recubrimiento, que es la distancia desde la fibra comprimida hasta el centro del acero.',
                'La capacidad portante neta se obtiene restando a qadm los pesos del terreno, de la zapata, del piso y la sobrecarga. El factor 10⁶ convierte γ en kgf/m³ y alturas en centímetros a kgf/cm². Este valor será la presión disponible para dimensionar la zapata.',
                'Se calcula el área necesaria dividiendo la carga de servicio entre la presión neta admisible. Como la zapata es cuadrada, B = L = raíz cuadrada del área. Después se compara qs.act con qsn; la presión actuante debe ser menor o igual que la capacidad del suelo.',
                'Se obtiene la presión última del suelo usando la combinación de cargas 1.4PD + 1.7PL. Esta presión se utiliza en las verificaciones de corte, punzonamiento y flexión.',
                'Se determina la distancia desde la cara de la columna hasta la sección crítica de corte. Vu es el cortante que produce el suelo y ϕVc es la resistencia reducida del concreto. Cumple cuando ϕVc es mayor o igual que Vu.',
                'Para punzonamiento se calcula el área crítica A₀ y el perímetro crítico b₀ alrededor de la columna. Vup es el punzonamiento actuante. Se calculan dos resistencias según E.060 y se adopta la menor. Cumple cuando ϕVcp es mayor o igual que Vup.',
                'Se revisan nuevamente los resultados después de modificar el peralte. Si el punzonamiento con hz = 70 cm no cumple, se adopta hz = 80 cm y se recalculan qsn, B, L, qsu, corte y punzonamiento.',
                'El momento se calcula en la cara de la columna. Con Mu se obtiene As requerido mediante la ecuación de flexión. Luego se compara con As mínimo. Finalmente se calcula la separación de barras y se limita según la norma.'
            ]
            st.markdown(f'**Procedimiento:** {explicaciones[indice]}')
            significados = [
                'Ldb: longitud de desarrollo del acero. db: diámetro de barra. fy: fluencia del acero. f’c: resistencia del concreto. d: peralte efectivo.',
                'qsn: capacidad portante neta del suelo. qadm: capacidad admisible. γt: peso unitario del terreno. γc: peso unitario del concreto. s/c: sobrecarga.',
                'A: área requerida de la zapata. B y L: ancho y largo. PD: carga muerta. PL: carga viva. qs.act: presión actuante del suelo.',
                'qsu: presión última o amplificada del suelo, obtenida con la combinación 1.4PD + 1.7PL.',
                'x: distancia hasta la sección crítica. Vu: cortante actuante. ϕVc: resistencia reducida del concreto al corte. ϕ: factor de reducción.',
                'A₀: área encerrada por la sección crítica de punzonamiento. b₀: perímetro crítico. Vup: punzonamiento actuante. ϕVcp: resistencia reducida al punzonamiento.',
                'La revisión final confirma simultáneamente presión del suelo, corte por flexión y punzonamiento después de adoptar el peralte final.',
                'Mu: momento último. As: área de acero requerida. As mínimo: acero mínimo normativo. Ab: área de una barra. s: separación entre barras.'
            ]
            st.markdown(f'<div style=\"background:#eef6ff;border-left:4px solid #1769aa;padding:10px 14px;border-radius:6px;margin-bottom:12px\"><b>Significado de los símbolos:</b> {significados[indice]}</div>', unsafe_allow_html=True)
            st.markdown('**Fórmulas utilizadas:**')
            for formula in formulas[indice]:
                st.latex(formula)
    st.success(f"Zapata final: {r['lado']:.0f} × {r['lado']:.0f} cm; hz = {hz:.0f} cm; acero inferior Ø{db:g}\" @ {r['separ_adopt']:.0f} cm en ambas direcciones.")

with tab2:
    col_planta, col_3d = st.columns(2)
    with col_planta:
        st.subheader('Vista en Planta')
        fig_planta, ax = plt.subplots(figsize=(6, 6))
        Bm = r['lado']/100; CmX = lcx/100; CmY = lcy/100; dm = r['d']/100
        ax.add_patch(Rectangle((-Bm/2,-Bm/2), Bm, Bm, facecolor='lightgray', edgecolor='black', linewidth=3, label='Zapata'))
        ax.add_patch(Rectangle((-(CmX+dm)/2,-(CmY+dm)/2), CmX+dm, CmY+dm, fill=False, edgecolor='blue', linestyle='--', linewidth=2, label='Sección crítica (d)'))
        ax.add_patch(Rectangle((-CmX/2,-CmY/2), CmX, CmY, facecolor='darkred', edgecolor='black', label='Columna'))
        ax.set_title(f'Vista en Planta: B = {r["lado"]:.0f} cm, L = {r["lado"]:.0f} cm')
        ax.set_xlabel('Ancho B (m)')
        ax.set_ylabel('Largo L (m)')
        ax.set_xlim(-Bm * 0.7, Bm * 0.7)
        ax.set_ylim(-Bm * 0.7, Bm * 0.7)
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, linestyle=':')
        ax.legend()
        st.pyplot(fig_planta, use_container_width=True)



    with col_3d:
        st.subheader('Vista en 3D Interactiva')

        B3 = r['lado'] / 100
        H3 = hz / 100
        CX3 = lcx / 100
        CY3 = lcy / 100
        HCOL = max(0.80, H3 * 1.5)

        def bloque(x0, x1, y0, y1, z0, z1, color, nombre, opacidad):
            return go.Mesh3d(
                x=[x0,x1,x1,x0,x0,x1,x1,x0], y=[y0,y0,y1,y1,y0,y0,y1,y1],
                z=[z0,z0,z0,z0,z1,z1,z1,z1],
                i=[0,0,4,4,0,0,1,1,2,2,3,3],
            j=[1,2,6,7,4,5,5,6,6,7,7,4],
            k=[2,3,5,6,5,1,6,2,7,3,4,0],
            color=color, opacity=opacidad, name=nombre, hovertext=nombre, hoverinfo='name'
            )

        fig = go.Figure()
        fig.add_trace(bloque(-B3/2,B3/2,-B3/2,B3/2,0,H3,'lightgray','Zapata',0.75))
        fig.add_trace(bloque(-CX3/2,CX3/2,-CY3/2,CY3/2,H3,H3+HCOL,'saddlebrown','Columna',0.95))
        # Líneas de cota principales
        for x1,y1,x2,y2,texto in [(-B3/2,-B3/2,B3/2,-B3/2,f'B = {r["lado"]:.0f} cm'),(B3/2,-B3/2,B3/2,B3/2,f'L = {r["lado"]:.0f} cm')]:
            fig.add_trace(go.Scatter3d(x=[x1,x2],y=[y1,y2],z=[0,0],mode='lines+text',text=['',texto],textposition='bottom center',line=dict(color='red',width=6),showlegend=False))
        fig.add_trace(go.Scatter3d(x=[B3/2,B3/2],y=[B3/2,B3/2],z=[0,H3],mode='lines+text',text=['',f'hz = {hz:.0f} cm'],textposition='middle right',line=dict(color='blue',width=6),showlegend=False))
        fig.update_layout(
            scene=dict(
                xaxis_title='Ancho B (m)', yaxis_title='Largo L (m)', zaxis_title='Altura (m)',
                aspectmode='cube',
                camera=dict(eye=dict(x=1.35, y=1.35, z=1.05))
            ),
            height=420,
            margin=dict(l=0, r=0, b=0, t=10),
            showlegend=True,
            legend=dict(orientation='h')
        )
        st.plotly_chart(fig, use_container_width=True, config={'displaylogo': False})
        st.caption(f'Dimensiones mostradas: B = {r["lado"]:.0f} cm, L = {r["lado"]:.0f} cm, hz = {hz:.0f} cm; columna = {lcx:.0f} × {lcy:.0f} cm.')


with tab3:
    st.subheader('📄 Reporte de cálculo y Exportación PDF')
    st.markdown('<div style="background:#dcecff;border-left:6px solid #1769aa;padding:16px;border-radius:8px;margin-bottom:18px"><h3 style="margin:0;color:#174a7e">Memoria de cálculo de zapata aislada</h3><p style="margin:6px 0 0">Visualiza los pasos y descarga el reporte oficial en formato PDF con su cuadro resumen.</p></div>', unsafe_allow_html=True)
    
    # --- FUNCIÓN PARA GENERAR EL PDF ---
    def generar_pdf():
        def u(texto):
            tabla = str.maketrans({
                '₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9',
                '−':'-','–':'-','—':'-','·':'*','’':"'",'“':'"','”':'"',
                'ϕ':'phi','φ':'phi','γ':'gamma','β':'beta','√':'raiz ','≥':'>=','≤':'<=','≠':'!=',
            })
            texto = str(texto).translate(tabla)
            # Cualquier otro carácter raro se vuelve "?" en vez de romper el programa
            return texto.encode('latin-1', 'replace').decode('latin-1')

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'MEMORIA DE DISEÑO DE ZAPATA AISLADA', align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, u(f'Proyecto: {nombre_proyecto} | Elemento: {nombre_zapata}'), align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(5)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'CUADRO RESUMEN - DATOS DE DISEÑO Y RESULTADOS', new_x='LMARGIN', new_y='NEXT')

        datos_tabla = [
            ("Resistencia del concreto (f'c)", f"{fc:.0f} kgf/cm²"),
            ("Fluencia del acero (fy)", f"{fy:.0f} kgf/cm²"),
            ("Carga muerta (PD)", f"{PD:.0f} tonf"),
            ("Carga viva (PL)", f"{PL:.0f} tonf"),
            ("Capacidad admisible del suelo (qadm)", f"{qadm:.2f} kgf/cm²"),
            ("Dimensiones de columna", f"{lcx:.0f} × {lcy:.0f} cm"),
            ("Dimensiones finales de zapata (B × L)", f"{r['lado']:.0f} × {r['lado']:.0f} cm"),
            ("Peralte total (hz)", f"{hz:.0f} cm"),
            ("Peralte efectivo (d)", f"{r['d']:.2f} cm"),
            ("Acero de refuerzo adoptado", f"Ø{db:g}\" @ {r['separ_adopt']:.0f} cm"),
        ]

        pdf.set_fill_color(23, 105, 170)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(110, 7, ' Parámetro / Dato', border=1, align='L', fill=True, new_x='RIGHT', new_y='TOP')
        pdf.cell(80, 7, ' Valor Adoptado', border=1, align='L', fill=True, new_x='LMARGIN', new_y='NEXT')

        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        fill = False
        for k, v in datos_tabla:
            if fill:
                pdf.set_fill_color(240, 245, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.cell(110, 6, u(f' {k}'), border=1, align='L', fill=True, new_x='RIGHT', new_y='TOP')
            pdf.cell(80, 6, u(f' {v}'), border=1, align='L', fill=True, new_x='LMARGIN', new_y='NEXT')
            fill = not fill

        pdf.ln(8)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'DESARROLLO DE PASOS DE CÁLCULO', new_x='LMARGIN', new_y='NEXT')

        for t, b in pasos:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(23, 105, 170)
            pdf.cell(0, 6, u(t), new_x='LMARGIN', new_y='NEXT')
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, u(b.replace('\n', ' ')), new_x='LMARGIN', new_y='NEXT')
            pdf.ln(3)

        return bytes(pdf.output())

    # Botón para descargar el PDF en Streamlit
    pdf_bytes = generar_pdf()
    st.download_button(
        label='📥 Descargar Memoria de Cálculo en PDF',
        data=pdf_bytes,
        file_name=f'Memoria_Diseno_Zapata_{nombre_zapata}.pdf',
        mime='application/pdf',
        use_container_width=True
    )
        
    st.markdown('---')
        
    # Vista previa en pantalla de los pasos
    opcion = st.selectbox('🔎 Seleccione el paso que desea revisar', ['Reporte completo'] + [t for t,b in pasos])
    if opcion == 'Reporte completo':
        seleccion = pasos
    else:
        seleccion = [item for item in pasos if item[0] == opcion]
                
    for t, b in seleccion:
        st.markdown(f'<div style="background:white;border:1px solid #8bb3d9;border-left:6px solid #1769aa;border-radius:8px;padding:16px;margin:10px 0;box-shadow:0 2px 7px #d7e4f2"><h4 style="color:#174a7e;margin:0 0 8px">{t}</h4><div style="white-space:pre-wrap;line-height:1.65">{b}</div></div>', unsafe_allow_html=True)
