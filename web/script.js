// ============================================
// ARK-II · Web UI
// Talks to server.py (localhost:8000) via /state and /command
// ============================================

const SERVER = "http://127.0.0.1:8000";

// ============================================
// 1. RING VISUALIZER (canvas)
// ============================================
const canvas = document.getElementById("ring");
const ctx = canvas.getContext("2d");

let W = 0, H = 0, CX = 0, CY = 0, R = 0;
let phase = 0;
let smoothed = 0;
let targetEnergy = 0;
let currentStatus = "idle";

function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const rect = canvas.parentElement.getBoundingClientRect();
    W = rect.width;
    H = rect.height;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    CX = W / 2;
    CY = H / 2;
    R = Math.min(W, H) * 0.22;
}

window.addEventListener("resize", resize);

function energyForState(status) {
    if (status === "speaking") return 1.0;
    if (status === "thinking") return 0.55;
    return 0.18;
}

function draw() {
    phase += 0.012 + smoothed * 0.06;
    smoothed += (targetEnergy - smoothed) * 0.06;

    ctx.clearRect(0, 0, W, H);

    const accent = { r: 0, g: 229, b: 255 };
    const warn = { r: 255, g: 179, b: 71 };
    const color = currentStatus === "thinking" ? warn : accent;

    // Outer halo
    const halo = ctx.createRadialGradient(CX, CY, R * 0.4, CX, CY, R * 2.4);
    halo.addColorStop(0, `rgba(${color.r},${color.g},${color.b}, ${0.06 + smoothed * 0.10})`);
    halo.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, W, H);

    // Static outline
    ctx.beginPath();
    ctx.arc(CX, CY, R * 1.5, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(CX, CY, R * 1.5 + 14, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,255,255,0.02)";
    ctx.stroke();

    // Rotating segments
    const segs = 72;
    for (let i = 0; i < segs; i++) {
        const angle = (i / segs) * Math.PI * 2 + phase * 0.5;
        const wave = Math.sin(phase * 3 + i * 0.4) * 0.5 + 0.5;
        const len = R * (0.06 + smoothed * 0.42 * wave);

        const x1 = CX + Math.cos(angle) * (R * 1.5 - len);
        const y1 = CY + Math.sin(angle) * (R * 1.5 - len);
        const x2 = CX + Math.cos(angle) * (R * 1.5);
        const y2 = CY + Math.sin(angle) * (R * 1.5);

        const alpha = 0.08 + smoothed * 0.55 * wave;
        ctx.strokeStyle = `rgba(${color.r},${color.g},${color.b}, ${alpha})`;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
    }

    // Inner ring
    ctx.beginPath();
    ctx.arc(CX, CY, R * 0.9, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(${color.r},${color.g},${color.b}, ${0.15 + smoothed * 0.4})`;
    ctx.lineWidth = 1;
    ctx.stroke();

    // Core dot
    const coreR = R * (0.18 + smoothed * 0.22);
    const core = ctx.createRadialGradient(CX, CY, 0, CX, CY, coreR);
    core.addColorStop(0, `rgba(255,255,255, ${0.55 + smoothed * 0.4})`);
    core.addColorStop(0.4, `rgba(${color.r},${color.g},${color.b}, ${0.5 + smoothed * 0.3})`);
    core.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = core;
    ctx.beginPath();
    ctx.arc(CX, CY, coreR, 0, Math.PI * 2);
    ctx.fill();

    // Orbiting particle
    const orbitAngle = phase * 1.6;
    const ox = CX + Math.cos(orbitAngle) * R * 1.15;
    const oy = CY + Math.sin(orbitAngle) * R * 1.15;
    ctx.beginPath();
    ctx.arc(ox, oy, 2.4, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${color.r},${color.g},${color.b}, ${0.5 + smoothed * 0.5})`;
    ctx.shadowColor = `rgba(${color.r},${color.g},${color.b}, 0.8)`;
    ctx.shadowBlur = 12 + smoothed * 20;
    ctx.fill();
    ctx.shadowBlur = 0;

    requestAnimationFrame(draw);
}

resize();
requestAnimationFrame(draw);

// ============================================
// 2. DOM ELEMENTS
// ============================================
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const stageLabel = document.getElementById("stage-label");
const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const clockEl = document.getElementById("clock");

// ============================================
// 3. STATE POLLING
// ============================================
let lastHistoryCount = -1;

async function poll() {
    try {
        const res = await fetch(SERVER + "/state", { cache: "no-store" });
        const state = await res.json();

        statusDot.className = "status-dot online";
        statusText.textContent = "online";

        applyState(state);
    } catch (e) {
        statusDot.className = "status-dot offline";
        statusText.textContent = "offline";
    }
}

function applyState(state) {
    // Ring energy
    currentStatus = state.status || "idle";
    targetEnergy = energyForState(currentStatus);

    // Stage label
    stageLabel.textContent = currentStatus;
    stageLabel.className = "stage-label " + currentStatus;

    // Chat
    renderChat(state.history || []);
}

setInterval(poll, 500);
poll();

// ============================================
// 4. CHAT RENDERING
// ============================================
function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[c]));
}

function renderChat(history) {
    if (history.length === lastHistoryCount) return;
    lastHistoryCount = history.length;

    chatEl.innerHTML = "";

    if (history.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.innerHTML = `<div class="empty-line">◈</div><div class="empty-text">Ready when you are.</div>`;
        chatEl.appendChild(empty);
        return;
    }

    for (const msg of history) {
        const isUser = msg.role === "user";
        const div = document.createElement("div");
        div.className = "message " + (isUser ? "user" : "ark");

        const who = document.createElement("div");
        who.className = "who";
        who.textContent = isUser ? "you" : "ark";

        const what = document.createElement("div");
        what.className = "what";
        what.textContent = msg.content;

        div.appendChild(who);
        div.appendChild(what);
        chatEl.appendChild(div);
    }

    chatEl.scrollTop = chatEl.scrollHeight;
}

// ============================================
// 5. SEND COMMANDS
// ============================================
async function sendCommand(text) {
    const val = (text || "").trim();
    if (!val) return;

    try {
        await fetch(SERVER + "/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: val })
        });
        // Immediate poll to feel responsive
        setTimeout(poll, 150);
    } catch (e) {
        console.error("send failed:", e);
    }
}

sendBtn.addEventListener("click", () => {
    const val = inputEl.value;
    inputEl.value = "";
    sendCommand(val);
});

inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        sendBtn.click();
    }
});

// Ctrl+K focuses input
document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputEl.focus();
    }
    if (e.key === "Escape") {
        inputEl.blur();
    }
});

// ============================================
// 6. CLOCK
// ============================================
function tick() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    clockEl.textContent = `${hh}:${mm}`;
}

setInterval(tick, 1000);
tick();
