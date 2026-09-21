// ============================================
// ARK-II · Chat Page
// Background ring + chat log + input + sidebar
// ============================================

const SERVER = "http://127.0.0.1:8000";

// ============================================
// 1. BACKGROUND RING
// ============================================
const ringCanvas = document.getElementById("bg-ring");
const rctx = ringCanvas.getContext("2d");

let W = 0, H = 0, CX = 0, CY = 0, R = 0;
let phase = 0;
let smoothed = 0;
let targetEnergy = 0;
let rstatus = "idle";

function resizeRing() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    W = window.innerWidth;
    H = window.innerHeight;
    ringCanvas.width = W * dpr;
    ringCanvas.height = H * dpr;
    ringCanvas.style.width = W + "px";
    ringCanvas.style.height = H + "px";
    rctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    CX = W / 2;
    CY = H / 2;
    R = Math.min(W, H) * 0.32;
}

window.addEventListener("resize", resizeRing);

function energyForState(status) {
    if (status === "speaking") return 1.0;
    if (status === "thinking") return 0.6;
    return 0.15;
}

function drawRing() {
    phase += 0.01 + smoothed * 0.05;
    smoothed += (targetEnergy - smoothed) * 0.05;

    rctx.clearRect(0, 0, W, H);

    const accent = { r: 0, g: 229, b: 255 };
    const warn = { r: 255, g: 179, b: 71 };
    const color = rstatus === "thinking" ? warn : accent;

    // Outer halo
    const halo = rctx.createRadialGradient(CX, CY, R * 0.4, CX, CY, R * 2.4);
    halo.addColorStop(0, `rgba(${color.r},${color.g},${color.b}, ${0.04 + smoothed * 0.08})`);
    halo.addColorStop(1, "rgba(0,0,0,0)");
    rctx.fillStyle = halo;
    rctx.fillRect(0, 0, W, H);

    // Outer ring
    rctx.beginPath();
    rctx.arc(CX, CY, R * 1.6, 0, Math.PI * 2);
    rctx.strokeStyle = "rgba(255,255,255,0.025)";
    rctx.lineWidth = 1;
    rctx.stroke();

    rctx.beginPath();
    rctx.arc(CX, CY, R * 1.6 + 20, 0, Math.PI * 2);
    rctx.strokeStyle = "rgba(255,255,255,0.012)";
    rctx.stroke();

    // Rotating segments
    const segs = 96;
    for (let i = 0; i < segs; i++) {
        const angle = (i / segs) * Math.PI * 2 + phase * 0.4;
        const wave = Math.sin(phase * 3 + i * 0.35) * 0.5 + 0.5;
        const len = R * (0.05 + smoothed * 0.5 * wave);

        const x1 = CX + Math.cos(angle) * (R * 1.6 - len);
        const y1 = CY + Math.sin(angle) * (R * 1.6 - len);
        const x2 = CX + Math.cos(angle) * (R * 1.6);
        const y2 = CY + Math.sin(angle) * (R * 1.6);

        const alpha = 0.05 + smoothed * 0.5 * wave;
        rctx.strokeStyle = `rgba(${color.r},${color.g},${color.b}, ${alpha})`;
        rctx.lineWidth = 1.2;
        rctx.beginPath();
        rctx.moveTo(x1, y1);
        rctx.lineTo(x2, y2);
        rctx.stroke();
    }

    // Inner ring
    rctx.beginPath();
    rctx.arc(CX, CY, R * 0.95, 0, Math.PI * 2);
    rctx.strokeStyle = `rgba(${color.r},${color.g},${color.b}, ${0.1 + smoothed * 0.3})`;
    rctx.lineWidth = 1;
    rctx.stroke();

    // Core glow
    const coreR = R * (0.2 + smoothed * 0.2);
    const core = rctx.createRadialGradient(CX, CY, 0, CX, CY, coreR);
    core.addColorStop(0, `rgba(255,255,255, ${0.4 + smoothed * 0.4})`);
    core.addColorStop(0.4, `rgba(${color.r},${color.g},${color.b}, ${0.35 + smoothed * 0.3})`);
    core.addColorStop(1, "rgba(0,0,0,0)");
    rctx.fillStyle = core;
    rctx.beginPath();
    rctx.arc(CX, CY, coreR, 0, Math.PI * 2);
    rctx.fill();

    // Orbiting particle
    const orbitAngle = phase * 1.4;
    const ox = CX + Math.cos(orbitAngle) * R * 1.2;
    const oy = CY + Math.sin(orbitAngle) * R * 1.2;
    rctx.beginPath();
    rctx.arc(ox, oy, 2.4, 0, Math.PI * 2);
    rctx.fillStyle = `rgba(${color.r},${color.g},${color.b}, ${0.4 + smoothed * 0.5})`;
    rctx.shadowColor = `rgba(${color.r},${color.g},${color.b}, 0.7)`;
    rctx.shadowBlur = 12 + smoothed * 20;
    rctx.fill();
    rctx.shadowBlur = 0;

    requestAnimationFrame(drawRing);
}

resizeRing();
requestAnimationFrame(drawRing);

// ============================================
// 2. DOM ELEMENTS
// ============================================
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const micBtn = document.getElementById("mic-btn");
const clockEl = document.getElementById("clock");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");

// ============================================
// 3. SIDEBAR TOGGLE
// ============================================
sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
    sidebarToggle.textContent = sidebar.classList.contains("collapsed") ? "›" : "‹";
});

// ============================================
// 4. STATE POLLING
// ============================================
let lastHistoryCount = -1;

async function poll() {
    try {
        const res = await fetch(SERVER + "/state", { cache: "no-store" });
        const state = await res.json();

        statusDot.className = "status-dot online";
        statusText.textContent = "online";

        rstatus = state.status || "idle";
        targetEnergy = energyForState(rstatus);

        renderChat(state.history || []);
    } catch (e) {
        statusDot.className = "status-dot offline";
        statusText.textContent = "offline";
    }
}

setInterval(poll, 500);
poll();

// ============================================
// 5. CHAT RENDERING
// ============================================
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
        who.innerHTML = `
            <span class="label">${isUser ? "you" : "ark"}</span>
            <span class="time">${msg.time || ""}</span>
        `;

        const what = document.createElement("div");
        what.className = "what";
        what.textContent = msg.content;

        // Copy button on ARK messages only
        if (!isUser) {
            const copyBtn = document.createElement("button");
            copyBtn.className = "copy-btn";
            copyBtn.textContent = "copy";
            copyBtn.addEventListener("click", () => {
                navigator.clipboard.writeText(msg.content).then(() => {
                    copyBtn.textContent = "copied";
                    copyBtn.classList.add("copied");
                    setTimeout(() => {
                        copyBtn.textContent = "copy";
                        copyBtn.classList.remove("copied");
                    }, 1500);
                });
            });
            what.appendChild(copyBtn);
        }

        div.appendChild(who);
        div.appendChild(what);
        chatEl.appendChild(div);
    }

    chatEl.scrollTop = chatEl.scrollHeight;
}

// ============================================
// 6. SEND
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
// 7. CLOCK
// ============================================
function tick() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    clockEl.textContent = `${hh}:${mm}`;
}

setInterval(tick, 1000);
tick();
