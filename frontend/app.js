// Global Variables
const API_URL = ""; // Relative path works since we are serving files from the same FastAPI server
let autoSimInterval = null;
let currentCamera = "camara_1";
let selectedCell = null;

// DOM Elements
const canvas = document.getElementById("warehouseCanvas");
const ctx = canvas.getContext("2d");
const btnStep = document.getElementById("btnStep");
const btnAuto = document.getElementById("btnAuto");
const btnReset = document.getElementById("btnReset");
const cameraSelector = document.getElementById("cameraSelector");
const threatAlertBox = document.getElementById("threatAlertBox");
const btnConfirmThreat = document.getElementById("btnConfirmThreat");
const btnDiscardThreat = document.getElementById("btnDiscardThreat");
const stockControlsGrid = document.getElementById("stockControlsGrid");
const inferenceTerminal = document.getElementById("inferenceTerminal");
const minimaxTerminal = document.getElementById("minimaxTerminal");
const copilotResponse = document.getElementById("copilotResponse");
const chatInput = document.getElementById("chatInput");
const btnSendChat = document.getElementById("btnSendChat");

// Metric Elements
const valNodes = document.getElementById("valNodes");
const valPrunings = document.getElementById("valPrunings");
const valHeuristic = document.getElementById("valHeuristic");

// Image elements
const imgYolo = document.getElementById("imgYolo");
const imgOriginal = document.getElementById("imgOriginal");
const imgGrayscale = document.getElementById("imgGrayscale");
const imgBlur = document.getElementById("imgBlur");
const imgCanny = document.getElementById("imgCanny");

// Alarm elements
const alarmIntrusion = document.getElementById("alarmIntrusion");
const alarmReplenishment = document.getElementById("alarmReplenishment");

// Tab links
const tabLinks = document.querySelectorAll(".tab-link");
const tabPanels = document.querySelectorAll(".tab-panel");

// Setup Tabs
tabLinks.forEach(link => {
    link.addEventListener("click", () => {
        tabLinks.forEach(l => l.classList.remove("active"));
        tabPanels.forEach(p => p.classList.remove("active"));
        
        link.classList.add("active");
        const targetId = link.getAttribute("data-target");
        document.getElementById(targetId).classList.add("active");
    });
});

// Init Event Listeners
btnStep.addEventListener("click", stepSimulation);
btnAuto.addEventListener("click", toggleAutoSimulation);
btnReset.addEventListener("click", resetSimulation);
btnConfirmThreat.addEventListener("click", confirmThreat);
btnDiscardThreat.addEventListener("click", discardThreat);
btnSendChat.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendChatMessage();
});

cameraSelector.addEventListener("change", (e) => {
    currentCamera = e.target.value;
    fetchState();
});

// Initial Load
window.addEventListener("DOMContentLoaded", () => {
    fetchState();
});

// Canvas Drawing function
function drawGrid(gridData, guardianPos, intruderPos, camaras) {
    const cellSize = canvas.width / 5;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw cells
    gridData.forEach(cell => {
        const x = (cell.x - 1) * cellSize;
        const y = (cell.y - 1) * cellSize;
        const val = cell.val;
        
        // Base Drawing
        if (val === 1) {
            // Full Shelf (Blue)
            ctx.fillStyle = "#1e293b";
            ctx.fillRect(x, y, cellSize, cellSize);
            ctx.strokeStyle = "#3b82f6";
            ctx.lineWidth = 3;
            ctx.strokeRect(x + 4, y + 4, cellSize - 8, cellSize - 8);
            
            // Draw visual products inside shelf
            ctx.fillStyle = "#3b82f6";
            ctx.fillRect(x + 10, y + 10, cellSize - 20, cellSize - 20);
        } else if (val === 10) {
            // Empty Shelf / Stockout (Blinking Orange-Red)
            ctx.fillStyle = "#1e293b";
            ctx.fillRect(x, y, cellSize, cellSize);
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 3;
            ctx.strokeRect(x + 4, y + 4, cellSize - 8, cellSize - 8);
            
            // Draw Empty indicator
            ctx.fillStyle = "rgba(239, 68, 68, 0.2)";
            ctx.fillRect(x + 10, y + 10, cellSize - 20, cellSize - 20);
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 1;
            ctx.strokeRect(x + 12, y + 12, cellSize - 24, cellSize - 24);
        } else {
            // Path (val === 0)
            ctx.fillStyle = "#0f172a";
            ctx.fillRect(x, y, cellSize, cellSize);
            ctx.strokeStyle = "rgba(255,255,255,0.03)";
            ctx.lineWidth = 1;
            ctx.strokeRect(x, y, cellSize, cellSize);
            
            // Grid point dots in path
            ctx.fillStyle = "rgba(255,255,255,0.15)";
            ctx.beginPath();
            ctx.arc(x + cellSize / 2, y + cellSize / 2, 2, 0, 2 * Math.PI);
            ctx.fill();
        }
    });

    // Draw Cameras
    camaras.forEach(cam => {
        const x = (cam.x - 1) * cellSize + cellSize / 2;
        const y = (cam.y - 1) * cellSize + cellSize / 2;
        
        ctx.fillStyle = cam.id === currentCamera ? "#00f2fe" : "#ffb703";
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        
        // Draw small camera triangle/symbol
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
        
        // Label
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 8px Outfit";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(cam.id.split("_")[1], x, y);
    });

    // Draw Guardian
    if (guardianPos) {
        const x = (guardianPos[0] - 1) * cellSize + cellSize / 2;
        const y = (guardianPos[1] - 1) * cellSize + cellSize / 2;
        
        // Glow effect
        ctx.shadowBlur = 15;
        ctx.shadowColor = "#00f2fe";
        
        ctx.fillStyle = "#00f2fe";
        ctx.beginPath();
        ctx.arc(x, y, cellSize * 0.28, 0, 2 * Math.PI);
        ctx.fill();
        
        // Reset shadow
        ctx.shadowBlur = 0;
        
        // Shield outline
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, cellSize * 0.28, 0, 2 * Math.PI);
        ctx.stroke();
        
        // Text label
        ctx.fillStyle = "#0b0f19";
        ctx.font = "bold 14px Outfit";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("G", x, y);
    }

    // Draw Intruder
    if (intruderPos) {
        const x = (intruderPos[0] - 1) * cellSize + cellSize / 2;
        const y = (intruderPos[1] - 1) * cellSize + cellSize / 2;
        
        // Blinking Glow effect
        const t = new Date().getTime();
        const glow = 10 + Math.sin(t / 100) * 8;
        
        ctx.shadowBlur = glow;
        ctx.shadowColor = "#ff073a";
        
        ctx.fillStyle = "#ff073a";
        ctx.beginPath();
        ctx.arc(x, y, cellSize * 0.28, 0, 2 * Math.PI);
        ctx.fill();
        
        ctx.shadowBlur = 0;
        
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, cellSize * 0.28, 0, 2 * Math.PI);
        ctx.stroke();
        
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 14px Outfit";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("I", x, y);
    }
}

// Fetch general state
async function fetchState() {
    try {
        const res = await fetch(`${API_URL}/api/state?camera_id=${currentCamera}`);
        if (!res.ok) throw new Error("Error fetching simulation state");
        const data = await res.json();
        updateUI(data);
    } catch (err) {
        console.error(err);
    }
}

// Execute 1 single step
async function stepSimulation() {
    try {
        const res = await fetch(`${API_URL}/api/step?camera_id=${currentCamera}`, { method: "POST" });
        if (!res.ok) throw new Error("Error in execution step");
        const data = await res.json();
        updateUI(data);
        
        // Automatically fetch copilot explanation when a threat update happens
        if (data.threat_chain && data.threat_chain.length > 0) {
            triggerCopilotTranslation();
        }
    } catch (err) {
        console.error(err);
    }
}

// Confirm alert
async function confirmThreat() {
    try {
        const res = await fetch(`${API_URL}/api/action/confirm?camera_id=${currentCamera}`, { method: "POST" });
        if (!res.ok) throw new Error("Error confirming threat");
        const data = await res.json();
        updateUI(data);
        triggerCopilotTranslation();
    } catch (err) {
        console.error(err);
    }
}

// Discard alert
async function discardThreat() {
    try {
        const res = await fetch(`${API_URL}/api/action/discard?camera_id=${currentCamera}`, { method: "POST" });
        if (!res.ok) throw new Error("Error discarding threat");
        const data = await res.json();
        updateUI(data);
    } catch (err) {
        console.error(err);
    }
}

// Reset
async function resetSimulation() {
    try {
        if (autoSimInterval) {
            toggleAutoSimulation(); // stop auto run
        }
        const res = await fetch(`${API_URL}/api/reset?camera_id=${currentCamera}`, { method: "POST" });
        if (!res.ok) throw new Error("Error resetting simulation");
        const data = await res.json();
        // Reset current positions to avoid jerky transitions
        currentG = null;
        currentI = null;
        updateUI(data);
        
        inferenceTerminal.innerHTML = "Base de datos reseteada.<br>Hechos actualizados.";
        minimaxTerminal.innerHTML = "Búsqueda reiniciada.";
    } catch (err) {
        console.error(err);
    }
}

// Auto-run loop
function toggleAutoSimulation() {
    if (autoSimInterval) {
        clearInterval(autoSimInterval);
        autoSimInterval = null;
        btnAuto.textContent = "AUTO-SIMULACIÓN: OFF";
        btnAuto.classList.remove("btn-primary");
        btnAuto.classList.add("btn-secondary");
    } else {
        autoSimInterval = setInterval(async () => {
            await stepSimulation();
        }, 1500);
        btnAuto.textContent = "AUTO-SIMULACIÓN: ON";
        btnAuto.classList.remove("btn-secondary");
        btnAuto.classList.add("btn-primary");
    }
}

// Dynamic stocks updates
async function updateStockQty(estanteId, quantity) {
    try {
        const res = await fetch(`${API_URL}/api/update_stock?camera_id=${currentCamera}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ estante_id: estanteId, cantidad: parseInt(quantity) })
        });
        if (!res.ok) throw new Error("Error updating stock quantity");
        const data = await res.json();
        updateUI(data);
    } catch (err) {
        console.error(err);
    }
}

// Send Gemini chat query
async function sendChatMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    copilotResponse.innerHTML = '<span class="txt-neon-blue">Pensando...</span>';
    chatInput.value = "";
    
    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        if (!res.ok) throw new Error("Error in copilot request");
        const data = await res.json();
        copilotResponse.textContent = data.reply;
    } catch (err) {
        copilotResponse.textContent = `Error: ${err.message}`;
    }
}

// Trigger Gemini Translation of current Prolog facts
async function triggerCopilotTranslation() {
    try {
        const res = await fetch(`${API_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: "Explain current status" })
        });
        if (res.ok) {
            const data = await res.json();
            copilotResponse.textContent = data.reply;
        }
    } catch (err) {
        console.error("Gemini automatic translation failed", err);
    }
}

// Update complete dashboard GUI
let latestGrid = [];
let latestCameras = [];
let currentG = null;
let currentI = null;
let targetG = null;
let targetI = null;
let animFrameId = null;

function startAnimation() {
    if (!animFrameId) {
        animFrameId = requestAnimationFrame(animationLoop);
    }
}

function animationLoop() {
    let needsMore = false;
    const ease = 0.15; // smooth animation interpolation factor
    
    if (targetG) {
        if (!currentG) {
            currentG = { x: targetG[0], y: targetG[1] };
        } else {
            const dx = targetG[0] - currentG.x;
            const dy = targetG[1] - currentG.y;
            if (Math.abs(dx) > 0.005 || Math.abs(dy) > 0.005) {
                currentG.x += dx * ease;
                currentG.y += dy * ease;
                needsMore = true;
            } else {
                currentG.x = targetG[0];
                currentG.y = targetG[1];
            }
        }
    } else {
        currentG = null;
    }
    
    if (targetI) {
        if (!currentI) {
            currentI = { x: targetI[0], y: targetI[1] };
        } else {
            const dx = targetI[0] - currentI.x;
            const dy = targetI[1] - currentI.y;
            if (Math.abs(dx) > 0.005 || Math.abs(dy) > 0.005) {
                currentI.x += dx * ease;
                currentI.y += dy * ease;
                needsMore = true;
            } else {
                currentI.x = targetI[0];
                currentI.y = targetI[1];
            }
        }
    } else {
        currentI = null;
    }
    
    if (latestGrid && latestCameras) {
        drawGrid(
            latestGrid, 
            currentG ? [currentG.x, currentG.y] : null, 
            currentI ? [currentI.x, currentI.y] : null, 
            latestCameras
        );
    }
    
    if (needsMore) {
        animFrameId = requestAnimationFrame(animationLoop);
    } else {
        animFrameId = null;
    }
}

function updateUI(data) {
    if (!data) return;

    latestGrid = data.grid;
    latestCameras = data.camaras;
    targetG = data.guardian_pos;
    targetI = data.intruder_pos;

    // Trigger smooth transition animation
    startAnimation();
    
    // 2. Ethics Warning Alert Box
    const threatAlertMsgEl = document.getElementById("threatAlertMsg");
    if (data.vision_logs && data.vision_logs.manual_confirmation_required && !data.intruder_confirmed) {
        threatAlertBox.classList.remove("hidden");
        const det = data.vision_logs.unconfirmed_detection;
        if (det && threatAlertMsgEl) {
            threatAlertMsgEl.innerHTML = `Detección de <strong>${det.class || 'Desconocido'}</strong> con <strong>${(det.conf ? (det.conf*100).toFixed(1) : '?')}%</strong> de confianza. ¿Confirmar el despliegue del Guardián?`;
        }
        
        // Pause auto-sim if active
        if (autoSimInterval) {
            toggleAutoSimulation();
        }
    } else {
        threatAlertBox.classList.add("hidden");
    }

    // 3. Stock Controls panel
    if (data.stock) {
        renderStockControls(data.stock);
    }

    // 4. Update cameras pipeline Base64 views
    if (data.vision_logs) {
        if (data.vision_logs.yolo_detect) imgYolo.src = "data:image/jpeg;base64," + data.vision_logs.yolo_detect;
        if (data.vision_logs.original) imgOriginal.src = "data:image/jpeg;base64," + data.vision_logs.original;
        if (data.vision_logs.grayscale) imgGrayscale.src = "data:image/jpeg;base64," + data.vision_logs.grayscale;
        if (data.vision_logs.blur) imgBlur.src = "data:image/jpeg;base64," + data.vision_logs.blur;
        if (data.vision_logs.canny) imgCanny.src = "data:image/jpeg;base64," + data.vision_logs.canny;
    }

    // 5. Alarms State UI
    let alarmIntrusionActive = false;
    let alarmReplenishmentActive = false;
    
    if (data.alarmas) {
        data.alarmas.forEach(al => {
            if (al.tipo === "intrusion" && al.estado === "activa") alarmIntrusionActive = true;
            if (al.tipo === "reabastecimiento" && al.estado === "activa") alarmReplenishmentActive = true;
        });
    }

    if (alarmIntrusionActive) {
        alarmIntrusion.textContent = "Intrusión: ACTIVA";
        alarmIntrusion.classList.add("active");
    } else {
        alarmIntrusion.textContent = "Intrusión: OFF";
        alarmIntrusion.classList.remove("active");
    }

    if (alarmReplenishmentActive) {
        alarmReplenishment.textContent = "Quiebre: ACTIVA";
        alarmReplenishment.classList.add("active");
    } else {
        alarmReplenishment.textContent = "Quiebre: OFF";
        alarmReplenishment.classList.remove("active");
    }

    // 6. Prolog Inferences Terminal
    let factsHtml = `<strong>FACTS DATABASE (Prolog active list):</strong><br>`;
    if (data.grid) {
        data.grid.forEach(cell => {
            if (cell.val !== 0) {
                factsHtml += `celda(${cell.x}, ${cell.y}, ${cell.val}).<br>`;
            }
        });
    }
    if (data.stock) {
        data.stock.forEach(st => {
            factsHtml += `estante_producto(${st.estante_id}, "${st.producto}", ${st.cantidad}, ${st.max_cap}).<br>`;
        });
    }
    
    if (data.threat_chain && data.threat_chain.length > 0) {
        factsHtml += `<br><span style="color: var(--neon-red)"><strong>INFERENCIA DE AMENAZAS:</strong><br>${data.threat_chain.join(" -> ")} (Nivel: ${(data.threat_level || 'N/A').toUpperCase()})</span>`;
    } else {
        factsHtml += `<br><span style="color: var(--neon-green)"><strong>ESTADO SEGURO:</strong><br>Sin intrusiones detectadas.</span>`;
    }
    inferenceTerminal.innerHTML = factsHtml;

    // 7. Minimax Search Metrics
    if (data.minimax_logs) {
        valNodes.textContent = data.minimax_logs.nodes_visited || 0;
        valPrunings.textContent = data.minimax_logs.prunings || 0;
        valHeuristic.textContent = (data.minimax_logs.eval_value != null) ? data.minimax_logs.eval_value.toFixed(2) : "0.00";
        
        const gPos = data.guardian_pos ? `(${data.guardian_pos[0]}, ${data.guardian_pos[1]})` : 'N/A';
        const iPos = data.intruder_pos ? `(${data.intruder_pos[0]}, ${data.intruder_pos[1]})` : 'Capturado';
        const mMove = data.minimax_logs.move ? `(${data.minimax_logs.move[0]}, ${data.minimax_logs.move[1]})` : 'N/A';
        
        let miniLog = `[Turno Guardián]<br>`;
        miniLog += `• Posición Guardián: ${gPos}<br>`;
        miniLog += `• Posición Intruso: ${iPos}<br>`;
        miniLog += `• Mejor movimiento calculado: ${mMove}<br>`;
        miniLog += `• Calificación heurística óptima: ${(data.minimax_logs.eval_value != null) ? data.minimax_logs.eval_value.toFixed(2) : '0.00'}<br>`;
        miniLog += `• Prunings ejecutadas: ${data.minimax_logs.prunings || 0}<br>`;
        minimaxTerminal.innerHTML = miniLog;
    } else {
        valNodes.textContent = "0";
        valPrunings.textContent = "0";
        valHeuristic.textContent = "0.00";
    }

    // 8. Header / Logs updates
    if (data.game_over) {
        if (autoSimInterval) {
            toggleAutoSimulation();
        }
    }
}

// Render inputs for manual stock updates
function renderStockControls(stockList) {
    // Clear and redraw if number of inputs mismatch or on first draw
    if (stockControlsGrid.children.length === 0) {
        stockList.forEach(st => {
            const item = document.createElement("div");
            item.className = "stock-item";
            
            const isStockout = st.cantidad <= 2;
            item.innerHTML = `
                <span class="label">${st.producto}</span>
                <span class="qty ${isStockout ? 'stockout' : ''}" id="qty-${st.estante_id}">${st.cantidad}</span>
                <input type="number" min="0" max="${st.max_cap}" value="${st.cantidad}" data-id="${st.estante_id}">
            `;
            
            // Add input change listener
            const input = item.querySelector("input");
            input.addEventListener("change", (e) => {
                const estanteId = e.target.getAttribute("data-id");
                const val = e.target.value;
                updateStockQty(estanteId, val);
            });
            
            stockControlsGrid.appendChild(item);
        });
    } else {
        // Just update quantities and values
        stockList.forEach(st => {
            const qtySpan = document.getElementById(`qty-${st.estante_id}`);
            if (qtySpan) {
                qtySpan.textContent = st.cantidad;
                const isStockout = st.cantidad <= 2;
                if (isStockout) qtySpan.classList.add("stockout");
                else qtySpan.classList.remove("stockout");
            }
            const input = stockControlsGrid.querySelector(`input[data-id="${st.estante_id}"]`);
            if (input && document.activeElement !== input) {
                input.value = st.cantidad;
            }
        });
    }
}

// Animation loop to blink empty shelves
setInterval(() => {
    // Trigger simple redraw or rely on CSS animation
}, 500);

// Canvas click listener to support interactive play (user controls the Intruder!)
canvas.addEventListener("click", async (e) => {
    // If auto simulation is currently active, ignore manual moves
    if (autoSimInterval) return;
    
    // Calculate clicked cell coordinates (1-indexed, 5x5 grid)
    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    // Scale according to actual canvas display size vs internal coordinates
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    
    const internalX = clickX * scaleX;
    const internalY = clickY * scaleY;
    
    const cellSize = canvas.width / 5;
    const cellX = Math.floor(internalX / cellSize) + 1;
    const cellY = Math.floor(internalY / cellSize) + 1;
    
    // Send step command with target coordinates to FastAPI
    try {
        const res = await fetch(`${API_URL}/api/step?camera_id=${currentCamera}&intruder_x=${cellX}&intruder_y=${cellY}`, { method: "POST" });
        if (!res.ok) throw new Error("Error executing manual play step");
        const data = await res.json();
        updateUI(data);
        
        // Automatically fetch copilot explanation when a threat update happens
        if (data.threat_chain && data.threat_chain.length > 0) {
            triggerCopilotTranslation();
        }
    } catch (err) {
        console.error("Manual move failed", err);
    }
});
