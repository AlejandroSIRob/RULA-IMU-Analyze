# RULA-IMU-Analyze 
Herramienta en Python para el análisis ergonómico automático RULA (Rapid Upper Limb Assessment) utilizando datos cinemáticos de sensores inerciales (IMU / Xsens).

## Descripción
Este script calcula las puntuaciones de riesgo ergonómico a partir de los ángulos articulares extraídos de archivos `.sto`, `.mot` o `.json`. Elimina la subjetividad de la evaluación visual y genera reportes detallados en CSV o Excel, incluyendo gráficas de evolución temporal y distribución del riesgo.

## Requisitos
Asegúrate de tener instaladas las siguientes librerías:
```bash
pip install pandas numpy scipy matplotlib openpyxl
```

## Calibración de datos
El código ya incluye una rutina de calibración más robusta que calcula la media de los primeros 10
datos de cada articulación (trunk, brazo, antebrazo y muñeca) para establecer el punto cero. Esto
reduce el impacto de un frame inicial erróneo si el operario se mueve justo al comenzar la captura.
