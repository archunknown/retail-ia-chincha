# 🏬 Retail IA Chincha — Sistema de Gestión de Inventario Autónomo y Seguridad Perimetral 🛡️🤖

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Prolog](https://img.shields.io/badge/SWI_Prolog-ED1C24?style=for-the-badge&logo=prolog&logoColor=white)](https://www.swi-prolog.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8A2BE2?style=for-the-badge)](https://github.com/ultralytics/ultralytics)
[![Minimax](https://img.shields.io/badge/Minimax_AI-00A8CC?style=for-the-badge)](#)

¡Bienvenido al repositorio de **Retail IA Chincha Alta**! Este proyecto es un prototipo interactivo que demuestra la convergencia de la **inteligencia artificial de visión (YOLOv8)**, el **procesamiento digital de imágenes (OpenCV)**, el **razonamiento lógico-simbólico (SWI-Prolog)** y la **toma de decisiones estratégicas (Minimax con Poda Alfa-Beta)** para automatizar la seguridad y el control de existencias en un almacén de retail.

---

## 🏗️ Arquitectura General del Sistema

El flujo de información en el sistema opera de forma circular y asíncrona:

```
[Simulador 2D] ──(Posiciones/Acciones)──> [Servidor SWI-Prolog] ──(Hechos Lógicos)
     ▲                                            │
     │ (Actualización de Interfaz)                 ▼ (Inferencia de Amenazas)
[Frontend HTML5] <──(JSON Integrado)── [Servidor FastAPI] <──(Decisión Minimax)
                                                  │
                                                  ▼ (Pipeline de Filtros)
                                            [OpenCV & YOLOv8]
```

---

## 🛠️ Stack Tecnológico

1. **Backend Principal**: `FastAPI` (Python 3.10+) gestiona la API REST, sincroniza hilos y lanza el servidor Prolog.
2. **Cerebro Lógico**: `SWI-Prolog` (HTTP Server en puerto 8080) almacena la base de conocimientos dinámica de celdas, stock y deduce los niveles de peligro perimetral.
3. **Procesador de Visión**: `OpenCV` simula las transmisiones CCTV y genera el pipeline gráfico (Grises, Desenfoque Gaussiano, Canny Edges) en tiempo real.
4. **Motor Estratégico**: `Minimax` con **Poda Alfa-Beta** (Profundidad 4) calcula la ruta óptima para que el robot Guardián capture al intruso.
5. **Interfaz de Operador**: `HTML5 Canvas`, Javascript nativo y CSS moderno con glassmorphism y diseño fluido de 3 columnas para monitores widescreen.

---

## 💻 Requisitos Previos (Instalación en Windows)

Antes de clonar e iniciar el proyecto, verifique que su entorno Windows cuente con los siguientes programas instalados y configurados en las variables de entorno (`PATH`):

### 1. Python 3.10 o superior 🐍
Abra la terminal (PowerShell o CMD) y ejecute:
```powershell
python --version
```
*Si no está instalado, descárguelo desde [python.org](https://www.python.org/downloads/) y asegúrese de marcar la casilla **"Add Python to PATH"** durante el proceso de instalación.*

### 2. SWI-Prolog (swipl) 🔴
Abra la terminal y verifique que el compilador sea accesible desde cualquier directorio:
```powershell
swipl --version
```
*Si no está instalado:*
1. Descargue el instalador para Windows (64-bit) de [swi-prolog.org](https://www.swi-prolog.org/download/stable).
2. Durante la instalación, marque la opción **"Add swipl to system PATH"** para todos los usuarios.
3. Reinicie su terminal para aplicar los cambios.

---

## ⚠️ Configuración Inicial Post-Clonación (Omitidos por Gitignore)

Al clonar este repositorio, hay archivos clave que no se descargan por cuestiones de exclusión de seguridad y configuración local. Siga estos pasos para crearlos:

### 1. Crear el Archivo de Entorno `.env` 🔐
En la raíz del proyecto, cree un archivo de texto llamado exactamente `.env` y defina la variable para la API de Gemini:
```env
GEMINI_API_KEY=tu_clave_de_google_ai_studio_aqui
```
*Nota: Por defecto, el copiloto está configurado en `USE_REMOTE_GEMINI = False` en `backend/main.py` para garantizar 0ms de latencia local. Sin embargo, el archivo `.env` es requerido para inicializar correctamente el módulo de variables de entorno.*

### 2. Archivo del Modelo YOLOv8 (`yolov8n.pt`) 👁️
Al arrancar la aplicación por primera vez, la librería `ultralytics` descargará automáticamente el archivo de pesos `yolov8n.pt` (aprox. 6 MB) en la raíz del proyecto. Asegúrese de tener conexión a Internet en la primera ejecución.

---

## 🚀 Secuencia de Comandos para Arrancar el Sistema

Siga esta secuencia ordenada de comandos en la terminal desde el directorio raíz del proyecto (`C:\Users\ADMIN\retail-ia-chincha`):

### Paso 1: Crear el Entorno Virtual de Python (Recomendado)
```powershell
python -m venv venv
```

### Paso 2: Activar el Entorno Virtual
*   **En PowerShell**:
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
*   **En Símbolo del Sistema (CMD)**:
    ```cmd
    .\venv\Scripts\activate.bat
    ```

### Paso 3: Instalar Dependencias del Sistema
```powershell
pip install -r requirements.txt
```

### Paso 4: Arrancar el Servidor FastAPI (Uvicorn)
Inicie el backend en modo de recarga automática para desarrollo:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🎯 Acceso y Verificación Operativa

Una vez levantado el servidor:
1. Abra su navegador web e ingrese a: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
2. **Verificación en Consola**: Deberá observar las siguientes líneas indicando que la base lógica Prolog se instanció en paralelo en el puerto 8080:
   ```text
   Iniciando servidor lógico Prolog en segundo plano...
   Servidor Prolog inicializado exitosamente.
   INFO:     Application startup complete.
   ```
3. **Interacción**: Pruebe haciendo clic en **"Confirmar Amenaza"** para activar las sirenas e iniciar el bucle con **"Auto-Simulación: ON"**.

---

## 🗂️ Estructura del Proyecto

*   `/backend`
    *   `/prolog`
        *   `sistema_logico.pl`: Hechos lógicos, base de conocimientos y deducción de amenazas en Prolog.
    *   `main.py`: Gateway REST FastAPI, lifespan de subprocess de Prolog y endpoints del copiloto.
    *   `motor_estrategico.py`: Algoritmo Minimax con Poda Alfa-Beta para el robot Guardián.
    *   `vision_module.py`: Simulación de CCTV y pipeline gráfico con OpenCV.
*   `/frontend`
    *   `index.html`: Layout de 3 columnas fluidas.
    *   `style.css`: Estilos visuales futuristas en modo oscuro y responsive.
    *   `app.js`: Lógica del cliente, fetch a FastAPI y loop de animación interpolada en Canvas.
*   `test_backend.py`: Batería de pruebas unitarias para el motor Minimax, YOLO y fallbacks.
*   `Manual_Usuario_Retail_IA_Chincha.pdf`: Manual en PDF no técnico para el personal de tienda.
