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
    @import url('https://fonts.googleapis.com/css2?family=Consolas&family=Roboto+Mono:wght@700&display=swap');
    
    html, body, [class*="css"], div, span, label, input, button, table {
        font-family: 'Consolas', 'Roboto Mono', 'Courier New', monospace !important;
        font-weight: 700 !important;
    }
    
    .header-box {
        background: #8B0000;
        color: white;
        padding: 18px;
        border: 2px solid #5A0000;
        margin-bottom: 20px;
        text-align: center;
    }
    .header-title {
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 1.5px;
        margin: 0;
        text-transform: uppercase;
    }
    .header-subtitle {
        font-size: 13px;
        margin-top: 5px;
        letter-spacing: 1px;
    }
</style>
<div class="header-box">
    <div class="header-title">SISTEMA DE ALCANTARILLADO SANITARIO</div>
    <div class="header-subtitle">CALCULO HIDRAULICO DINAMICO (50 COLECTORES - 300 TRAMOS)</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INICIALIZACION DE DATOS EN SESSION_STATE
# -----------------------------------------------------------------------------
def generar_300_tramos():
    tramos = []
    tramo_global_count = 1
    
    for num_colector in range(1, 51):
        colector_tag = f"COLECTOR {num_colector}"
        camara_inicio = (num_colector - 1) * 6 + 1
        
        for t_index in range(1, 7):
            c_de = int(camara_inicio + (t_index - 1))
            c_a = int(c_de + 1)
            
            cota_t_de = round(3830.00 - (t_index * 0.45) - (num_colector * 0.10), 2)
            cota_t_a = round(3830.00 - ((t_index + 1) * 0.45) - (num_colector * 0.10), 2)
            cota_f_de = round(cota_t_de - 1.20, 2)
            cota_f_a = round(cota_t_a - 1.20, 2)
            
            tramos.append({
                "COLECTOR": colector_tag,
                "TRAMO_ID": f"T-{tramo_global_count:03d} (C-{c_de} a C-{c_a})",
                "DE": c_de,
                "A": c_a,
                "Long_m": 66.0,
                "Cota_Terreno_DE": cota_t_de,
                "Cota_Terreno_A": cota_t_a,
                "Cota_Tapa_DE": cota_t_de,
                "Cota_Fondo_DE": cota_f_de,
                "Cota_Fondo_A": cota_f_a,
                "D_m": 0.1536,
                "Manning_n": 0.013,
                "Q_min_RNE": 1.50
            })
            tramo_global_count += 1
            
    return pd.DataFrame(tramos)

if "df_tramos_base" not in st.session_state:
    st.session_state.df_tramos_base = generar_300_tramos()

# PALETA DE COLORES PASTEL PARA AGRUPAR COLECTORES
PALETA_COLECTORES = [
    "#e6f2ff", "#e6ffe6", "#fff0f5", "#f0f8ff", "#fff8dc",
    "#f3e5f5", "#e8f8f5", "#fef9e7", "#ebf5fb", "#fced4c2"
]

def estilar_colector(val):
    try:
        num = int(str(val).replace("COLECTOR", "").strip())
        color = PALETA_COLECTORES[(num - 1) % len(PALETA_COLECTORES)]
        return f"background-color: {color}; color: #1c2833; font-weight: bold;"
    except:
        return ""

def estilar_cumplimiento(val):
    if str(val).startswith("CUMPLE"):
        return "background-color: #d4edda; color: #155724; font-weight: bold;"
    else:
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"

# -----------------------------------------------------------------------------
# PESTANAS PRINCIPALES
# -----------------------------------------------------------------------------
tab_param, tab_planilla, tab_seccion, tab_perfil = st.tabs([
    "1. PARAMETROS DE DISENO", 
    "2. PLANILLA HIDRAULICA (300 TRAMOS)", 
    "3. DETALLE DE TRAMO Y TIRANTE DE AGUA",
    "4. PERFIL LONGITUDINAL"
])

# =============================================================================
# PESTANA 1: PARAMETROS GENERALES
# =============================================================================
with tab_param:
    st.subheader("PARAMETROS GENERALES DE DISENO")
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        periodo = st.number_input("Periodo de diseno (anos)", value=15)
        pob_actual = st.number_input("Poblacion actual (hab)", value=4804)
        pob_futura = st.number_input("Poblacion futura (hab)", value=7286)
        qmh = st.number_input("Caudal maximo horario Qmh (L/s)", value=42.16, format="%.2f")
        coef_retorno = st.number_input("Coeficiente de retorno (%)", value=80.0) / 100.0
        coef_erradas = st.number_input("Coeficiente conexiones erradas (%)", value=15.0) / 100.0
        coef_infilt = st.number_input("Coeficiente de infiltracion (L/s/m)", value=0.0001, format="%.4f")
        long_total = st.number_input("Longitud total de red (m)", value=19800.00, format="%.2f")

    q_retorno = qmh * coef_retorno
    q_erradas = q_retorno * coef_erradas
    q_infilt = coef_infilt * long_total
    q_total = q_retorno + q_erradas + q_infilt
    q_unitario = q_total / long_total if long_total > 0 else 0.0

    with col_p2:
        st.markdown("### RESULTADOS DE CAUDALES GLOBALES")
        df_params = pd.DataFrame([
            {"PARAMETRO": "CAUDAL TOTAL ALCANTARILLADO", "UNIDAD": "L/s", "VALOR": f"{q_total:.2f}"},
            {"PARAMETRO": "CAUDAL UNITARIO DE CIRCULACION", "UNIDAD": "L/s/m", "VALOR": f"{q_unitario:.4f}"}
        ])
        st.dataframe(df_params, use_container_width=True, hide_index=True)

# =============================================================================
# FUNCION PARA CALCULAR LA HIDRAULICA
# =============================================================================
def calcular_hidraulica_tramo(row, q_unit, c_erradas, c_infilt, long_acum):
    l_propia = float(row['Long_m'])
    
    q_dom_acum = q_unit * long_acum
    q_err_acum = q_dom_acum * c_erradas
    q_inf_acum = c_infilt * long_acum
    
    q_max = q_dom_acum + q_err_acum + q_inf_acum
    q_diseno_ls = max(q_max, float(row['Q_min_RNE']))
    q_diseno_m3s = q_diseno_ls / 1000.0
    
    c_f_de = float(row['Cota_Fondo_DE'])
    c_f_a = float(row['Cota_Fondo_A'])
    S = (c_f_de - c_f_a) / l_propia if l_propia > 0 else 0.001
    
    D = float(row['D_m'])
    n = float(row['Manning_n'])
    
    K = (n * q_diseno_m3s) / (np.sqrt(S) * (D ** (8/3))) if (S > 0 and D > 0) else 0.01
    
    def func_solver(theta):
        if theta <= 0.0001: return 1e6
        return (((theta - np.sin(theta)) ** 5) / (theta ** 2)) - K

    try:
        theta_sol = fsolve(func_solver, x0=3.0)[0]
    except:
        theta_sol = np.pi
        
    area = (D**2 / 8.0) * (theta_sol - np.sin(theta_sol))
    perimetro = (D / 2.0) * theta_sol
    r_hid = area / perimetro if perimetro > 0 else 0.0
    v_real = q_diseno_m3s / area if area > 0 else 0.0
    
    tirante = (D / 2.0) * (1.0 - np.cos(theta_sol / 2.0))
    espejo_agua = D * np.sin(theta_sol / 2.0)
    
    d_m = area / espejo_agua if espejo_agua > 0 else D
    froude = v_real / np.sqrt(9.81 * d_m) if d_m > 0 else 0.0
    
    tau = 9810.0 * r_hid * S
    
    cumple_v = "CUMPLE" if (0.60 <= v_real <= 5.00) else ("NO CUMPLE (Baja V)" if v_real < 0.60 else "NO CUMPLE (Alta V)")
    cumple_tau = "CUMPLE" if tau >= 1.00 else "NO CUMPLE (< 1 Pa)"
    
    return {
        "COLECTOR": row['COLECTOR'],
        "TRAMO_ID": row['TRAMO_ID'],
        "DE": row['DE'],
        "A": row['A'],
        "Long_m": l_propia,
        "S_m/m": round(S, 4),
        "D_m": D,
        "Q_L/s": round(q_diseno_ls, 2),
        "Q_m3/s": round(q_diseno_m3s, 5),
        "K": round(K, 4),
        "Theta_rad": round(theta_sol, 4),
        "Area_m2": round(area, 4),
        "Perimetro_m": round(perimetro, 4),
        "R_Hidraulico_m": round(r_hid, 4),
        "Velocidad_m/s": round(v_real, 4),
        "Tirante_m": round(tirante, 4),
        "Espejo_Agua_m": round(espejo_agua, 4),
        "Froude": round(froude, 4),
        "Tension_Tractiva_Pa": round(tau, 4),
        "Cumple_Velocidad": cumple_v,
        "Cumple_Tension": cumple_tau
    }

# =============================================================================
# PESTANA 2: PLANILLA DE CALCULO EN VIVO
# =============================================================================
with tab_planilla:
    st.subheader("PLANILLA DE CALCULO HIDRAULICO COMPLETA (50 COLECTORES / 300 TRAMOS)")
    
    # 1. Editor con TRAMO_ID deshabilitado
    df_edited = st.data_editor(
        st.session_state.df_tramos_base,
        num_rows="dynamic",
        use_container_width=True,
        disabled=["TRAMO_ID"],
        key="editor_300_key"
    )
    
    # 2. Recalcular TRAMO_ID según cámaras DE y A
    df_edited['TRAMO_ID'] = [
        f"T-{(idx + 1):03d} (C-{int(row['DE'])} a C-{int(row['A'])})"
        for idx, row in df_edited.iterrows()
    ]
    
    st.session_state.df_tramos_base = df_edited

    # 3. Verificación de tramos duplicados
    duplicados = df_edited[df_edited.duplicated(subset=['DE', 'A'], keep=False)]
    if not duplicados.empty:
        tramos_dupl_str = ", ".join(duplicados['TRAMO_ID'].unique())
        st.error(f"⚠️ **ALERTA DE TRAMOS DUPLICADOS DETECTADA**: Se encontraron cámaras conexas repetidas en: **{tramos_dupl_str}**. Por favor corrige las cámaras 'DE' y 'A'.")

    # 4. Cálculo de la planilla
    resultados_lista = []
    for colector_tag, df_g in df_edited.groupby('COLECTOR', sort=False):
        l_acum = 0.0
        for _, row in df_g.iterrows():
            l_acum += float(row['Long_m'])
            res = calcular_hidraulica_tramo(row, q_unitario, coef_erradas, coef_infilt, l_acum)
            resultados_lista.append(res)
            
    df_res_completo = pd.DataFrame(resultados_lista)
    
    st.markdown("### RESULTADOS AUTOMATICOS DEL SOLVER")
    
    # Estilizado de la tabla Solver (Colector agrupado por color + Cumplimientos verde/rojo)
    df_res_styled = df_res_completo.style \
        .map(estilar_colector, subset=['COLECTOR']) \
        .map(estilar_cumplimiento, subset=['Cumple_Velocidad', 'Cumple_Tension'])
    
    st.dataframe(df_res_styled, use_container_width=True)

# =============================================================================
# PESTANA 3: DETALLE DE TRAMO Y TIRANTE
# =============================================================================
with tab_seccion:
    st.subheader("DETALLE DE TRAMO Y VISUALIZACION DEL TIRANTE DE AGUA")
    
    lista_tramos_opciones = df_res_completo['TRAMO_ID'].tolist()
    tramo_seleccionado = st.selectbox("SELECCIONAR EL TRAMO A ANALIZAR:", lista_tramos_opciones)
    
    data_t = df_res_completo[df_res_completo['TRAMO_ID'] == tramo_seleccionado].iloc[0]
    
    col_t1, col_t2 = st.columns([1, 1])
    
    with col_t1:
        st.markdown(f"#### PARAMETROS DEL {tramo_seleccionado}")
        df_tabla_excel = pd.DataFrame([
            {"PARAMETRO": "Longitud (m)", "VALOR": data_t['Long_m']},
            {"PARAMETRO": "Diametro (m)", "VALOR": data_t['D_m']},
            {"PARAMETRO": "Caudal (m3/s)", "VALOR": data_t['Q_m3/s']},
            {"PARAMETRO": "Pendiente (m/m)", "VALOR": data_t['S_m/m']},
            {"PARAMETRO": "Factor K", "VALOR": data_t['K']},
            {"PARAMETRO": "Angulo theta (rad)", "VALOR": data_t['Theta_rad']},
            {"PARAMETRO": "Area Mojada (m2)", "VALOR": data_t['Area_m2']},
            {"PARAMETRO": "Perimetro Mojado P (m)", "VALOR": data_t['Perimetro_m']},
            {"PARAMETRO": "Radio Hidraulico (m)", "VALOR": data_t['R_Hidraulico_m']},
            {"PARAMETRO": "Velocidad (m/s)", "VALOR": data_t['Velocidad_m/s']},
            {"PARAMETRO": "Tirante De Agua (m)", "VALOR": data_t['Tirante_m']},
            {"PARAMETRO": "Espejo De Agua (m)", "VALOR": data_t['Espejo_Agua_m']},
            {"PARAMETRO": "Numero De Froude", "VALOR": data_t['Froude']},
            {"PARAMETRO": "Tension Tractiva (Pa)", "VALOR": data_t['Tension_Tractiva_Pa']},
            {"PARAMETRO": "Cumple Velocidad", "VALOR": data_t['Cumple_Velocidad']},
            {"PARAMETRO": "Cumple Tension Tractiva", "VALOR": data_t['Cumple_Tension']}
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
                name=f'Agua ({pct_lleno*100:.1f}% lleno)'
            ))

        fig_pipe.update_layout(
            title=f"Llenado de Tubería: {pct_lleno*100:.1f}% (Tirante y = {y_val:.4f} m)",
            xaxis=dict(range=[-R*1.2, R*1.2], constrain='domain', visible=False),
            yaxis=dict(range=[-R*0.2, D_val*1.2], scaleanchor="x", scaleratio=1, visible=False),
            height=400,
            template="plotly_white",
            showlegend=True
        )
        
        st.plotly_chart(fig_pipe, use_container_width=True)

# =============================================================================
# PESTANA 4: PERFIL LONGITUDINAL
# =============================================================================
with tab_perfil:
    st.subheader("PERFILES LONGITUDINALES POR COLECTOR")
    
    lista_cols = df_res_completo['COLECTOR'].unique().tolist()
    col_elegido = st.selectbox("SELECCIONAR COLECTOR:", lista_cols)
    
    df_p = st.session_state.df_tramos_base[st.session_state.df_tramos_base['COLECTOR'] == col_elegido].reset_index(drop=True)
    
    progresivas = [0.0]
    p_terreno = [float(df_p.iloc[0]['Cota_Terreno_DE'])]
    p_fondo = [float(df_p.iloc[0]['Cota_Fondo_DE'])]
    
    p_acum = 0.0
    for idx, r in df_p.iterrows():
        p_acum += float(r['Long_m'])
        progresivas.append(p_acum)
        p_terreno.append(float(r['Cota_Terreno_A']))
        p_fondo.append(float(r['Cota_Fondo_A']))
        
    fig_prof = go.Figure()
    fig_prof.add_trace(go.Scatter(x=progresivas, y=p_terreno, mode='lines+markers', name='TERRENO', line=dict(color='green', width=2)))
    fig_prof.add_trace(go.Scatter(x=progresivas, y=p_fondo, mode='lines+markers', name='FONDO TUBERIA', line=dict(color='orange', width=2.5)))
    
    fig_prof.update_layout(
        title=f"PERFIL LONGITUDINAL {col_elegido}",
        xaxis_title="Progresiva (m)",
        yaxis_title="Cota (M.S.N.M)",
        template="plotly_white",
        height=450
    )
    st.plotly_chart(fig_prof, use_container_width=True)
