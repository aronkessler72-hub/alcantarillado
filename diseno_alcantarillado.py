import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import plotly.graph_objects as go


# -----------------------------------------------------------------------------
# CONFIGURACION DE PAGINA Y ESTILOS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Alcantarillado Sanitario",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Consolas&family=Roboto+Mono:wght@500;700&display=swap');
    
    /* 1. Forzar tipografía en todo el cuerpo del DOM de Streamlit */
    html, body, [class*="st-"], [class*="css"], div, span, p, label, input, button, table, td, th {
        font-family: 'Consolas', 'Roboto Mono', 'Courier New', monospace !important;
    }
    
    /* 2. Forzar tipografía específica dentro de las tablas de datos (st.dataframe) */
    [data-testid="stDataFrame"] *, 
    [data-testid="stTable"] *,
    div[role="gridcell"], 
    div[role="columnheader"] {
        font-family: 'Consolas', 'Roboto Mono', 'Courier New', monospace !important;
    }

    /* 3. Ajuste de peso negrita opcional para los valores */
    div[role="gridcell"] {
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ENCABEZADO CON LOGOS Y DATOS PEQUEÑOS
# -----------------------------------------------------------------------------
col_logo_izq, col_titulo, col_logo_der = st.columns([1.5, 7, 1.5])

with col_logo_izq:
    st.image("logo_izquierda.png", use_container_width=True) 

with col_titulo:
    st.markdown("""
    <div style="
        background-color: #8B0000;
        color: white;
        padding: 12px 15px;
        border: 2px solid #5A0000;
        text-align: center;
        border-radius: 4px;
        margin-bottom: 20px;
    ">
        <div style="font-size: 20px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px;">
            SISTEMA DE ALCANTARILLADO SANITARIO
        </div>
        <div style="font-size: 12px; font-weight: 700; letter-spacing: 1px; color: #E0E0E0; text-transform: uppercase;">
            CÁLCULO HIDRÁULICO
        </div>
        <hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.3); margin: 8px 0;">
        <div style="font-size: 9.5px; font-weight: 400; line-height: 1.3; color: #F0F0F0; opacity: 0.9;">
            POR: Condori Bustincio, Norka Guadalupe 240852 &nbsp;|&nbsp; 
            CURSO: Abastecimiento de Agua y Alcantarillado &nbsp;|&nbsp; 
            DOCENTE: Fernández Sila, Guillermo Nestor
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_logo_der:
    st.image("logo_derecha.png", use_container_width=True)

# -----------------------------------------------------------------------------
# INICIALIZACION DE DATOS EN SESSION_STATE
# -----------------------------------------------------------------------------
OPCIONES_DIAMETROS = [0.1500, 0.1536, 0.2000, 0.2500, 0.3000, 0.3500, 0.4000, 0.4500, 0.5000]

def generar_300_tramos():
    tramos = []
    tramo_global_count = 1
    
    for num_colector in range(1, 51):
        colector_tag = f"COLECTOR {num_colector}"
        camara_inicio = (num_colector - 1) * 6 + 1
        
        for t_index in range(1, 7):
            c_de = int(camara_inicio + (t_index - 1))
            c_a = int(c_de + 1)
            
            cota_t_de = round(3830.00 - (t_index * 0.45) - (num_colector * 0.10), 4)
            cota_t_a = round(3830.00 - ((t_index + 1) * 0.45) - (num_colector * 0.10), 4)
            cota_f_de = round(cota_t_de - 1.20, 4)
            cota_f_a = round(cota_t_a - 1.20, 4)
            
            tramos.append({
                "COLECTOR": colector_tag,
                "TRAMO_ID": f"T-{tramo_global_count:03d} (C-{c_de} a C-{c_a})",
                "DE": c_de,
                "A": c_a,
                "Long_m": 66.0,
                "Cota_Terreno_DE": cota_t_de,
                "Cota_Terreno_A": cota_t_a,
                "Cota_Fondo_DE": cota_f_de,
                "Cota_Fondo_A": cota_f_a,
                "D_comercial_m": 0.1536,
                "Manning_n": 0.013,
                "Q_min_RNE": 1.50
            })
            tramo_global_count += 1
            
    return pd.DataFrame(tramos)

if "df_tramos_base" not in st.session_state:
    st.session_state.df_tramos_base = generar_300_tramos()

PALETA_COLECTORES_CLAROS = [
    "#EBF5FB", "#E8F8F5", "#FEF9E7", "#F5EEF8",
    "#FBEEE6", "#EAEDED", "#EAF2F8", "#FEF5E7"
]

def estilar_colector(val):
    try:
        num = int(str(val).replace("COLECTOR", "").strip())
        color = PALETA_COLECTORES_CLAROS[(num - 1) % len(PALETA_COLECTORES_CLAROS)]
        return f"background-color: {color}; color: #2C3E50; font-weight: bold;"
    except:
        return ""

def estilar_cumplimiento(val):
    if str(val).startswith("CUMPLE"):
        return "background-color: #D4EDDA; color: #155724; font-weight: bold;"
    else:
        return "background-color: #F8D7DA; color: #721C24; font-weight: bold;"

# -----------------------------------------------------------------------------
# PESTANAS PRINCIPALES
# -----------------------------------------------------------------------------
tab_param, tab_planilla, tab_seccion, tab_perfil = st.tabs([
    "1. PARÁMETROS DE DISEÑO", 
    "2. PLANILLA HIDRÁULICA", 
    "3. DETALLE DE TRAMO Y TIRANTE DE AGUA",
    "4. PERFIL LONGITUDINAL"
])

# =============================================================================
# PESTANA 1: PARAMETROS GENERALES DINAMICOS
# =============================================================================
with tab_param:
    st.subheader("PARÁMETROS GENERALES DE DISEÑO Y CAUDAL UNITARIO")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("##### Datos Básicos")
        periodo = st.number_input("Periodo de diseño (años)", value=15)
        pob_actual = st.number_input("Población actual (hab)", value=4804)
        pob_futura = st.number_input("Población futura (hab)", value=7286)
        qmh = st.number_input("Caudal máximo horario Qmh (L/s)", value=42.16, format="%.4f")
        coef_retorno = st.number_input("Coeficiente de retorno (%)", value=80.0, format="%.2f") / 100.0
        long_total = st.number_input("Longitud total de la red (m)", value=19800.00, format="%.2f")
        
        st.markdown("---")
        st.markdown("##### 1. Selección de Conexiones Erradas ($Q_{CE}$)")
        cultura_sanitaria = st.selectbox(
            "Cultura Sanitaria de la Población:",
            ["Alta Cultura Sanitaria (5%)", "Media Cultura Sanitaria (7.5%)", "Baja / Nula Cultura Sanitaria (10%)", "Personalizado"]
        )
        
        if "Alta" in cultura_sanitaria:
            pct_erradas = 5.0
        elif "Media" in cultura_sanitaria:
            pct_erradas = 7.5
        elif "Baja" in cultura_sanitaria:
            pct_erradas = 10.0
        else:
            pct_erradas = st.number_input("Porcentaje de Conexiones Erradas (%)", value=8.0, min_value=0.0, max_value=20.0, format="%.2f")
            
        coef_erradas = pct_erradas / 100.0

    with col_p2:
        st.markdown("##### 2. Selección de Infiltración Lineal ($q_{inf}$)")
        
        nivel_freatico = st.selectbox("Nivel Freático en el área:", ["Ausente / Bajo (Por debajo del colector)", "Alto (Colector bajo agua subterránea)"])
        material_tub = st.selectbox("Material de Tubería y Junta:", ["PVC / Plástico con anillo de goma (Estanco)", "Hormigón / Concreto rígido", "Personalizado"])
        calidad_const = st.selectbox("Calidad de Construcción / Estanqueidad de BZ:", ["Buena / Estanca", "Regular", "Deficiente"])
        
        # Lógica de sugerencia de q_inf
        if "PVC" in material_tub:
            q_base = 0.00005 if "Ausente" in nivel_freatico else 0.00010
        elif "Hormigón" in material_tub:
            q_base = 0.00015 if "Ausente" in nivel_freatico else 0.00030
        else:
            q_base = 0.00010
            
        if "Deficiente" in calidad_const:
            q_base *= 1.25
            
        if material_tub == "Personalizado":
            coef_infilt = st.number_input("Coeficiente de Infiltración Lineal (L/s/m)", value=0.0001, format="%.5f")
        else:
            coef_infilt = st.number_input("Coeficiente de Infiltración Lineal Asignado (L/s/m)", value=q_base, format="%.5f")

        st.markdown("---")
        st.markdown("### RESULTADOS DE CAUDALES GLOBALES")
        
        q_retorno = qmh * coef_retorno
        q_erradas = q_retorno * coef_erradas
        q_infilt = coef_infilt * long_total
        q_total = q_retorno + q_erradas + q_infilt
        q_unitario = q_total / long_total if long_total > 0 else 0.0

        df_params = pd.DataFrame([
            {"PARAMETRO": "Caudal por Retorno (L/s)", "VALOR": f"{q_retorno:.4f}"},
            {"PARAMETRO": "Caudal Conexiones Erradas (L/s)", "VALOR": f"{q_erradas:.4f} ({pct_erradas:.1f}%)"},
            {"PARAMETRO": "Caudal por Infiltración Total (L/s)", "VALOR": f"{q_infilt:.4f}"},
            {"PARAMETRO": "CAUDAL TOTAL DE DISEÑO QDIS (L/s)", "VALOR": f"{q_total:.4f}"},
            {"PARAMETRO": "CAUDAL UNITARIO DE CIRCULACION qu (L/s/m)", "VALOR": f"{q_unitario:.4f}"}
        ])
        st.dataframe(df_params, use_container_width=True, hide_index=True)

# =============================================================================
# FUNCION CON FORMULAS Y FORMATO DE 4 DECIMALES EXACTOS
# =============================================================================
def calcular_hidraulica_tramo_completo(row, q_unit, c_erradas, c_infilt, long_acum, q_inicio_anterior):
    l_propia = float(row['Long_m'])
    
    # 1. Aguas residuales
    q_res_propio = q_unit * l_propia
    q_res_acum = q_unit * long_acum
    
    # 2. Conexiones erradas
    q_err_propio = q_res_propio * c_erradas
    q_err_acum = q_res_acum * c_erradas
    
    # 3. Infiltración
    q_inf_propio = c_infilt * l_propia
    q_inf_acum = c_infilt * long_acum
    
    # 4. Caudal total acumulado
    q_tot_calculado = q_res_acum + q_err_acum + q_inf_acum
    q_diseno_ls = max(q_tot_calculado, float(row['Q_min_RNE']))
    
    # Qi (inicial) y Qf (final)
    q_i_ls = q_inicio_anterior
    q_f_ls = q_diseno_ls
    
    q_diseno_m3s = q_diseno_ls / 1000.0
    
    # Pendiente
    c_f_de = float(row['Cota_Fondo_DE'])
    c_f_a = float(row['Cota_Fondo_A'])
    S = (c_f_de - c_f_a) / l_propia if l_propia > 0 else 0.001
    n = float(row['Manning_n'])
    
    # Diámetro calculado teórico D_calc = ((0.312 * S^0.5) / (Q * n))^-0.375
    D_calc = float(( (q_diseno_m3s * n) / (0.312 * np.sqrt(S)) ) ** (3/8)) if S > 0 else 0.1000
    
    # Diámetro comercial interior seleccionado
    D_com = float(row['D_comercial_m'])
    
    # Capacidad a sección llena y al 75%
    A_llena = (np.pi * (D_com ** 2)) / 4.0
    RH_lleno = D_com / 4.0
    Q_lleno = (1.0 / n) * A_llena * (RH_lleno ** (2/3)) * np.sqrt(S)
    
    Q_75 = 0.75 * Q_lleno
    V_75 = (1.0 / n) * (RH_lleno ** (2/3)) * np.sqrt(S)
    
    # Solver de Manning para sección parcial (Ángulo theta)
    K = (n * q_diseno_m3s) / (np.sqrt(S) * (D_com ** (8/3))) if (S > 0 and D_com > 0) else 0.01
    
    def func_solver(theta):
        if theta <= 0.0001: return 1e6
        return (((theta - np.sin(theta)) ** 5) / (theta ** 2)) - K

    try:
        theta_sol = fsolve(func_solver, x0=3.0)[0]
    except:
        theta_sol = np.pi
        
    area = (D_com**2 / 8.0) * (theta_sol - np.sin(theta_sol))
    perimetro = (D_com / 2.0) * theta_sol
    r_hid = area / perimetro if perimetro > 0 else 0.0
    v_real = q_diseno_m3s / area if area > 0 else 0.0
    
    tirante = (D_com / 2.0) * (1.0 - np.cos(theta_sol / 2.0))
    relacion_y_D = tirante / D_com if D_com > 0 else 0.0
    
    # Tensión tractiva tau = 9810 * R * S
    tau = 9810.0 * r_hid * S
    
    # Validaciones exactas
    cumple_v = "CUMPLE" if (0.60 <= v_real <= 5.00) else "NO CUMPLE"
    cumple_tau = "CUMPLE" if tau >= 1.00 else "NO CUMPLE"
    
    return {
        "COLECTOR": row['COLECTOR'],
        "CÁMARA DE": row['DE'],
        "CÁMARA A": row['A'],
        "NOMBRE ID": row['TRAMO_ID'],
        "LONGITUD TRIBUTARIA PROPIA (m)": f"{l_propia:.4f}",
        "LONG TRIBUTARIA ACUMULADA (m)": f"{long_acum:.4f}",
        "MÁXIMA AGUA RESIDUAL (Q_unit)": f"{q_unit:.4f}",
        "AGUA RESIDUAL PROPIA (L/s)": f"{q_res_propio:.4f}",
        "AGUA RESIDUAL ACUMULADO (L/s)": f"{q_res_acum:.4f}",
        "CONEXIONES ERRADAS PROPIA (L/s)": f"{q_err_propio:.4f}",
        "CONEXIONES ERRADAS ACUMULADO (L/s)": f"{q_err_acum:.4f}",
        "INFILTRACIÓN PROPIA (L/s)": f"{q_inf_propio:.4f}",
        "INFILTRACIÓN ACUMULADO (L/s)": f"{q_inf_acum:.4f}",
        "CAUDAL TOTAL (L/s)": f"{q_diseno_ls:.4f}",
        "Qi (L/s)": f"{q_i_ls:.4f}",
        "Qf (L/s)": f"{q_f_ls:.4f}",
        "COTA FONDO INICIAL (m)": f"{c_f_de:.4f}",
        "COTA FONDO FINAL (m)": f"{c_f_a:.4f}",
        "PENDIENTE (m/m)": f"{S:.4f}",
        "DIÁMETRO CALCULADO (m)": f"{D_calc:.4f}",
        "DIÁMETRO COMERCIAL INTERIOR (m)": f"{D_com:.4f}",
        "CAPACIDAD AL 75% (L/s)": f"{(Q_75 * 1000.0):.4f}",
        "VELOCIDAD AL 75% (m/s)": f"{V_75:.4f}",
        "TIRANTE (m)": f"{tirante:.4f}",
        "RELACIÓN Y/D": f"{relacion_y_D:.4f}",
        "VELOCIDAD REAL (m/s)": f"{v_real:.4f}",
        "RADIO HIDRÁULICO REAL (m)": f"{r_hid:.4f}",
        "TENSIÓN TRACTIVA (Pa)": f"{tau:.4f}",
        "VALIDACIÓN VELOCIDAD": cumple_v,
        "VALIDACIÓN TENSIÓN TRACTIVA": cumple_tau,
        # Variables numéricas internas para gráfica
        "D_m": D_com,
        "S_m/m": S,
        "Theta_rad": theta_sol,
        "Tirante_m": tirante,
        "Long_m": l_propia
    }

# =============================================================================
# PESTANA 2: PLANILLA DE CALCULO EN VIVO
# =============================================================================
with tab_planilla:
    st.subheader("PLANILLA DE CÁLCULO HIDRÁULICO PARA UN PROYECTO DE ALCANTARILLADO SANITARIO")
    
    df_edited = st.data_editor(
        st.session_state.df_tramos_base,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["TRAMO_ID"],
        column_config={
            "D_comercial_m": st.column_config.SelectboxColumn(
                "Diámetro Comercial (m)",
                help="Selecciona el diámetro interior comercial",
                width="medium",
                options=OPCIONES_DIAMETROS,
                required=True
            )
        },
        key="editor_300_key"
    )
    
    df_edited['TRAMO_ID'] = [
        f"T-{(idx + 1):03d} (C-{int(row['DE'])} a C-{int(row['A'])})"
        for idx, row in df_edited.iterrows()
    ]
    
    st.session_state.df_tramos_base = df_edited

    duplicados = df_edited[df_edited.duplicated(subset=['DE', 'A'], keep=False)]
    if not duplicados.empty:
        tramos_dupl_str = ", ".join(duplicados['TRAMO_ID'].unique())
        st.error(f"⚠️ **ALERTA DE TRAMOS DUPLICADOS DETECTADA**: Se encontraron cámaras conexas repetidas en: **{tramos_dupl_str}**.")

    resultados_lista = []
    for colector_tag, df_g in df_edited.groupby('COLECTOR', sort=False):
        l_acum = 0.0
        q_inicio = 0.0
        for _, row in df_g.iterrows():
            l_acum += float(row['Long_m'])
            res = calcular_hidraulica_tramo_completo(row, q_unitario, coef_erradas, coef_infilt, l_acum, q_inicio)
            q_inicio = float(res['CAUDAL TOTAL (L/s)'])
            resultados_lista.append(res)
            
    df_res_completo = pd.DataFrame(resultados_lista)
    
    st.markdown("### RESULTADOS AUTOMÁTICOS DEL SOLVER")
    
    columnas_solver_ver = [
        "COLECTOR", "CÁMARA DE", "CÁMARA A", "NOMBRE ID",
        "LONGITUD TRIBUTARIA PROPIA (m)", "LONG TRIBUTARIA ACUMULADA (m)",
        "MÁXIMA AGUA RESIDUAL (Q_unit)", "AGUA RESIDUAL PROPIA (L/s)", "AGUA RESIDUAL ACUMULADO (L/s)",
        "CONEXIONES ERRADAS PROPIA (L/s)", "CONEXIONES ERRADAS ACUMULADO (L/s)",
        "INFILTRACIÓN PROPIA (L/s)", "INFILTRACIÓN ACUMULADO (L/s)",
        "CAUDAL TOTAL (L/s)", "Qi (L/s)", "Qf (L/s)",
        "COTA FONDO INICIAL (m)", "COTA FONDO FINAL (m)",
        "PENDIENTE (m/m)", "DIÁMETRO CALCULADO (m)", "DIÁMETRO COMERCIAL INTERIOR (m)",
        "CAPACIDAD AL 75% (L/s)", "VELOCIDAD AL 75% (m/s)",
        "TIRANTE (m)", "RELACIÓN Y/D", "VELOCIDAD REAL (m/s)",
        "RADIO HIDRÁULICO REAL (m)", "TENSIÓN TRACTIVA (Pa)",
        "VALIDACIÓN VELOCIDAD", "VALIDACIÓN TENSIÓN TRACTIVA"
    ]
    
    df_solver_view = df_res_completo[columnas_solver_ver]
    
    df_res_styled = df_solver_view.style \
        .map(estilar_colector, subset=['COLECTOR']) \
        .map(estilar_cumplimiento, subset=['VALIDACIÓN VELOCIDAD', 'VALIDACIÓN TENSIÓN TRACTIVA'])
    
    st.dataframe(df_res_styled, use_container_width=True)

# =============================================================================
# PESTANA 3: DETALLE DE TRAMO Y TIRANTE
# =============================================================================
with tab_seccion:
    st.subheader("DETALLE DE TRAMO Y VISUALIZACIÓN DEL TIRANTE DE AGUA")
    
    lista_tramos_opciones = df_res_completo['NOMBRE ID'].tolist()
    tramo_seleccionado = st.selectbox("SELECCIONAR EL TRAMO A ANALIZAR:", lista_tramos_opciones)
    
    data_t = df_res_completo[df_res_completo['NOMBRE ID'] == tramo_seleccionado].iloc[0]
    
    col_t1, col_t2 = st.columns([1, 1])
    
    with col_t1:
        st.markdown(f"#### PARAMETROS DETALLADOS DEL {tramo_seleccionado}")
        df_tabla_excel = pd.DataFrame([
            {"PARAMETRO": "Longitud Tributaria Propia (m)", "VALOR": data_t['LONGITUD TRIBUTARIA PROPIA (m)']},
            {"PARAMETRO": "Longitud Acumulada (m)", "VALOR": data_t['LONG TRIBUTARIA ACUMULADA (m)']},
            {"PARAMETRO": "Caudal Total (L/s)", "VALOR": data_t['CAUDAL TOTAL (L/s)']},
            {"PARAMETRO": "Pendiente (m/m)", "VALOR": data_t['PENDIENTE (m/m)']},
            {"PARAMETRO": "Diametro Calculado (m)", "VALOR": data_t['DIÁMETRO CALCULADO (m)']},
            {"PARAMETRO": "Diametro Comercial Interior (m)", "VALOR": data_t['DIÁMETRO COMERCIAL INTERIOR (m)']},
            {"PARAMETRO": "Velocidad Real (m/s)", "VALOR": data_t['VELOCIDAD REAL (m/s)']},
            {"PARAMETRO": "Tirante (m)", "VALOR": data_t['TIRANTE (m)']},
            {"PARAMETRO": "Relacion Y/D", "VALOR": data_t['RELACIÓN Y/D']},
            {"PARAMETRO": "Radio Hidraulico Real (m)", "VALOR": data_t['RADIO HIDRÁULICO REAL (m)']},
            {"PARAMETRO": "Tension Tractiva (Pa)", "VALOR": data_t['TENSIÓN TRACTIVA (Pa)']},
            {"PARAMETRO": "Validacion Velocidad", "VALOR": data_t['VALIDACIÓN VELOCIDAD']},
            {"PARAMETRO": "Validacion Tension Tractiva", "VALOR": data_t['VALIDACIÓN TENSIÓN TRACTIVA']}
        ])
        st.dataframe(df_tabla_excel, use_container_width=True, hide_index=True)
        
    with col_t2:
        st.markdown("#### SECCION TRANSVERSAL CON NIVEL DE AGUA REAL")
        
        D_val = data_t['D_m']
        y_val = data_t['Tirante_m']
        R = D_val / 2.0
        
        angles = np.linspace(0, 2*np.pi, 200)
        x_pipe = R * np.cos(angles)
        y_pipe = R * np.sin(angles) + R
        
        pct_lleno = min(y_val / D_val, 1.0)
        
        fig_pipe = go.Figure()
        
        fig_pipe.add_trace(go.Scatter(
            x=x_pipe, y=y_pipe,
            mode='lines',
            line=dict(color='black', width=4),
            name='Tubería'
        ))
        
        theta_val = data_t['Theta_rad']
        if theta_val > 0:
            angles_water = np.linspace((3*np.pi/2) - (theta_val/2), (3*np.pi/2) + (theta_val/2), 100)
            x_water = R * np.cos(angles_water)
            y_water = R * np.sin(angles_water) + R
            
            x_water = np.append(x_water, [x_water[-1], x_water[0]])
            y_water = np.append(y_water, [y_water[-1], y_water[-1]])
            
            fig_pipe.add_trace(go.Scatter(
                x=x_water, y=y_water,
                fill='toself',
                fillcolor='rgba(30, 144, 255, 0.65)',
                line=dict(color='blue', width=2),
                name=f'Agua ({pct_lleno*100:.2f}% lleno)'
            ))

        fig_pipe.update_layout(
            title=dict(
                text=f"<b>Llenado de Tubería: {pct_lleno*100:.2f}% (Tirante y = {y_val:.4f} m)</b>",
                font=dict(size=20)  # <-- Aumenta el tamaño de la letra del título
            ),
            xaxis=dict(range=[-R*1.2, R*1.2], constrain='domain', visible=False),
            yaxis=dict(range=[-R*0.2, D_val*1.2], scaleanchor="x", scaleratio=1, visible=False),
            height=600,            # <-- Aumenta la altura del gráfico (de 400 a 600)
            margin=dict(l=20, r=20, t=50, b=20), # <-- Quita bordes blancos innecesarios
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_pipe, use_container_width=True)

# =============================================================================
# PESTANA 4: PERFIL LONGITUDINAL ESTILO AUTOCAD / CIVIL 3D
# =============================================================================
with tab_perfil:
    st.subheader("PERFIL LONGITUDINAL")
    
    lista_cols = df_res_completo['COLECTOR'].unique().tolist()
    col_elegido = st.selectbox("SELECCIONAR COLECTOR PARA EL PERFIL:", lista_cols)
    
    df_p = st.session_state.df_tramos_base[st.session_state.df_tramos_base['COLECTOR'] == col_elegido].reset_index(drop=True)
    df_res_p = df_res_completo[df_res_completo['COLECTOR'] == col_elegido].reset_index(drop=True)
    
    nodos_x = [0.0]
    cota_terreno_nodes = [float(df_p.iloc[0]['Cota_Terreno_DE'])]
    cota_fondo_nodes = [float(df_p.iloc[0]['Cota_Fondo_DE'])]
    buzones_names = [f"BZ-{int(df_p.iloc[0]['DE'])}"]
    
    p_acum = 0.0
    for idx, r in df_p.iterrows():
        p_acum += float(r['Long_m'])
        nodos_x.append(p_acum)
        cota_terreno_nodes.append(float(r['Cota_Terreno_A']))
        cota_fondo_nodes.append(float(r['Cota_Fondo_A']))
        buzones_names.append(f"BZ-{int(r['A'])}")

    fig_cad = go.Figure()
    
    fig_cad.add_trace(go.Scatter(
        x=nodos_x, y=cota_terreno_nodes,
        mode='lines',
        line=dict(color='#228B22', width=2),
        name='Terreno Natural'
    ))
    
    fig_cad.add_trace(go.Scatter(
        x=nodos_x, y=cota_fondo_nodes,
        mode='lines',
        line=dict(color='#8B4513', width=5),
        name='Tubería (Fondo)'
    ))
    
    ancho_bz = (max(nodos_x) if max(nodos_x) > 0 else 100) * 0.008
    for i in range(len(nodos_x)):
        x_c = nodos_x[i]
        y_bottom = cota_fondo_nodes[i]
        y_top = cota_terreno_nodes[i]
        h_bz = y_top - y_bottom
        
        fig_cad.add_shape(
            type="rect",
            x0=x_c - ancho_bz, x1=x_c + ancho_bz,
            y0=y_bottom, y1=y_top,
            fillcolor="rgba(128, 128, 128, 0.4)",
            line=dict(color="black", width=1.5)
        )
        
        fig_cad.add_annotation(
            x=x_c, y=y_top + 0.35,
            text=f"<b>{buzones_names[i]}</b><br>CT: {y_top:.2f}<br>CF: {y_bottom:.2f}<br>H: {h_bz:.2f}m",
            showarrow=False,
            font=dict(size=9, color="black"),
            bgcolor="#FFFFCC",
            bordercolor="gray",
            borderwidth=1,
            align="center"
        )
        
    for idx, r in df_res_p.iterrows():
        x_mid = (nodos_x[idx] + nodos_x[idx+1]) / 2.0
        y_mid = (cota_fondo_nodes[idx] + cota_fondo_nodes[idx+1]) / 2.0 - 0.30
        pend_pct = r['S_m/m'] * 100.0
        long_m = r['Long_m']
        d_mm = float(r['D_m']) * 1000.0
        
        fig_cad.add_annotation(
            x=x_mid, y=y_mid,
            text=f"DN {d_mm:.0f}mm | L = {long_m:.2f}m | S = {pend_pct:.2f}%",
            showarrow=False,
            font=dict(size=9, color="#8B0000"),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="#8B0000",
            borderwidth=1
        )

    fig_cad.update_layout(
        title=dict(
            text=f"<b>PERFIL LONGITUDINAL - {col_elegido} ({buzones_names[0]} a {buzones_names[-1]})</b>",
            x=0.5, font=dict(size=16)
        ),
        xaxis=dict(
            title="PROGRESIVA / DISTANCIA (m)",
            showgrid=True, gridcolor='lightgray',
            zeroline=False
        ),
        yaxis=dict(
            title="ELEVACION / COTA (m.s.n.m.)",
            showgrid=True, gridcolor='lightgray',
            zeroline=False
        ),
        template="plotly_white",
        height=550,
        showlegend=True
    )
    
    st.plotly_chart(fig_cad, use_container_width=True)
    
    st.markdown("#### GUITARRA DE DATOS DE CAMPO (GUITARRA CAD)")
    
    filas_guitarra = []
    
    row_prog = {"CONCEPTO": "PROGRESIVA (m)"}
    for i, x in enumerate(nodos_x):
        row_prog[f"{buzones_names[i]}"] = f"0+{x:06.2f}"
    filas_guitarra.append(row_prog)
    
    row_ct = {"CONCEPTO": "COTA TERRENO (m)"}
    for i, ct in enumerate(cota_terreno_nodes):
        row_ct[f"{buzones_names[i]}"] = f"{ct:.2f}"
    filas_guitarra.append(row_ct)
    
    row_cf = {"CONCEPTO": "COTA FONDO (m)"}
    for i, cf in enumerate(cota_fondo_nodes):
        row_cf[f"{buzones_names[i]}"] = f"{cf:.2f}"
    filas_guitarra.append(row_cf)
    
    row_h = {"CONCEPTO": "ALTURA BZ (m)"}
    for i in range(len(nodos_x)):
        row_h[f"{buzones_names[i]}"] = f"{(cota_terreno_nodes[i] - cota_fondo_nodes[i]):.2f}"
    filas_guitarra.append(row_h)
    
    df_guitarra = pd.DataFrame(filas_guitarra)
    st.dataframe(df_guitarra, use_container_width=True, hide_index=True)
