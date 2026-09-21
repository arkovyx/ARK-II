const SERVER = "http://127.0.0.1:8000";

// ============================================
// FLOATING PARTICLES (attracted to cursor)
// ============================================
const particleCanvas = document.getElementById("bg-particles");
const pctx = particleCanvas.getContext("2d");

let PW = 0, PH = 0;
let particles = [];
const PARTICLE_COUNT = 70;
const CONNECTION_DIST = 150;
const MOUSE_RADIUS = 200;

const mouse = { x: -9999, y: -9999 };

function resizeParticles() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    PW = window.innerWidth;
    PH = window.innerHeight;
    particleCanvas.width = PW * dpr;
    particleCanvas.height = PH * dpr;
    particleCanvas.style.width = PW + "px";
    particleCanvas.style.height = PH + "px";
    pctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function initParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
            x: Math.random() * PW,
            y: Math.random() * PH,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            r: 1 + Math.random() * 1.5,
        });
    }
}

function updateParticles() {
    for (const p of particles) {
        // Cursor attraction
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < MOUSE_RADIUS && dist > 0.1) {
            const force = (1 - dist / MOUSE_RADIUS) * 0.05;
            p.vx += (dx / dist) * force;
            p.vy += (dy / dist) * force;
        }

        // Damping
        p.vx *= 0.98;
        p.vy *= 0.98;

        // Slight random drift
        p.vx += (Math.random() - 0.5) * 0.02;
        p.vy += (Math.random() - 0.5) * 0.02;

        // Move
        p.x += p.vx;
        p.vy *= 1;
        p.y += p.vy;

        // Wrap around edges
        if (p.x < 0) p.x = PW;
        if (p.x > PW) p.x = 0;
        if (p.y < 0) p.y = PH;
        if (p.y > PH) p.y = 0;
    }
}

function drawParticles() {
    pctx.clearRect(0, 0, PW, PH);

    // Connections
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const a = particles[i];
            const b = particles[j];
            const dx = a.x - b.x;
            const dy = a.y - b.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < CONNECTION_DIST) {
                const alpha = (1 - dist / CONNECTION_DIST) * 0.12;
                pctx.strokeStyle = `rgba(0, 229, 255, ${alpha})`;
                pctx.lineWidth = 0.5;
                pctx.beginPath();
                pctx.moveTo(a.x, a.y);
                pctx.lineTo(b.x, b.y);
                pctx.stroke();
            }
        }
    }

    // Dots
    for (const p of particles) {
        pctx.beginPath();
        pctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        pctx.fillStyle = "rgba(0, 229, 255, 0.4)";
        pctx.fill();
    }

    updateParticles();
    requestAnimationFrame(drawParticles);
}

window.addEventListener("resize", () => {
    resizeParticles();
});

window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

window.addEventListener("mouseleave", () => {
    mouse.x = -9999;
    mouse.y = -9999;
});

resizeParticles();
initParticles();
requestAnimationFrame(drawParticles);

// ============================================
// STATE POLLING
// ============================================
const statusDot = document.getElementById("status-dot");
const statusText = document.getElementById("status-text");
const clockEl = document.getElementById("clock");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");

sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
    sidebarToggle.textContent = sidebar.classList.contains("collapsed") ? "›" : "‹";
});

async function poll() {
    try {
        const res = await fetch(SERVER + "/state", { cache: "no-store" });
        await res.json();
        statusDot.className = "status-dot online";
        statusText.textContent = "online";
    } catch (e) {
        statusDot.className = "status-dot offline";
        statusText.textContent = "offline";
    }
}

setInterval(poll, 1000);
poll();

// ============================================
// CLOCK
// ============================================
function tick() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    clockEl.textContent = `${hh}:${mm}`;
}

setInterval(tick, 1000);
tick();
