import pandas as pd
import numpy as np
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import csv
# =========================================================
# 1. DICCIONARIO DE PUNTUACIONES RULA (Basado en el TFG)
# =========================================================
# El diccionario almacena dos tipos de datos para cada segmento:
#   * "rango" contiene los rangos angulares y la puntuación básica.
#   * "posicion" recoge ajustes adicionales que se suman en función
#     de otras variables o de posturas especiales.
# Esta estructura coincide con la figura 37 del TFG y permite adaptar
# el código a metodologías distintas sin tocar la lógica de cálculo.

rula_diccionario = {
    'brazo': {
        'rango': [
            {'min': -20, 'max': 20, 'score': 1},
            {'min': -180, 'max': -20, 'score': 2},  # extensión
            {'min': 20,  'max': 45, 'score': 2},
            {'min': 45,  'max': 90, 'score': 3},
            {'min': 90,  'max': 180, 'score': 4}
        ],
        'posicion': [
            # ejemplo: abducción del hombro añade +1 si supera 20°
            {'angulo': 'abduccion_hombro', 'min': 20, 'max': 180, 'score': 1},
            # el cruce de la línea media se trata con una función especial
        ]
    },
    'antebrazo': {
        'rango': [
            {'min': -90, 'max': 0, 'score': 1},
            {'min': 0,   'max': 60, 'score': 2},
            {'min': 60,  'max': 100, 'score': 3},
            {'min': 100, 'max': 180, 'score': 4}
        ],
        'posicion': []
    },
    'muñeca': {
        'rango': [
            {'min': -15, 'max': 15, 'score': 1},
            {'min': -60, 'max': -15, 'score': 2},
            {'min': 15,  'max': 60, 'score': 2},
            {'min': -180,'max': -60, 'score': 3},
            {'min': 60,  'max': 180, 'score': 3}
        ],
        'posicion': [
            # pronosupinación: distintos programas usan referencias opuestas
            # se corrige en la carga de datos en lugar de aquí
        ]
    },
    'cuello': {
        'rango': [
            {'min': -10, 'max': 10, 'score': 1},
            {'min': 10,  'max': 20, 'score': 2},
            {'min': 20,  'max': 40, 'score': 3},
            {'min': 40,  'max': 180,'score': 4}
        ],
        'posicion': [
            {'angulo': 'rotacion_cuello', 'min': 15, 'max': 180, 'score': 1},
            {'angulo': 'inclinacion_lateral_cuello', 'min': 15, 'max': 180, 'score': 1}
        ]
    },
    'tronco': {
        'rango': [
            {'min': -5,  'max': 5,  'score': 1},
            {'min': 5,   'max': 20, 'score': 2},
            {'min': 20,  'max': 60, 'score': 3},
            {'min': 60,  'max': 180, 'score': 4}
        ],
        'posicion': [
            {'angulo': 'rotacion_tronco', 'min': 15, 'max': 180, 'score': 1},
            {'angulo': 'inclinacion_lateral_tronco', 'min': 15, 'max': 180, 'score': 1}
        ]
    },
    'piernas': {
        # en RULA las piernas no se miden con un ángulo, el valor depende
        # de la postura general y del apoyo. Se deja tabla para escoger.
        'estado': {'depie': 2, 'sentado': 1, 'apoyado': 1}
    }
}


def evaluar_rango(angulo, segmento):
    """Devuelve la puntuación básica extraída del rango angular."""
    reglas = rula_diccionario[segmento].get('rango', [])
    for regla in reglas:
        if regla['min'] <= angulo <= regla['max']:
            return regla['score']
    return 1  # valor por defecto si no encaja en ningún rango


def aplicar_posiciones(score, segmento, angulos_disponibles):
    """Suma las puntuaciones adicionales definidas bajo 'posicion'.

    `angulos_disponibles` es un diccionario con nombres de ángulo
    (como 'rotacion_cuello') y sus valores actuales. Esto permite
    usar el mismo marco para entradas dependientes de múltiples medidas.
    """
    for adj in rula_diccionario[segmento].get('posicion', []):
        nombre = adj['angulo']
        if nombre in angulos_disponibles:
            valor = angulos_disponibles[nombre]
            if adj['min'] <= valor <= adj['max']:
                score += adj['score']
    return score


def brazo_cruza_linea_media(angulo_relativo):
    """Detección simplificada de cruce de línea media para el antebrazo.

    MVN/MTManager utilizan varios ángulos; aquí tomamos como referencia
    la abducción/adducción (índice 1 del vector xyz) y la flexión (índice 0).
    Si el brazo se desplaza hacia el cuerpo en flexión y abducción negativa
    se considera que ha cruzado la línea media.
    """
    flex, abd, _ = angulo_relativo
    return 1 if (flex < 0 and abd < -20) else 0

# La función original queda disponible para usos sencillos.

def evaluar_angulo(angulo, segmento):
    """Compatibilidad con código anterior: solo evalúa el rango."""
    return evaluar_rango(angulo, segmento)


# =========================================================
# 2. FUNCIONES CINEMÁTICAS Y DE CARGA
# =========================================================
def parse_quat(q_str):
    try:
        parts = [float(x) for x in q_str.split(',')]
        return [parts[1], parts[2], parts[3], parts[0]]
    except:
        return [0, 0, 0, 1]

def calculate_joint_angles(q_parent, q_child):
    r_parent = R.from_quat(q_parent)
    r_child = R.from_quat(q_child)
    r_rel = r_parent.inv() * r_child
    return r_rel.as_euler('xyz', degrees=True)

# CONFIGURACIÓN DE RUTAS
file_path = r'C:\Users\alexs\Desktop\RULA\Data\IMU\cinematica_v1.sto'
# cambia la extensión según se prefiera xlsx o csv
output_report = r'C:\Users\alexs\Desktop\RULA\Informe_Ergonomico_RULA.csv'

# --- carga de datos ---
ext = file_path.split('.')[-1].lower()
if ext == 'json':
    import json
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # suponiendo formato MVN, convertir a DataFrame sencillo
    rows = []
    for frame in data.get('frames', []):
        rows.append(frame)
    df = pd.DataFrame(rows)
elif ext in ('mot', 'sto'):
    df = pd.read_csv(file_path, sep='\t', skiprows=5)
else:
    raise ValueError(f"Formato de archivo no soportado: {ext}")

# normalizamos los quaterniones y calculamos ángulos relativos
sensors = ['pelvis_imu', 'torso_imu', 'humerus_r_imu', 'radius_r_imu', 'hand_r_imu']
for s in sensors:
    if s in df.columns:
        df[s + '_q'] = df[s].apply(parse_quat)

if 'pelvis_imu_q' in df.columns and 'torso_imu_q' in df.columns:
    df['trunk_angles'] = df.apply(lambda r: calculate_joint_angles(r['pelvis_imu_q'], r['torso_imu_q']), axis=1)
if 'torso_imu_q' in df.columns and 'humerus_r_imu_q' in df.columns:
    df['arm_angles'] = df.apply(lambda r: calculate_joint_angles(r['torso_imu_q'], r['humerus_r_imu_q']), axis=1)
# ángulo de muñeca entre antebrazo (radius) y mano
if 'radius_r_imu_q' in df.columns and 'hand_r_imu_q' in df.columns:
    df['wrist_angles'] = df.apply(lambda r: calculate_joint_angles(r['radius_r_imu_q'], r['hand_r_imu_q']), axis=1)

# --- CALIBRACIÓN ROBUSTA (Media de los primeros 10 frames) ---
def calibrar_con_media(df, col_angles, index=0, num_frames=10):
    if col_angles in df.columns:
        # calculamos la media de los primeros N frames (ej. 10) para evitar el ruido del inicio
        offset = df[col_angles].iloc[:num_frames].apply(lambda x: x[index]).mean()
        return ((df[col_angles].apply(lambda x: x[index]) - offset) + 180) % 360 - 180
    # si no existe la columna devolvemos una serie de ceros para no romper el concat
    return pd.Series([0] * len(df))

# aplicamos la nueva función a todos los segmentos que tengamos

# trunk y brazo ya estaban definidos anteriormente
if 'trunk_angles' in df.columns:
    df['flexion_tronco'] = calibrar_con_media(df, 'trunk_angles', 0)
if 'arm_angles' in df.columns:
    df['flexion_brazo'] = calibrar_con_media(df, 'arm_angles', 0)
# por si llegase a introducirse una columna de antebrazo independiente
if 'forearm_angles' in df.columns:
    df['flexion_antebrazo'] = calibrar_con_media(df, 'forearm_angles', 0)
if 'wrist_angles' in df.columns:
    df['flexion_muneca'] = calibrar_con_media(df, 'wrist_angles', 0)

# límites circulares: incluye ahora el antebrazo si se calculó
for col in ['flexion_tronco', 'flexion_brazo', 'flexion_antebrazo', 'flexion_muneca']:
    if col in df.columns:
        df[col] = (df[col] + 180) % 360 - 180

# inversión manual si los datos vienen con signo invertido
# df['flexion_tronco'] *= -1  # descomentar si se detecta inversión

# =========================================================
# 3. APLICACIÓN DE PUNTUACIONES RULA
# =========================================================

# calculamos las puntuaciones básicas y aplicamos ajustes de posición
def puntuaciones_por_fila(row):
    extras = {}
    
    # --- NOVEDAD: Rellenamos los "extras" para que las penalizaciones funcionen ---
    # Extraemos abducción (eje Y = índice 1) y rotación (eje Z = índice 2)
    if 'arm_angles' in row and isinstance(row['arm_angles'], (list, tuple, np.ndarray)):
        extras['abduccion_hombro'] = abs(row['arm_angles'][1])
        
    if 'trunk_angles' in row and isinstance(row['trunk_angles'], (list, tuple, np.ndarray)):
        extras['inclinacion_lateral_tronco'] = abs(row['trunk_angles'][1])
        extras['rotacion_tronco'] = abs(row['trunk_angles'][2])

    # 1. Puntos Brazo (Ahora sí aplicará +1 si abducción > 20)
    score_brazo = evaluar_rango(row.get('flexion_brazo', 0), 'brazo')
    score_brazo = aplicar_posiciones(score_brazo, 'brazo', extras)
    
    # 2. Cruce de línea media (Añadido np.ndarray para que funcione)
    if 'arm_angles' in row and isinstance(row['arm_angles'], (list, tuple, np.ndarray)):
        score_brazo += brazo_cruza_linea_media(row['arm_angles'])
        
    # 3. Puntos Muñeca
    score_muneca = evaluar_rango(row.get('flexion_muneca', 0), 'muñeca')
    score_muneca = aplicar_posiciones(score_muneca, 'muñeca', extras)
    
    # 4. Puntos Tronco (Ahora sí aplicará +1 si hay rotación o inclinación)
    score_tronco = evaluar_rango(row.get('flexion_tronco', 0), 'tronco')
    score_tronco = aplicar_posiciones(score_tronco, 'tronco', extras)
    
    return pd.Series({
        'Puntos_Brazo': score_brazo, 
        'Puntos_Muneca': score_muneca, 
        'Puntos_Tronco': score_tronco
    })

puntos = df.apply(puntuaciones_por_fila, axis=1)
df = pd.concat([df, puntos], axis=1)

# parámetros de usuario
Carga_Kilos = 0       # 0 = <2kg, 1 = 2-10kg, 2 = >10kg o repetitivo, 3 = >10kg estático
Uso_Muscular = 0      # 1 si la postura es estática (>1 min) o repetitiva (>4 veces/min), 0 si es ocasional
estado_piernas = 'depie'  # opciones: 'depie','sentado','apoyado'

# añadir puntuación de piernas a la tabla B (Grupos B)
puntaje_piernas = rula_diccionario['piernas']['estado'].get(estado_piernas, 2)

# cálculo de los score de grupos A y B
# ahora brazo y muñeca forman parte del grupo A
df['Score_Grupo_A'] = df['Puntos_Brazo'] + df.get('Puntos_Muneca',0) + Uso_Muscular + Carga_Kilos
df['Score_Grupo_B'] = df['Puntos_Tronco'] + Uso_Muscular + Carga_Kilos + puntaje_piernas

# Matriz C simplificada (Para calcular el riesgo final de 1 a 7)
def calcular_rula_final(score_a, score_b):
    # Esto es una simplificación matemática de la Tabla C de RULA
    riesgo = max(score_a, score_b) + (min(score_a, score_b) // 2)
    return min(7, max(1, riesgo))

df['RULA_Final'] = df.apply(lambda r: calcular_rula_final(r['Score_Grupo_A'], r['Score_Grupo_B']), axis=1)

# Categorización para la Gráfica de Sectores
def clasificar_riesgo(score):
    if score in [1, 2]: return 'Verde (1-2) Riesgo Bajo'
    elif score in [3, 4]: return 'Amarillo (3-4) Riesgo Medio'
    elif score in [5, 6]: return 'Naranja (5-6) Riesgo Alto'
    else: return 'Rojo (7) Riesgo Inaceptable'

df['Nivel_Riesgo'] = df['RULA_Final'].apply(clasificar_riesgo)

# =========================================================
# 4. EXPORTACIÓN A EXCEL Y GENERACIÓN DE GRÁFICAS
# =========================================================
# Guardar informe, seleccionando el método según la extensión
columnas_export = ['time', 'flexion_tronco', 'flexion_brazo', 'flexion_muneca',
                   'Puntos_Brazo', 'Puntos_Muneca', 'Puntos_Tronco', 'RULA_Final']
ext_rep = output_report.split('.')[-1].lower()
if ext_rep in ('xlsx','xls'):
    df[columnas_export].to_excel(output_report, index=False, engine='openpyxl')
elif ext_rep == 'csv':
    df[columnas_export].to_csv(output_report, index=False)
else:
    raise ValueError(f"Extensión desconocida para el informe: {ext_rep}")
print(f" Informe generado con éxito en:\n{output_report}")

# Gráficas
fig = plt.figure(figsize=(14, 6))

# Subplot 1: Línea de tiempo de la Puntuación RULA Final
ax1 = plt.subplot(1, 2, 1)
ax1.plot(df['time'], df['RULA_Final'], color='black', drawstyle='steps-post')
ax1.fill_between(df['time'], df['RULA_Final'], color='gray', alpha=0.2)
ax1.set_title('Evolución de la Puntuación RULA Final')
ax1.set_xlabel('Tiempo (s)')
ax1.set_ylabel('Puntuación RULA (1-7)')
ax1.set_ylim(0, 8)
ax1.grid(True, linestyle='--', alpha=0.5)

# Subplot 2: Gráfica de Sectores (Pie Chart)
ax2 = plt.subplot(1, 2, 2)
conteo_riesgos = df['Nivel_Riesgo'].value_counts()
colores_oficiales = {
    'Verde (1-2) Riesgo Bajo': '#2ecc71',
    'Amarillo (3-4) Riesgo Medio': '#f1c40f',
    'Naranja (5-6) Riesgo Alto': '#e67e22',
    'Rojo (7) Riesgo Inaceptable': '#e74c3c'
}
colores_grafica = [colores_oficiales[key] for key in conteo_riesgos.index]

ax2.pie(conteo_riesgos, labels=conteo_riesgos.index, autopct='%1.1f%%', 
        colors=colores_grafica, startangle=90, wedgeprops={'edgecolor': 'black'})
ax2.set_title('Distribución del Nivel de Riesgo (Tiempo Total)')

plt.tight_layout()
plt.show()