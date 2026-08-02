#!/usr/bin/env python3
"""
Diseño Hidráulico de Redes de Alcantarillado Sanitario
Integra la formulación solver de la planilla Excel con la validación normativa de Python.
"""

import numpy as np
import pandas as pd
from scipy.optimize import fsolve

# ==========================================
# 1. PARÁMETROS GENERALES Y CONSTANTES DE NORMA
# ==========================================
N_MANNING = 0.013      # Coeficiente de rugosidad para PVC
G = 9.81               # Aceleración de la gravedad (m/s²)
GAMMA_AGUA = 9810      # Peso específico del agua (N/m³)
RHO_AGUA = 1000        # Densidad del agua (kg/m³)
D_MIN = 0.1536         # Diámetro interno estándar mínimo (~160mm exterior / SN4)
TAU_MIN = 1.0          # Tensión tractiva mínima admisible (Pa)
H_D_MAX = 0.75         # Tirante máximo permitido (75% del diámetro)

# Tabla de diámetros comerciales (mm nominal -> m interno SN4 / Serie 20)
TABLA_DIAMETROS = {
    110: 0.1036,
    160: 0.1520,
    200: 0.1902,
    250: 0.2376,
    315: 0.2996,
    355: 0.3376,
    400: 0.3804,
    450: 0.4280,
    500: 0.4754,
    630: 0.5992
}

# ==========================================
# 2. FUNCIONES HIDRÁULICAS CORE
# ==========================================

def solver_funcion_k(theta, K_target):
    """
    Función solver usada en tu hoja de Excel:
    ((theta - sen(theta))^5) / (theta^2) - K_target = 0
    """
    if theta <= 0:
        return 1e6
    return (((theta - np.sin(theta))**5) / (theta**2)) - K_target

def calcular_angulo_theta(D, Q, S, n=N_MANNING):
    """
    Calcula el valor de 'K' de Manning y resuelve el ángulo central theta (rad).
    """
    if Q <= 0 or S <= 0 or D <= 0:
        return 0.0, 0.0

    # Constante K exacta del modelo Excel
    # K = (n * Q) / (S^0.5 * D^(8/3))
    K_manning = (n * Q) / (np.sqrt(S) * (D ** (8/3)))
    
    # Resolver theta partiendo de pi
    theta_sol = fsolve(solver_funcion_k, x0=np.pi, args=(K_manning,))[0]
    
    return K_manning, theta_sol

def procesar_tramo_hidraulico(row):
    """
    Procesa un tramo completo calculando geometría, hidráulica y validaciones normativas.
    """
    # 1. Recuperar entradas
    tramo_id = f"{row['Cámara_DE']}-{row['Cámara_A']}"
    longitud = row['Longitud_m']
    Q_dis_m3s = row['Q_dis_m3s']
    S = row['Pendiente_m_m']
    D = row.get('Diametro_m', D_MIN)
    
    # 2. Solución del ángulo Theta y K
    K_calc, theta = calcular_angulo_theta(D, Q_dis_m3s, S, N_MANNING)
    
    if theta <= 0 or np.isnan(theta):
        return pd.Series([tramo_id, D, 0, 0, 0, 0, 0, 0, 0, 0, "ERROR EN SOLVER"])

    # 3. Propiedades hidráulicas a sección parcialmente llena
    area_mojada = (D**2 / 8.0) * (theta - np.sin(theta))
    perimetro_mojado = (D / 2.0) * theta
    radio_hidraulico = area_mojada / perimetro_mojado if perimetro_mojado > 0 else 0
    
    velocidad = Q_dis_m3s / area_mojada if area_mojada > 0 else 0
    tirante_y = (D / 2.0) * (1.0 - np.cos(theta / 2.0))
    espejo_agua_T = D * np.sin(theta / 2.0)
    
    # Relación Tirante/Diámetro (y/D)
    h_D = tirante_y / D
    
    # Número de Froude
    prof_hidraulica = area_mojada / espejo_agua_T if espejo_agua_T > 0 else 1
    froude = velocidad / np.sqrt(G * prof_hidraulica)
    
    # Tensión Tractiva (Pa)
    tau = GAMMA_AGUA * radio_hidraulico * S
    
    # 4. Validaciones de Norma
    cumple_h = h_D <= H_D_MAX
    cumple_tau = tau >= TAU_MIN
    
    if cumple_h and cumple_tau:
        estado = "OK"
    else:
        alertas = []
        if not cumple_h: alertas.append(f"h/D>{H_D_MAX*100}%")
        if not cumple_tau: alertas.append(f"Tau<{TAU_MIN}Pa")
        estado = "REVISAR: " + " & ".join(alertas)

    return pd.Series({
        'Tramo': tramo_id,
        'Longitud (m)': longitud,
        'Pendiente (m/m)': S,
        'Q_Diseño (m3/s)': Q_dis_m3s,
        'Diámetro (m)': D,
        'K Solver': round(K_calc, 4),
        'Ángulo (rad)': round(theta, 4),
        'Área Mojada (m2)': round(area_mojada, 4),
        'Perímetro (m)': round(perimetro_mojado, 4),
        'R. Hidráulico (m)': round(radio_hidraulico, 4),
        'Velocidad (m/s)': round(velocidad, 3),
        'Tirante (m)': round(tirante_y, 4),
        'Espejo Agua (m)': round(espejo_agua_T, 4),
        'Froude': round(froude, 3),
        'Tensión Tractiva (Pa)': round(tau, 2),
        'Estado Norma': estado
    })

# ==========================================
# 3. EJECUCIÓN Y DATOS DE ENTRADA (PLANILLA)
# ==========================================
if __name__ == "__main__":
    print("=========================================================")
    print("   DISEÑO HIDRÁULICO DE ALCANTARILLADO - PLANILLA EXCEL")
    print("=========================================================\n")

    # Tramos del proyecto extraídos de tu capturas
    datos_tramos = [
        {"Cámara_DE": 35, "Cámara_A": 48, "Longitud_m": 66.0, "Q_dis_m3s": 0.0015, "Pendiente_m_m": 0.0130, "Diametro_m": 0.1536},
        {"Cámara_DE": 48, "Cámara_A": 49, "Longitud_m": 66.0, "Q_dis_m3s": 0.0015, "Pendiente_m_m": 0.0109, "Diametro_m": 0.1536},
        {"Cámara_DE": 49, "Cámara_A": 50, "Longitud_m": 66.0, "Q_dis_m3s": 0.0015, "Pendiente_m_m": 0.0156, "Diametro_m": 0.1536},
        {"Cámara_DE": 42, "Cámara_A": 43, "Longitud_m": 56.0, "Q_dis_m3s": 0.0129, "Pendiente_m_m": 0.0102, "Diametro_m": 0.1536},
        {"Cámara_DE": 43, "Cámara_A": 44, "Longitud_m": 56.0, "Q_dis_m3s": 0.0129, "Pendiente_m_m": 0.0104, "Diametro_m": 0.1536}
    ]
    
    # Crear DataFrame
    df_tramos = pd.DataFrame(datos_tramos)
    
    # Aplicar el procesador a cada tramo
    df_resultados = df_tramos.apply(procesar_tramo_hidraulico, axis=1)
    
    # Mostrar reporte
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df_resultados.to_string(index=False))
