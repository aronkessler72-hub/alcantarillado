import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Alcantarillado Sanitario",
    page_icon="🌊",
    layout="wide"
)

st.markdown("""
<style>
    .header-box {
        background: linear-gradient(135deg, #8B0000 0%, #4A0000 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    .header-subtitle {
        font-size: 14px;
        opacity: 0.9;
    }
</style>
<div class="header-box">
    <div class="header-title">SISTEMA DE ALCANTARILLADO SANITARIO</div>
    <div class="header-subtitle">Planilla de Cálculo Hidráulico, Parámetros de Diseño y Perfil Longitudinal (Norma RNE / NB 688)</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PESTAÑAS PRINCIPALES
# -----------------------------------------------------------------------------
tab_param, tab_planilla, tab_perfil = st.tabs([
    "⚙️ 1. Parámetros de Diseño", 
    "📊 2. Planilla de Cálculo Hidráulico", 
    "📈 3. Perfil Longitudinal (Gráfico)"
])

# =============================================================================
# PESTAÑA 1: PARÁMETROS DE DISEÑO
# =============================================================================
with tab_param:
    st.subheader("PARÁMETROS GENERALES DE DISEÑO")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        periodo = st.number_input("Periodo de diseño (años)", value=15)
        pob_actual = st.number_input("Población actual (hab)", value=4804)
        pob_futura = st.number_input("Población futura (hab)", value=7286)
        qmh = st.number_input("Caudal máximo horario Qmh (L/s)", value=42.16, format="%.2f")
        coef_retorno = st.number_input("Coeficiente de retorno (%)", value=80.0) / 100.0
        coef_erradas = st.number_input("Coeficiente conexiones erradas (%)", value=15.0) / 100.0
        coef_infilt = st.number_input("Coeficiente de infiltración (L/s/m)", value=0.0001, format="%.4f")
        long_total = st.number_input("Longitud total de red de colectores (m)", value=5177.30, format="%.2f")

    # Cálculos derivados
    q_retorno = qmh * coef_retorno
    q_erradas = q_retorno * coef_erradas
    q_infilt = coef_infilt * long_total
    q_total = q_retorno + q_erradas + q_infilt
    q_unitario = q_total / long_total if long_total > 0 else 0.0

    with col_p2:
        st.markdown("### Resultados de Caudales Globales")
        df_params = pd.DataFrame([
            {"NRO": 1, "PARÁMETROS DE DISEÑO": "Periodo de diseño", "UNIDAD": "año", "VALOR": f"{periodo}", "OBS": ""},
            {"NRO": 2, "PARÁMETROS DE DISEÑO": "Población actual", "UNIDAD": "hab", "VALOR": f"{pob_actual}", "OBS": ""},
            {"NRO": 3, "PARÁMETROS DE DISEÑO": "Población futura", "UNIDAD": "hab", "VALOR": f"{pob_futura}", "OBS": ""},
            {"NRO": 4, "PARÁMETROS DE DISEÑO": "Caudal máximo horario (Qmh)", "UNIDAD": "L/s", "VALOR": f"{qmh:.2f}", "OBS": ""},
            {"NRO": 5, "PARÁMETROS DE DISEÑO": "Coeficiente de retorno", "UNIDAD": "%", "VALOR": f"{coef_retorno*100:.2f}%", "OBS": "RNE"},
            {"NRO": 6, "PARÁMETROS DE DISEÑO": "Coeficiente por conexiones erradas", "UNIDAD": "%", "VALOR": f"{coef_erradas*100:.2f}%", "OBS": "NB 688"},
            {"NRO": 7, "PARÁMETROS DE DISEÑO": "Coeficiente de infiltración", "UNIDAD": "L/s/m", "VALOR": f"{coef_infilt:.4f}", "OBS": "NB 688"},
            {"NRO": 8, "PARÁMETROS DE DISEÑO": "Longitud total de red de colectores", "UNIDAD": "m", "VALOR": f"{long_total:.2f}", "OBS": ""},
            {"NRO": 9, "PARÁMETROS DE DISEÑO": "Caudal de retorno", "UNIDAD": "L/s", "VALOR": f"{q_retorno:.2f}", "OBS": ""},
            {"NRO": 10, "PARÁMETROS DE DISEÑO": "Caudal por conexiones erradas", "UNIDAD": "L/s", "VALOR": f"{q_erradas:.2f}", "OBS": ""},
            {"NRO": 11, "PARÁMETROS DE DISEÑO": "Caudal por infiltración", "UNIDAD": "L/s", "VALOR": f"{q_infilt:.2f}", "OBS": ""},
            {"NRO": 12, "PARÁMETROS DE DISEÑO": "CAUDAL TOTAL DE ALCANTARILLADO", "UNIDAD": "L/s", "VALOR": f"{q_total:.2f}", "OBS": ""},
            {"NRO": 13, "PARÁMETROS DE DISEÑO": "CAUDAL UNITARIO DE CIRCULACIÓN", "UNIDAD": "L/s/m", "VALOR": f"{q_unitario:.4f}", "OBS": "CLAVE CÁLCULO"}
        ])
        st.dataframe(df_params, use_container_width=True, hide_index=True)


# =============================================================================
# DATASET INICIAL DE TRAMOS (SEGÚN TU EXCEL)
# =============================================================================
datos_tramos = [
    {"DE": 35, "A": 48, "Long_m": 66.0, "Cota_Terreno_DE": 3830.19, "Cota_Terreno_A": 3826.23, "Cota_Tapa_DE": 3830.00, "Cota_Fondo_DE": 3828.80, "Cota_Fondo_A": 3827.68, "D_m": 0.1536, "Q_min_RNE": 1.50},
    {"DE": 48, "A": 49, "Long_m": 66.0, "Cota_Terreno_DE": 3826.23, "Cota_Terreno_A": 3825.15, "Cota_Tapa_DE": 3829.16, "Cota_Fondo_DE": 3827.68, "Cota_Fondo_A": 3826.96, "D_m": 0.1536, "Q_min_RNE": 1.50},
    {"DE": 49, "A": 50, "Long_m": 66.0, "Cota_Terreno_DE": 3825.15, "Cota_Terreno_A": 3827.38, "Cota_Tapa_DE": 3828.41, "Cota_Fondo_DE": 3826.96, "Cota_Fondo_A": 3825.93, "D_m": 0.1536, "Q_min_RNE": 1.50},
    {"DE": 50, "A": 51, "Long_m": 66.0, "Cota_Terreno_DE": 3827.38, "Cota_Terreno_A": 3828.06, "Cota_Tapa_DE": 3827.58, "Cota_Fondo_DE": 3825.93, "Cota_Fondo_A": 3825.26, "D_m": 0.1536, "Q_min_RNE": 1.75},
    {"DE": 51, "A": 52, "Long_m": 60.0, "Cota_Terreno_DE": 3828.06, "Cota_Terreno_A": 3827.17, "Cota_Tapa_DE": 3826.87, "Cota_Fondo_DE": 3825.26, "Cota_Fondo_A": 3824.65, "D_m": 0.1536, "Q_min_RNE": 2.33}
]
df_tramos_input = pd.DataFrame(datos_tramos)

# =============================================================================
# PESTAÑA 2: PLANILLA DE CÁLCULO HIDRÁULICO
# =============================================================================
with tab_planilla:
    st.subheader("PLANILLA DE CÁLCULO HIDRÁULICO - ALCANTARILLADO SANITARIO")
    
    st.caption("Edita o agrega tramos según las cotas y parámetros requeridos:")
    df_edited = st.data_editor(df_tramos_input, num_rows="dynamic", use_container_width=True)

    # Lógica de cálculo acumulativo por tramo
    filas_calculadas = []
    long_acum = 0.0
    
    for idx, row in df_edited.iterrows():
        l_propia = float(row['Long_m'])
        long_acum += l_propia
        
        # Caudales
        q_dom_propio = q_unitario * l_propia
        q_dom_acum = q_unitario * long_acum
        
        q_err_propio = q_dom_propio * coef_erradas
        q_err_acum = q_dom_acum * coef_erradas
        
        q_inf_propio = coef_infilt * l_propia
        q_inf_acum = coef_infilt * long_acum
        
        q_max_final = q_dom_acum + q_err_acum + q_inf_acum
        q_diseno = max(q_max_final, float(row['Q_min_RNE']))
        q_diseno_m3s = q_diseno / 1000.0
        
        # Cotas y Pendiente
        cota_f_init = float(row['Cota_Fondo_DE'])
        cota_f_fin = float(row['Cota_Fondo_A'])
        S = (cota_f_init - cota_f_fin) / l_propia if l_propia > 0 else 0.001
        
        D = float(row['D_m'])
        n_manning = 0.013
        
        # Solver Hidráulico Manning Parcialmente Lleno
        def solver_k(theta):
            if theta <= 0: return 1e6
            K = (n_manning * q_diseno_m3s) / (np.sqrt(S) * (D ** (8/3)))
            return (((theta - np.sin(theta))**5) / (theta**2)) - K

        try:
            theta_sol = fsolve(solver_k, x0=np.pi)[0]
        except:
            theta_sol = np.pi / 2
            
        area = (D**2 / 8.0) * (theta_sol - np.sin(theta_sol))
        perimetro = (D / 2.0) * theta_sol
        r_hid = area / perimetro if perimetro > 0 else 0
        v_real = q_diseno_m3s / area if area > 0 else 0
        tirante = (D / 2.0) * (1.0 - np.cos(theta_sol / 2.0))
        hd_pct = (tirante / D) * 100
        
        # Capacidad al 75%
        cap_75 = 0.75 * (1/n_manning) * (np.pi * D**2 / 4) * ((D/4)**(2/3)) * np.sqrt(S) * 1000
        vel_75 = cap_75 / (1000 * np.pi * D**2 / 4) if D > 0 else 0
        
        tau = 9810 * r_hid * S
        
        filas_calculadas.append({
            "CÁMARA DE": row['DE'],
            "CÁMARA A": row['A'],
            "Long. Propia (m)": l_propia,
            "Long. Acum. (m)": long_acum,
            "Q Unit (L/s/m)": q_unitario,
            "Q Dom Propio": round(q_dom_propio, 3),
            "Q Dom Acum": round(q_dom_acum, 3),
            "Q Err Acum": round(q_err_acum, 3),
            "Q Inf Acum": round(q_inf_acum, 3),
            "Q Máx Final (L/s)": round(q_max_final, 3),
            "Q Diseño RNE (L/s)": round(q_diseno, 2),
            "Cota Fondo Inic": cota_f_init,
            "Cota Fondo Fin": cota_f_fin,
            "Pendiente S (m/m)": round(S, 4),
            "Diámetro (m)": D,
            "Capacidad 75% (L/s)": round(cap_75, 2),
            "Velocidad 75% (m/s)": round(vel_75, 2),
            "Tirante y (m)": round(tirante, 3),
            "h/D (%)": round(hd_pct, 2),
            "Velocidad Real (m/s)": round(v_real, 2),
            "R. Hidráulico (m)": round(r_hid, 3),
            "Tensión Tractiva (Pa)": round(tau, 2)
        })
        
    df_resultado = pd.DataFrame(filas_calculadas)
    st.dataframe(df_resultado, use_container_width=True)

# =============================================================================
# PESTAÑA 3: PERFIL LONGITUDINAL (GRÁFICO PERFIL)
# =============================================================================
with tab_perfil:
    st.subheader("📈 PERFIL LONGITUDINAL DEL COLECTOR / TRAMO")
    
    # Construcción de Progresivas
    progresiva = [0.0]
    puntos_terreno = [df_edited.iloc[0]['Cota_Terreno_DE']]
    puntos_tapa = [df_edited.iloc[0]['Cota_Tapa_DE']]
    puntos_fondo = [df_edited.iloc[0]['Cota_Fondo_DE']]
    eje_x_labels = [f"C-{df_edited.iloc[0]['DE']}"]

    prog_curr = 0.0
    for idx, r in df_edited.iterrows():
        prog_curr += float(r['Long_m'])
        progresiva.append(prog_curr)
        puntos_terreno.append(float(r['Cota_Terreno_A']))
        puntos_tapa.append(float(r['Cota_Tapa_DE']) - (idx * 0.5)) # simulación suave tapa
        puntos_fondo.append(float(r['Cota_Fondo_A']))
        eje_x_labels.append(f"C-{r['A']}")

    # Selector de tramo o ver todo
    opcion_ver = st.selectbox("Seleccionar vista del gráfico:", ["Perfil Longitudinal Completo"] + [f"Tramo Cámara {r['DE']} - {r['A']}" for _, r in df_edited.iterrows()])

    fig = go.Figure()

    if opcion_ver == "Perfil Longitudinal Completo":
        fig.add_trace(go.Scatter(x=progresiva, y=puntos_terreno, mode='lines+markers', name='TERRENO', line=dict(color='green', width=2)))
        fig.add_trace(go.Scatter(x=progresiva, y=puntos_tapa, mode='lines', name='RASANTE / TAPA', line=dict(color='gray', width=1.5, dash='dash')))
        fig.add_trace(go.Scatter(x=progresiva, y=puntos_fondo, mode='lines+markers', name='BUZÓN (FONDO)', line=dict(color='orange', width=2.5)))
        title_text = "Perfil Longitudinal General de la Red"
    else:
        # Extraer tramo individual
        idx_t = int(opcion_ver.split("Tramo")[0].strip() if "Tramo" in opcion_ver else 0)
        idx_sel = [i for i, r in df_edited.iterrows() if f"Tramo Cámara {r['DE']} - {r['A']}" == opcion_ver][0]
        
        x_sub = [progresiva[idx_sel], progresiva[idx_sel+1]]
        y_terr = [puntos_terreno[idx_sel], puntos_terreno[idx_sel+1]]
        y_fond = [puntos_fondo[idx_sel], puntos_fondo[idx_sel+1]]
        
        fig.add_trace(go.Scatter(x=x_sub, y=y_terr, mode='lines+markers', name='TERRENO', line=dict(color='green', width=3)))
        fig.add_trace(go.Scatter(x=x_sub, y=y_fond, mode='lines+markers', name='FONDO TUBERÍA', line=dict(color='orange', width=4)))
        title_text = f"Perfil Detallado del {opcion_ver}"

    fig.update_layout(
        title=title_text,
        xaxis_title="Progresiva / Distancia Acumulada (m)",
        yaxis_title="Cota (M.S.N.M)",
        hovermode="x unified",
        template="plotly_white",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)
