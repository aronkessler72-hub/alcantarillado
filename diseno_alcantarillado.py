import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import plotly.express as px

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CUSTOM (CSS / HTML)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Cálculo Hidráulico - Alcantarillado Sanitario",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .header-box {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 24px;
    }
    .header-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        font-size: 14px;
        opacity: 0.9;
        margin-top: 6px;
    }
    .metric-card {
        background-color: white;
        border-left: 5px solid #2a5298;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .metric-label {
        font-size: 12px;
        color: #6c757d;
        text-transform: uppercase;
        font-weight: 600;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #1e3c72;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MOTOR DE CÁLCULO HIDRÁULICO
# -----------------------------------------------------------------------------
def solver_funcion_k(theta, K_target):
    if theta <= 0:
        return 1e6
    return (((theta - np.sin(theta))**5) / (theta**2)) - K_target

def calcular_angulo_theta(D, Q, S, n):
    if Q <= 0 or S <= 0 or D <= 0:
        return 0.0, 0.0
    K_manning = (n * Q) / (np.sqrt(S) * (D ** (8/3)))
    try:
        theta_sol = fsolve(solver_funcion_k, x0=np.pi, args=(K_manning,))[0]
        return K_manning, theta_sol
    except:
        return K_manning, 0.0

def calcular_tramo(row, n_manning, tau_min, h_d_max, g=9.81, gamma_agua=9810):
    c_de = row['Cámara DE']
    c_a = row['Cámara A']
    tramo_id = f"{c_de} - {c_a}"
    longitud = float(row['Longitud (m)'])
    Q_dis_m3s = float(row['Q Diseño (L/s)']) / 1000.0
    S = float(row['Pendiente (m/m)'])
    D = float(row['Diámetro (m)'])

    K_calc, theta = calcular_angulo_theta(D, Q_dis_m3s, S, n_manning)

    if theta <= 0 or np.isnan(theta):
        return {
            'Tramo': tramo_id, 'Longitud (m)': longitud, 'Pendiente (m/m)': S,
            'Q (L/s)': row['Q Diseño (L/s)'], 'Diámetro (m)': D, 'K Solver': 0,
            'Theta (rad)': 0, 'Área (m2)': 0, 'R. Hidráulico (m)': 0,
            'Velocidad (m/s)': 0, 'Tirante y (m)': 0, 'h/D (%)': 0,
            'Froude': 0, 'Tensión Tractiva (Pa)': 0, 'Estado': 'ERROR'
        }

    area_mojada = (D**2 / 8.0) * (theta - np.sin(theta))
    perimetro_mojado = (D / 2.0) * theta
    radio_hidraulico = area_mojada / perimetro_mojado if perimetro_mojado > 0 else 0
    velocidad = Q_dis_m3s / area_mojada if area_mojada > 0 else 0
    tirante_y = (D / 2.0) * (1.0 - np.cos(theta / 2.0))
    espejo_agua_T = D * np.sin(theta / 2.0)
    h_D = (tirante_y / D) * 100
    
    prof_hidraulica = area_mojada / espejo_agua_T if espejo_agua_T > 0 else 1
    froude = velocidad / np.sqrt(g * prof_hidraulica)
    tau = gamma_agua * radio_hidraulico * S

    cumple_h = (tirante_y / D) <= h_d_max
    cumple_tau = tau >= tau_min

    if cumple_h and cumple_tau:
        estado = "CUMPLE NORMA"
    else:
        alertas = []
        if not cumple_h: alertas.append("h/D excede max")
        if not cumple_tau: alertas.append("Tau bajo")
        estado = "REVISAR: " + " & ".join(alertas)

    return {
        'Tramo': tramo_id,
        'Longitud (m)': longitud,
        'Pendiente (m/m)': S,
        'Q (L/s)': float(row['Q Diseño (L/s)']),
        'Diámetro (m)': D,
        'K Solver': round(K_calc, 4),
        'Theta (rad)': round(theta, 4),
        'Área (m2)': round(area_mojada, 5),
        'R. Hidráulico (m)': round(radio_hidraulico, 4),
        'Velocidad (m/s)': round(velocidad, 3),
        'Tirante y (m)': round(tirante_y, 4),
        'h/D (%)': round(h_D, 2),
        'Froude': round(froude, 3),
        'Tensión Tractiva (Pa)': round(tau, 2),
        'Estado': estado
    }

# -----------------------------------------------------------------------------
# INTERFAZ Y SIDEBAR
# -----------------------------------------------------------------------------
st.markdown("""
<div class="header-box">
    <div class="header-title">🌊 Diseñador Hidráulico de Alcantarillado Sanitario</div>
    <div class="header-subtitle">Criterio de Tensión Tractiva, Ecuación de Manning & Modelación Parcialmente Llena</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ Parámetros de Norma & Diseño")

n_manning = st.sidebar.number_input("Coeficiente Rugosidad (n Manning)", value=0.013, format="%.4f")
tau_min = st.sidebar.number_input("Tensión Tractiva Mínima (Pa)", value=1.00, step=0.1)
h_d_max = st.sidebar.slider("Relación Tirante Máx. (h/D %)", min_value=50, max_value=90, value=75) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Cargar / Descargar Plantilla")

datos_defecto = pd.DataFrame([
    {"Cámara DE": "35", "Cámara A": "48", "Longitud (m)": 66.0, "Q Diseño (L/s)": 1.50, "Pendiente (m/m)": 0.0130, "Diámetro (m)": 0.1536},
    {"Cámara DE": "48", "Cámara A": "49", "Longitud (m)": 66.0, "Q Diseño (L/s)": 1.50, "Pendiente (m/m)": 0.0109, "Diámetro (m)": 0.1536},
    {"Cámara DE": "49", "Cámara A": "50", "Longitud (m)": 66.0, "Q Diseño (L/s)": 1.50, "Pendiente (m/m)": 0.0156, "Diámetro (m)": 0.1536},
    {"Cámara DE": "42", "Cámara A": "43", "Longitud (m)": 56.0, "Q Diseño (L/s)": 12.95, "Pendiente (m/m)": 0.0102, "Diámetro (m)": 0.1536},
    {"Cámara DE": "43", "Cámara A": "44", "Longitud (m)": 56.0, "Q Diseño (L/s)": 12.95, "Pendiente (m/m)": 0.0104, "Diámetro (m)": 0.1536}
])

archivo_subido = st.sidebar.file_uploader("Subir CSV o Excel con Tramos", type=["csv", "xlsx"])

if archivo_subido is not None:
    if archivo_subido.name.endswith(".csv"):
        df_input = pd.read_csv(archivo_subido)
    else:
        df_input = pd.read_excel(archivo_subido)
else:
    df_input = datos_defecto

# -----------------------------------------------------------------------------
# EDICIÓN INTERACTIVA DE DATOS
# -----------------------------------------------------------------------------
st.subheader("📋 Planilla de Datos de Entrada de Tramos")
st.caption("Puedes editar los valores directamente en la tabla:")

df_editable = st.data_editor(
    df_input,
    num_rows="dynamic",
    use_container_width=True
)

# -----------------------------------------------------------------------------
# CÁLCULOS Y RESULTADOS
# -----------------------------------------------------------------------------
if not df_editable.empty:
    resultados = []
    for idx, row in df_editable.iterrows():
        res = calcular_tramo(row, n_manning, tau_min, h_d_max)
        resultados.append(res)
    
    df_res = pd.DataFrame(resultados)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Longitud Total</div>
            <div class="metric-value">{df_res['Longitud (m)'].sum():.1f} m</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        cumple_cnt = (df_res['Estado'] == 'CUMPLE NORMA').sum()
        total_cnt = len(df_res)
        pct = (cumple_cnt / total_cnt) * 100 if total_cnt > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Cumplimiento Norma</div>
            <div class="metric-value">{pct:.0f}% ({cumple_cnt}/{total_cnt})</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tensión Tractiva Mín.</div>
            <div class="metric-value">{df_res['Tensión Tractiva (Pa)'].min():.2f} Pa</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Máx. Relación h/D</div>
            <div class="metric-value">{df_res['h/D (%)'].max():.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("📊 Planilla de Cálculo Hidráulico Resultante")
    
    def destacar_estado(val):
        if val == "CUMPLE NORMA":
            return 'background-color: #d4edda; color: #155724; font-weight: bold;'
        else:
            return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'

    st.dataframe(
        df_res.style.map(destacar_estado, subset=['Estado']),
        use_container_width=True
    )

    st.subheader("📈 Gráficos de Perfil e Hidráulica")
    tab1, tab2 = st.tabs(["Tensión Tractiva & Velocidad", "Relación Tirante h/D"])

    with tab1:
        fig1 = px.bar(
            df_res, x="Tramo", y="Tensión Tractiva (Pa)",
            color="Estado",
            title="Tensión Tractiva por Tramo vs Límite de Autolimpieza (1.0 Pa)",
            color_discrete_map={"CUMPLE NORMA": "#2b8a3e", "REVISAR: Tau bajo": "#c92a2a"}
        )
        fig1.add_hline(y=tau_min, line_dash="dash", line_color="red", annotation_text="Límite Autolimpieza (1.0 Pa)")
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        fig2 = px.line(
            df_res, x="Tramo", y="h/D (%)",
            markers=True,
            title="Relación Tirante / Diámetro (h/D) por Tramo"
        )
        fig2.add_hline(y=h_d_max*100, line_dash="dash", line_color="orange", annotation_text=f"Máximo Permitido ({h_d_max*100}%)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📥 Exportar Resultados")
    csv = df_res.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Descargar Planilla Completa en CSV",
        data=csv,
        file_name="Planilla_Calculo_Hidraulico_Alcantarillado.csv",
        mime="text/csv"
    )
