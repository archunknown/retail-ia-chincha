import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
print(f"[DEBUG GEMINI] Clave detectada (Primeros 5 caracteres): {GEMINI_API_KEY[:5] if GEMINI_API_KEY else 'NULA/VACÍA'}")
USE_REMOTE_GEMINI = False # Desactivado por defecto para garantizar 0ms de latencia y funcionamiento 100% local/offline

import time
import subprocess
import requests
import random
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel

# Import our custom modules
from backend.motor_estrategico import find_best_move_guardian, find_best_move_intruder, manhattan_distance
from backend.vision_module import VisionSystem

# Global variables to track state
prolog_process = None
prolog_port = 8080
prolog_url = f"http://localhost:{prolog_port}"

grid_state = {
    'guardian_pos': [3, 5],
    'intruder_pos': [2, 1],
    'intruder_conf': 0.85, # Starts in warning range (70-89%) to demonstrate ethical manual confirmation
    'intruder_confirmed': False,
    'active_camera': 'camara_1',
    'simulation_logs': [],
    'minimax_logs': None,
    'vision_logs': None,
    'game_over': False,
    'message': "Inicializando simulación. Intruso detectado con confianza del 85%. Requiere confirmación manual."
}

vision_system = VisionSystem()

def check_prolog_alive():
    try:
        r = requests.get(f"{prolog_url}/state", timeout=0.5)
        return r.status_code == 200
    except Exception:
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global prolog_process
    # 1. Start Prolog server via subprocess.Popen (non-blocking)
    print("Iniciando servidor lógico Prolog en segundo plano...")
    try:
        prolog_process = subprocess.Popen(
            ['swipl', '-q', '-s', 'backend/prolog/sistema_logico.pl', '-t', f'server({prolog_port})'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except (FileNotFoundError, OSError) as e:
        print(f"ERROR CRÍTICO: No se pudo iniciar SWI-Prolog ({e}). Asegúrese de que 'swipl' esté instalado y en el PATH.")
        prolog_process = None
    
    # Wait for Prolog to start
    retries = 10
    started = False
    for i in range(retries):
        if check_prolog_alive():
            started = True
            break
        print(f"Esperando a Prolog (intento {i+1}/{retries})...")
        time.sleep(0.5)
        
    if not started:
        print("ERROR: No se pudo conectar con el servidor Prolog.")
    else:
        print("Servidor Prolog inicializado exitosamente.")
        # Sync initial agent positions into Prolog
        try:
            # Sync Guardian (val=2) and Intruder (val=3)
            requests.post(f"{prolog_url}/update_grid", json={'x': grid_state['guardian_pos'][0], 'y': grid_state['guardian_pos'][1], 'val': 2})
            requests.post(f"{prolog_url}/update_grid", json={'x': grid_state['intruder_pos'][0], 'y': grid_state['intruder_pos'][1], 'val': 3})
        except Exception as e:
            print(f"Error al sincronizar posiciones iniciales: {e}")

    yield
    
    # Shutdown Prolog
    if prolog_process:
        print("Apagando servidor Prolog...")
        prolog_process.terminate()
        try:
            prolog_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            prolog_process.kill()
        print("Servidor Prolog terminado.")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware to support any client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API schemas
class StockUpdate(BaseModel):
    estante_id: str
    cantidad: int

class ChatRequest(BaseModel):
    message: str

def fetch_prolog_state():
    """Fetches the state directly from SWI-Prolog HTTP server."""
    try:
        r = requests.get(f"{prolog_url}/state", timeout=1.0)
        return r.json()
    except Exception as e:
        print(f"Error fetching Prolog state: {e}")
        return None

def sync_agent_positions_to_prolog(old_g, new_g, old_i, new_i):
    """
    Ensures sequential, atomic updates of cell states in Prolog.
    Value 0 is path, 2 is Guardian, 3 is Intruder.
    """
    try:
        # 1. Clear old positions in Prolog (if they were paths)
        if old_g:
            requests.post(f"{prolog_url}/update_grid", json={'x': old_g[0], 'y': old_g[1], 'val': 0})
        if old_i:
            requests.post(f"{prolog_url}/update_grid", json={'x': old_i[0], 'y': old_i[1], 'val': 0})
            
        # 2. Write new positions in Prolog
        if new_g:
            requests.post(f"{prolog_url}/update_grid", json={'x': new_g[0], 'y': new_g[1], 'val': 2})
        if new_i:
            requests.post(f"{prolog_url}/update_grid", json={'x': new_i[0], 'y': new_i[1], 'val': 3})
    except Exception as e:
        print(f"Error syncing positions to Prolog: {e}")

def get_prolog_threat_check(clase, zona, horario):
    try:
        r = requests.post(f"{prolog_url}/check_event_threat", json={
            'clase': clase,
            'zona': zona,
            'horario': horario
        })
        return r.json()
    except Exception as e:
        print(f"Error querying threat from Prolog: {e}")
        return {'nivel': 'bajo', 'cadena_inferencia': ['error_comunicacion']}

def explain_inference_chain_with_gemini(chain):
    def get_fallback_message(c):
        chain_str = " -> ".join(c)
        base = f"[Modo Local] Inferencia de lógica local: {chain_str}.\n"
        if "alerta_intrusion" in c or "intruso_detectado" in c:
            return base + "Alerta de seguridad crítica. El sistema ha inferido la presencia de un intruso en la zona restringida. Despliegue inmediato de contención táctica por el Guardián."
        elif "cliente_en_zona_restringida" in c:
            return base + "Advertencia operativa. Se detectó un cliente o elemento sospechoso en estante restringido durante el turno de noche. Verifique las cámaras de seguridad."
        elif "quiebre_stock" in c:
            return base + "Reabastecimiento crítico. Uno o más estantes han registrado un nivel de stock menor al 20%. Se requiere la reposición inmediata de productos."
        else:
            return base + "Reporte de almacén general: Operaciones en estado normal."

    if not USE_REMOTE_GEMINI or not GEMINI_API_KEY:
        return get_fallback_message(chain)

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"""
    Eres el Copiloto de Inteligencia Artificial para el sistema de seguridad e inventario del almacén Retail en Chincha.
    El cerebro lógico Prolog ha retornado la siguiente cadena de inferencia de amenazas: {chain}.
    Explica de forma concisa, profesional y directa qué significa esta inferencia lógica para el operador de seguridad humano y qué acciones se deben tomar.
    No uses saludos ni explicaciones innecesarias, ve directo al grano.
    """
    
    try:
        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=5.0)
        
        if response.status_code == 200:
            res_json = response.json()
            try:
                return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            except (KeyError, IndexError, TypeError):
                print("[WARN GEMINI] Respuesta con estructura inesperada. Usando fallback local.")
                return get_fallback_message(chain)
        else:
            print(f"[WARN GEMINI] API retornó {response.status_code} ({response.text}). Usando fallback local.")
            return get_fallback_message(chain)
    except (requests.RequestException, Exception) as e:
        print(f"[WARN GEMINI] Error de comunicación ({str(e)}). Usando fallback local.")
        return get_fallback_message(chain)

def get_local_fallback_chat_reply(user_msg, chain, p_state):
    user_msg_clean = user_msg.strip().lower()
    
    # 1. Intruso/Amenazas
    if any(k in user_msg_clean for k in ["intruso", "amenaza", "robo", "seguridad", "ladron", "alerta", "peligro"]):
        if grid_state['intruder_pos']:
            return f"[Modo Local] ALERTA DE SEGURIDAD: Se detecta un intruso en la posición {grid_state['intruder_pos']}. El Guardián (en {grid_state['guardian_pos']}) está ejecutando la búsqueda competitiva Minimax para neutralizar la amenaza."
        else:
            return "[Modo Local] SEGURIDAD: No se registran amenazas activas en el perímetro. El almacén se encuentra seguro."
            
    # 2. Stock/Inventario/Estantes
    elif any(k in user_msg_clean for k in ["stock", "inventario", "estante", "arroz", "azucar", "leche", "aceite", "cafe", "atun", "lentejas", "fideos", "producto", "mercancia"]):
        if p_state and 'stock' in p_state:
            low_stock = []
            for st in p_state['stock']:
                if st.get('cantidad', 0) <= 2:
                    low_stock.append(f"{st.get('producto')} ({st.get('cantidad')} uds)")
            if low_stock:
                return f"[Modo Local] INVENTARIO: Se registran niveles críticos en los siguientes estantes: {', '.join(low_stock)}. Requiere reabastecimiento inmediato."
            else:
                return "[Modo Local] INVENTARIO: Todos los estantes tienen niveles de stock estables (capacidad normal)."
        return "[Modo Local] INVENTARIO: La base de datos de inventario no está accesible en este momento."
        
    # 3. Alarmas
    elif "alarma" in user_msg_clean:
        if p_state and 'alarmas' in p_state:
            alarm_info = []
            for al in p_state['alarmas']:
                alarm_info.append(f"{al.get('tipo')}: {al.get('estado')}")
            return f"[Modo Local] ESTADO DE ALARMAS: {', '.join(alarm_info)}."
        return "[Modo Local] ALARMAS: No se pudo obtener el estado de las alarmas lógicas."
        
    # 4. Guardian/Minimax
    elif any(k in user_msg_clean for k in ["guardian", "minimax", "movimiento", "estrategia", "poda", "heuristica"]):
        return f"[Modo Local] SISTEMA ESTRATÉGICO: El Guardián patrulla activamente. Utiliza búsqueda Minimax con profundidad de 4 plies y poda Alfa-Beta. Heurística actual: w1=5.0 (cobertura), w2=15.0 (persecución), w3=10.0 (seguridad)."
        
    # 5. Cámaras/Visión/OpenCV
    elif any(k in user_msg_clean for k in ["camara", "cctv", "vision", "opencv", "yolo", "canny", "grises", "blur"]):
        return f"[Modo Local] SUBSISTEMA DE VISIÓN: Se simulan 4 cámaras CCTV con OpenCV. El pipeline de procesamiento de imagen genera flujos de Canny y grises en tiempo real. YOLOv8-nano detecta objetos aplicando un umbral ético de confianza del 90%."
        
    # Default fallback
    chain_str = " -> ".join(chain)
    base = f"[Modo Local] Inferencia de lógica local: {chain_str}.\n"
    if "alerta_intrusion" in chain or "intruso_detectado" in chain:
        return base + "Acción recomendada: Intervención del Guardián activada. Mantenga vigilado el cuadrante noroeste/noreste."
    elif "quiebre_stock" in chain:
        return base + "Acción recomendada: Envíe personal a reponer los estantes vacíos identificados."
    else:
        return base + "Acción recomendada: Operaciones normales. No se requieren acciones correctivas."

def get_chat_response_with_gemini_or_fallback(user_msg, chain, p_state):
    # If API key is not configured or remote Gemini is disabled, go straight to local fallback
    if not USE_REMOTE_GEMINI or not GEMINI_API_KEY:
        return get_local_fallback_chat_reply(user_msg, chain, p_state)
        
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    context = f"""
    Contexto de la simulación del almacén Chincha:
    - Posición del Guardián: {grid_state['guardian_pos']}
    - Posición del Intruso: {grid_state['intruder_pos'] if grid_state['intruder_pos'] else 'Capturado/Inactivo'}
    - Cámaras activas: {p_state.get('camaras') if p_state else 'No disponible'}
    - Alarmas activas: {p_state.get('alarmas') if p_state else 'No disponible'}
    - Inventario de estantes: {p_state.get('stock') if p_state else 'No disponible'}
    - Inferencia Prolog actual: {chain}
    """
    
    prompt = f"""
    Eres el Copiloto de Inteligencia Artificial para el sistema de seguridad e inventario del almacén Retail en Chincha.
    Responde la siguiente pregunta del operador de seguridad: "{user_msg}"
    Utiliza el contexto de la simulación provisto a continuación:
    {context}
    Responde de forma concisa, profesional y directa en español. Si el usuario te pregunta sobre el stock de un producto o sobre la posición del intruso, responde de acuerdo a los datos de la simulación.
    No uses saludos ni introducciones vacías.
    """
    
    try:
        response = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=5.0)
        
        if response.status_code == 200:
            res_json = response.json()
            try:
                return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            except (KeyError, IndexError, TypeError):
                print("[WARN GEMINI] Estructura de respuesta de chat inesperada. Usando fallback local.")
                return get_local_fallback_chat_reply(user_msg, chain, p_state)
        else:
            print(f"[WARN GEMINI] API retornó {response.status_code} en chat. Usando fallback local.")
            return get_local_fallback_chat_reply(user_msg, chain, p_state)
    except (requests.RequestException, Exception) as e:
        print(f"[WARN GEMINI] Error de comunicación en chat ({str(e)}). Usando fallback local.")
        return get_local_fallback_chat_reply(user_msg, chain, p_state)

# REST API Endpoints
@app.get("/api/state")
def get_state(camera_id: str = None):
    p_state = fetch_prolog_state()
    if p_state:
        # Merge Prolog database state with local Python state
        # Find camera covering intruder if intruder exists
        if camera_id and any(c['id'] == camera_id for c in p_state.get('camaras', [])):
            grid_state['active_camera'] = camera_id
        elif grid_state['intruder_pos'] and not grid_state.get('active_camera'):
            ix, iy = grid_state['intruder_pos']
            # Choose camera closest to intruder
            closest_cam = 'camara_1'
            min_d = 999
            for c in p_state.get('camaras', []):
                d = abs(c['x'] - ix) + abs(c['y'] - iy)
                if d < min_d:
                    min_d = d
                    closest_cam = c['id']
            grid_state['active_camera'] = closest_cam
            
        # Update vision logs
        vis_data = vision_system.get_cell_image_and_process(
            {
                'celdas': p_state['celdas'],
                'guardian_pos': grid_state['guardian_pos'],
                'intruder_pos': grid_state['intruder_pos'],
                'intruder_conf': grid_state['intruder_conf'],
                'camaras': p_state['camaras']
            },
            grid_state['active_camera']
        )
        grid_state['vision_logs'] = vis_data
        
        # Threat evaluation via Prolog
        if grid_state['intruder_pos']:
            # Determine zone
            # Row 1, 3, 5 are shelf zones.
            iy = grid_state['intruder_pos'][1]
            zona = 'restringida' if iy in (1, 3, 5) else 'publica'
            # Let's say it's night time
            threat_eval = get_prolog_threat_check('intruso', zona, 'noche')
            grid_state['threat_level'] = threat_eval['nivel']
            grid_state['threat_chain'] = threat_eval['cadena_inferencia']
        else:
            grid_state['threat_level'] = 'ninguno'
            grid_state['threat_chain'] = []
            
        return {
            'grid': p_state['celdas'],
            'stock': p_state['stock'],
            'camaras': p_state['camaras'],
            'alarmas': p_state['alarmas'],
            'guardian_pos': grid_state['guardian_pos'],
            'intruder_pos': grid_state['intruder_pos'],
            'intruder_confirmed': grid_state['intruder_confirmed'],
            'active_camera': grid_state['active_camera'],
            'minimax_logs': grid_state['minimax_logs'],
            'vision_logs': grid_state['vision_logs'],
            'simulation_logs': grid_state['simulation_logs'],
            'game_over': grid_state['game_over'],
            'message': grid_state['message'],
            'threat_level': grid_state['threat_level'],
            'threat_chain': grid_state['threat_chain']
        }
    else:
        raise HTTPException(status_code=500, detail="Unable to retrieve Prolog state")

@app.post("/api/step")
def step_simulation(camera_id: str = None):
    if grid_state['game_over']:
        return get_state(camera_id)
        
    p_state = fetch_prolog_state()
    if not p_state:
        raise HTTPException(status_code=500, detail="Prolog server offline")

    # Save old positions for sync
    old_g = list(grid_state['guardian_pos'])
    old_i = list(grid_state['intruder_pos']) if grid_state['intruder_pos'] else None

    # Check if there is an intruder
    if grid_state['intruder_pos']:
        # Run vision check to see if human confirmation is required
        vis_data = vision_system.get_cell_image_and_process(
            {
                'celdas': p_state['celdas'],
                'guardian_pos': grid_state['guardian_pos'],
                'intruder_pos': grid_state['intruder_pos'],
                'intruder_conf': grid_state['intruder_conf'],
                'camaras': p_state['camaras']
            },
            grid_state['active_camera']
        )
        
        # Ethics threshold check:
        # Confidence between 70% and 89% requires confirmation, if not already confirmed
        if vis_data['manual_confirmation_required'] and not grid_state['intruder_confirmed']:
            grid_state['message'] = "ALERTA: Detección en rango de sospecha (70%-89%). Simulación pausada esperando confirmación humana."
            return get_state(camera_id)

        # 1. Intruder's Turn:
        # Check if adjacent to a shelf (value 1) and rob it
        ix, iy = grid_state['intruder_pos']
        robbed = False
        
        # Check for adjacent shelves with stock > 0
        shelves_positions = {}
        for cell in p_state['celdas']:
            if cell['val'] == 1: # Full shelf
                shelves_positions[(cell['x'], cell['y'])] = True
                
        adjacent_shelf_pos = None
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            ax, ay = ix + dx, iy + dy
            if (ax, ay) in shelves_positions:
                adjacent_shelf_pos = (ax, ay)
                break
                
        if adjacent_shelf_pos:
            # Find which estante is at this position
            estante_id = None
            for s in p_state['stock']:
                # Find estante position from Prolog setup: we know by default Y=1,3,5 are shelves
                # Let's map positions:
                # estante_1: (1,1), estante_2: (3,1), estante_3: (5,1)
                # estante_4: (1,3), estante_5: (3,3), estante_6: (5,3)
                # estante_7: (1,5), estante_8: (5,5)
                # Let's dynamically locate it
                # We can call Prolog stock update
                pass
            
            # Simple mapping
            pos_to_id = {
                (1,1): 'estante_1', (3,1): 'estante_2', (5,1): 'estante_3',
                (1,3): 'estante_4', (3,3): 'estante_5', (5,3): 'estante_6',
                (1,5): 'estante_7', (5,5): 'estante_8'
            }
            estante_id = pos_to_id.get(adjacent_shelf_pos)
            
            if estante_id:
                # Robbery! Set stock to 0
                requests.post(f"{prolog_url}/update_stock", json={'estante_id': estante_id, 'cantidad': 0})
                robbed = True
                grid_state['simulation_logs'].append(f"Intruso robó el {estante_id} en {adjacent_shelf_pos}. Stock reducido a 0 (Quiebre de Stock).")
                grid_state['message'] = f"¡Robo en progreso! Intruso vació el {estante_id}."
        
        if not robbed:
            # Move intruder towards closest full shelf, avoiding guardian
            new_i = find_best_move_intruder(grid_state['guardian_pos'], grid_state['intruder_pos'], p_state['celdas'])
            grid_state['intruder_pos'] = list(new_i)
            grid_state['simulation_logs'].append(f"Intruso se movió de {old_i} a {new_i}.")

        # 2. Guardian's Turn (Runs Minimax):
        weights = {'w1': 5.0, 'w2': 15.0, 'w3': 10.0}
        minimax_res = find_best_move_guardian(grid_state['guardian_pos'], grid_state['intruder_pos'], p_state['celdas'], weights)
        new_g = minimax_res['best_move']
        
        grid_state['guardian_pos'] = list(new_g)
        grid_state['minimax_logs'] = {
            'nodes_visited': minimax_res['nodes_visited'],
            'prunings': minimax_res['prunings'],
            'eval_value': minimax_res['eval_value'],
            'move': new_g
        }
        grid_state['simulation_logs'].append(
            f"Guardián se movió de {old_g} a {new_g}. Minimax evaluó {minimax_res['nodes_visited']} nodos con {minimax_res['prunings']} podas."
        )

        # 3. Sincronizar estados secuencialmente en Prolog
        sync_agent_positions_to_prolog(old_g, grid_state['guardian_pos'], old_i, grid_state['intruder_pos'])

        # Check if intruder is caught
        if grid_state['guardian_pos'] == grid_state['intruder_pos']:
            grid_state['game_over'] = True
            grid_state['message'] = "¡ÉXITO: El Guardián ha capturado al Intruso!"
            grid_state['simulation_logs'].append("Intruso capturado por el Guardián. Amenaza neutralizada.")
            # Clear intruder from Prolog grid
            requests.post(f"{prolog_url}/update_grid", json={'x': grid_state['intruder_pos'][0], 'y': grid_state['intruder_pos'][1], 'val': 0})
            grid_state['intruder_pos'] = None
    else:
        # No intruder, patrol or simulation finished
        grid_state['game_over'] = True
        grid_state['message'] = "Simulación terminada. No hay amenazas activas."

    return get_state(camera_id)

@app.post("/api/action/confirm")
def confirm_threat(camera_id: str = None):
    grid_state['intruder_confirmed'] = True
    # Boost confidence to 100% to simulate confirmed alert
    grid_state['intruder_conf'] = 0.99
    grid_state['message'] = "Amenaza confirmada manualmente por el operador. Alarmas activadas."
    grid_state['simulation_logs'].append("Operador confirmó la amenaza de intrusión manualmente.")
    return get_state(camera_id)

@app.post("/api/action/discard")
def discard_threat(camera_id: str = None):
    old_i = list(grid_state['intruder_pos']) if grid_state['intruder_pos'] else None
    grid_state['intruder_pos'] = None
    grid_state['intruder_confirmed'] = False
    grid_state['message'] = "Detección descartada como falsa alarma por el operador."
    grid_state['simulation_logs'].append("Operador descartó la alerta de intrusión.")
    
    # Remove intruder from Prolog grid
    if old_i:
        try:
            requests.post(f"{prolog_url}/update_grid", json={'x': old_i[0], 'y': old_i[1], 'val': 0})
        except (requests.RequestException, Exception) as e:
            print(f"[WARN] Error al limpiar posición del intruso en Prolog: {e}")
            grid_state['simulation_logs'].append(f"Advertencia: No se pudo sincronizar la eliminación del intruso con Prolog.")
            
    return get_state(camera_id)

@app.post("/api/update_stock")
def update_stock(data: StockUpdate, camera_id: str = None):
    try:
        r = requests.post(f"{prolog_url}/update_stock", json={
            'estante_id': data.estante_id,
            'cantidad': data.cantidad
        })
        if r.status_code == 200:
            grid_state['simulation_logs'].append(f"Stock del {data.estante_id} actualizado manualmente a {data.cantidad}.")
            return get_state(camera_id)
        else:
            raise HTTPException(status_code=r.status_code, detail=r.json().get('message', 'Prolog update error'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_copilot(req: ChatRequest):
    try:
        user_msg = req.message.strip()
        user_msg_lower = user_msg.lower()
        
        # Fetch current Prolog threat chain
        if grid_state['intruder_pos']:
            iy = grid_state['intruder_pos'][1]
            zona = 'restringida' if iy in (1, 3, 5) else 'publica'
            threat_eval = get_prolog_threat_check('intruso', zona, 'noche')
            chain = threat_eval.get('cadena_inferencia', ['error_comunicacion'])
        else:
            # Check stockouts
            p_state = fetch_prolog_state()
            empty_shelves = []
            if p_state and 'stock' in p_state:
                for s in p_state['stock']:
                    if s.get('cantidad', 0) == 0:
                        empty_shelves.append(f"{s.get('estante_id', 'desconocido')}_vacio")
            if empty_shelves:
                chain = ["quiebre_stock"] + empty_shelves
            else:
                chain = ["estado_normal", "almacen_seguro"]
                
        # If it is a generic status update request
        if user_msg_lower == "explain current status" or not user_msg:
            explanation = explain_inference_chain_with_gemini(chain)
            return {"reply": explanation}
            
        # Get active database state
        p_state = fetch_prolog_state()
        
        # For custom chat queries, handle with Gemini or Local Fallback
        reply = get_chat_response_with_gemini_or_fallback(user_msg, chain, p_state)
        return {"reply": reply}
    except Exception as e:
        print(f"[ERROR CHAT] {str(e)}")
        return {"reply": f"[Copiloto Local] Error interno: {str(e)}"}

@app.post("/api/reset")
def reset_simulation(camera_id: str = None):
    global grid_state
    grid_state = {
        'guardian_pos': [3, 5],
        'intruder_pos': [2, 1],
        'intruder_conf': 0.85,
        'intruder_confirmed': False,
        'active_camera': camera_id if camera_id else 'camara_1',
        'simulation_logs': [],
        'minimax_logs': None,
        'vision_logs': None,
        'game_over': False,
        'message': "Simulación reiniciada. Intruso detectado con confianza del 85%. Requiere confirmación manual."
    }
    # Reset Prolog database
    try:
        # Prolog server has an init_db rule, but restarting it or calling its update endpoint is enough.
        # Let's update agent positions in Prolog
        requests.get(f"{prolog_url}/state") # Trigger initial load
        # Sync default grid values in Prolog (we can do a simple reset by posting positions)
        requests.post(f"{prolog_url}/update_grid", json={'x': 3, 'y': 5, 'val': 2})
        requests.post(f"{prolog_url}/update_grid", json={'x': 2, 'y': 1, 'val': 3})
        # Reset stocks
        for i in range(1, 9):
            requests.post(f"{prolog_url}/update_stock", json={'estante_id': f'estante_{i}', 'cantidad': 10 if i != 4 and i != 2 else (5 if i==4 else 8)})
    except Exception as e:
        print(f"Error resetting Prolog grid: {e}")
        
    return get_state(camera_id)

# Serve Frontend static files
# Make sure directory path exists
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

app.mount("/", StaticFiles(directory=frontend_path), name="frontend")
