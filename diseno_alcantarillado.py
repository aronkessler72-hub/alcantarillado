#!/usr/bin/env python3
"""
Diseño Hidráulico de Redes de Alcantarillado Sanitario
Basado en el criterio de Tensión Tractiva y la fórmula de Manning.
"""

import numpy as np
import pandas as pd
from scipy.optimize import fsolve

# ==========================================
# 1. PARÁMETROS GENERALES (Constantes de Norma)
# ==========================================
N_MANNING = 0.013      # Coeficiente de rugosidad para tuberías de PVC
G = 9.81               # Aceleración de la gravedad (m/s²)
GAMMA_AGUA = 9810      # Peso específico del agua (N/m³)
D_MIN = 0.160          # Diámetro mínimo normado: 160mm o 6 pulgadas (en metros)
TAU_MIN = 1.0          # Tensión tractiva mínima admisible (1.0 Pascal) para autolimpieza
H_D_MAX = 0.75         # Relación de tirante máximo permitido (75% del diámetro)

# ==========================================
# 2. FUNCIONES HIDRÁULICAS CORE
# ==========================================

def calcular_seccion_llena(D, S, n):
    """
    Calcula las capacidades de la tubería trabajando al 100% (Sección Llena)
    usando la ecuación de Manning.
    """
    # Caudal a sección llena (m³/s)
    Q_0 = (0.312 / n) * (D ** (8/3)) * (S ** 0.5)
    # Velocidad a sección llena (m/s)
    V_0 = (0.397 / n) * (D ** (2/3)) * (S ** 0.5)
    return Q_0, V_0

def ecuacion_theta(theta, Q_dis, Q_0):
    """
    Ecuación implícita de relación de caudales parcial/lleno.
    Se usa para hallar el ángulo central 'theta' mediante métodos numéricos.
    """
    # Expresión geométrica deducida de las ecuaciones de flujo en canales circulares
    return (1 - np.sin(theta)/theta)**(5/3) / (1 + np.sin(theta/2))**(2/3) - (Q_dis / Q_0)

def procesar_tramo(row):
    """
    Realiza las verificaciones hidráulicas para un tramo individual de la red.
    """
    # 1. Recuperar datos de entrada del tramo
    Q_dis = row['Q_dis_m3s']
    S = row['Pendiente_m_m']
    D = D_MIN # Iniciamos con el diámetro mínimo normado
    
    # 2. Calcular propiedades a sección llena
    Q_0, V_0 = calcular_seccion_llena(D, S, N_MANNING)
    
    # Verificación rápida: si el caudal de diseño supera al de sección llena
    if Q_dis >= Q_0:
        return pd.Series([D, Q_0, np.nan, np.nan, np.nan, "ERROR: Diámetro insuficiente para el caudal"])
    
    # 3. Resolver el ángulo Theta para sección parcialmente llena
    # fsolve busca el valor de theta (empezando en pi) que hace cero la ecuación
    theta_inicial = np.pi
    theta_sol = fsolve(ecuacion_theta, theta_inicial, args=(Q_dis, Q_0))[0]
    
    # 4. Calcular parámetros en sección parcial usando el ángulo Theta obtenido
    # Relación de tirante (h/D)
    h_D = 0.5 * (1 - np.cos(theta_sol / 2))
    
    # Radio Hidráulico parcial (R_H)
    R_H = (D / 4) * (1 - np.sin(theta_sol) / theta_sol)
    
    # Velocidad real del flujo (V_real)
    V_real = V_0 * (1 - np.sin(theta_sol)/theta_sol)**(2/3)
    
    # Tensión Tractiva Real (Tau) en Pascales
    tau = GAMMA_AGUA * R_H * S
    
    # 5. Evaluar si cumple con los criterios normativos
    cumple_h = h_D <= H_D_MAX
    cumple_tau = tau >= TAU_MIN
    
    if cumple_h and cumple_tau:
        estado = "CUMPLE NORMA"
    else:
        alertas = []
        if not cumple_h: alertas.append(f"Alerta h/D (> {H_D_MAX})")
        if not cumple_tau: alertas.append(f"Alerta Autolimpieza (< {TAU_MIN} Pa)")
        estado = " REVISAR: " + " y ".join(alertas)
        
    return pd.Series([D, Q_0, h_D, V_real, tau, estado])

# ==========================================
# 3. EJECUCIÓN PRINCIPAL Y ENTRADA DE DATOS
# ==========================================
if __name__ == "__main__":
    print("Iniciando cálculo hidráulico de la red de alcantarillado...")

    # Datos iniciales recopilados del diseño geométrico en campo
    # Caudales en m3/s (puedes calcularlos previamente multiplicando área por caudal unitario)
    datos_tramos = [
        {"Tramo": "Buzón 1 - Buzón 2", "Q_dis_m3s": 0.0015, "Pendiente_m_m": 0.012},
        {"Tramo": "Buzón 2 - Buzón 3", "Q_dis_m3s": 0.0032, "Pendiente_m_m": 0.008},
        {"Tramo": "Buzón 4 - Buzón 2", "Q_dis_m3s": 0.0009, "Pendiente_m_m": 0.005}  # Pendiente baja a propósito
    ]
    
    # Convertimos los datos a una tabla de Pandas (DataFrame)
    df_red = pd.DataFrame(datos_tramos)
    
    # Aplicamos nuestros cálculos fila por fila (tramo por tramo)
    columnas_resultado = ['D_propuesto_m', 'Q_lleno_m3s', 'Relacion_h_D', 'V_real_m_s', 'Tau_Pa', 'Validacion']
    df_red[columnas_resultado] = df_red.apply(procesar_tramo, axis=1)
    
    # Imprimir los resultados en la terminal de forma ordenada
    print("\n=== REPORTE FINAL DE DISEÑO HIDRÁULICO ===")
    print(df_red.to_string(index=False))
    
    # Opcional: Descomenta la línea de abajo si quieres generar un Excel automático
    # df_red.to_excel("Planilla_Diseno_Resultados.xlsx", index=False)
