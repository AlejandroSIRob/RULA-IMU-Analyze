import matplotlib.pyplot as plt
import numpy as np

# =========================================================
# 1. DICCIONARIO DE PUNTUACIONES RULA
# =========================================================
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
            {'angulo': 'abduccion_hombro', 'min': 20, 'max': 180, 'score': 1},
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
        'posicion': []
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
        'estado': {'depie': 2, 'sentado': 1, 'apoyado': 1}
    }
}

def generar_png_rango(segmento, rangos, output_path):
    """Genera un PNG con la gráfica de rangos para un segmento."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Crear datos para step plot
    angles = []
    scores = []
    for r in rangos:
        angles.extend([r['min'], r['max']])
        scores.extend([r['score'], r['score']])
    
    # Ordenar por ángulo (para que plt.step dibuje de izquierda a derecha sin cruzarse)
    sorted_indices = np.argsort(angles)
    angles = np.array(angles)[sorted_indices]
    scores = np.array(scores)[sorted_indices]
    
    # Plot step y relleno
    ax.step(angles, scores, where='post', linewidth=2, color='darkblue')
    ax.fill_between(angles, scores, step='post', alpha=0.3, color='cornflowerblue')
    
    # Etiquetas y título
    ax.set_title(f'Puntuaciones RULA - {segmento.upper()} (Rangos Angulares)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Ángulo (grados): (-) Extensión / (+) Flexión', fontsize=12)
    ax.set_ylabel('Puntuación (Riesgo)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_ylim(0, 5)
    
    # Añadir anotaciones de texto en medio de cada "escalón"
    for r in rangos:
        mid = (r['min'] + r['max']) / 2
        ax.annotate(f'Pts: {r["score"]}', xy=(mid, r['score'] + 0.15), ha='center', fontsize=11, fontweight='bold', color='darkred')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'- PNG generado: {output_path}')

def generar_png_posicion(segmento, posiciones, output_path):
    """Genera un PNG con la gráfica de posiciones adicionales para un segmento."""
    if not posiciones:
        return  
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Para cada ajuste de posición, mostrar como barras
    for i, pos in enumerate(posiciones):
        # Dibujar una barra horizontal desde 'min' hasta 'max'
        ax.barh(i, pos['max'] - pos['min'], left=pos['min'], height=0.5, color='orange', alpha=0.7, edgecolor='black')
        
        # Etiqueta en el centro de la barra
        mid_point = pos['min'] + (pos['max'] - pos['min'])/2
        ax.text(mid_point, i, f'+{pos["score"]} Ptos', ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.set_title(f'Penalizaciones RULA - {segmento.upper()}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Ángulo detectado (grados)', fontsize=12)
    ax.set_yticks(range(len(posiciones)))
    ax.set_yticklabels([p['angulo'].replace('_', ' ').capitalize() for p in posiciones])
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'- PNG generado: {output_path}')

# =========================================================
# GENERADOR PRINCIPAL
# =========================================================
print("Iniciando generación de gráficos teóricos RULA...")

for segmento, data in rula_diccionario.items():
    if segmento == 'piernas':
        # Para piernas, mostrar tabla de estados
        fig, ax = plt.subplots(figsize=(6, 3))
        estados = data['estado']
        ax.table(cellText=[[k.capitalize(), f"{v} pts"] for k, v in estados.items()],
                 colLabels=['Postura/Estado', 'Puntuación Asignada'],
                 cellLoc='center', loc='center')
        ax.set_title('Puntuaciones RULA - Piernas', fontsize=14, fontweight='bold')
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(f'rula_{segmento}_estados.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f'- PNG generado: rula_{segmento}_estados.png')
        continue
    
    # Generar gráficas de rangos
    if 'rango' in data and data['rango']:
        generar_png_rango(segmento, data['rango'], f'rula_{segmento}_rangos.png')
    
    # Generar gráficas de penalizaciones por posición
    if 'posicion' in data and data['posicion']:
        generar_png_posicion(segmento, data['posicion'], f'rula_{segmento}_penalizaciones.png')

print('\n- Todos los PNGs han sido generados exitosamente. ¡Listos para adjuntar al informe!')