/* ═══ Dialectic — App Logic ═══ */

let debateActive = false;
let startTime = 0;
let timerInterval = null;

// ── Initialization ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Initial UI state
    document.getElementById('wizardOverlay').classList.remove('hidden');

    // Fetch available models and warn if missing
    fetch('/api/models')
        .then(r => r.json())
        .then(data => {
            const startBtn = document.querySelector('.btn-start');
            if (data.models && data.models.length > 0) {
                const missing = data.models.filter(m => !m.installed);
                if (missing.length > 0) {
                    startBtn.innerText = "Error: Models Missing";
                    startBtn.style.backgroundColor = "#cc0000";
                    startBtn.disabled = true;
                }
            }
        }).catch(err => console.error("Error fetching models:", err));

    // Add Enter key support for topic input
    const topicInput = document.getElementById('topicInput');
    if (topicInput) {
        topicInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                initiateDebate();
            }
        });
    }

    // Add Enter key support for rebuttal input
    const rebuttalInput = document.getElementById('rebuttalInput');
    if (rebuttalInput) {
        rebuttalInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const btn = rebuttalInput.nextElementSibling;
                if (btn) btn.click();
            }
        });
    }
});

function startTimer() {
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const h = Math.floor(elapsed / 3600000).toString().padStart(2, '0');
        const m = Math.floor((elapsed % 3600000) / 60000).toString().padStart(2, '0');
        const s = Math.floor((elapsed % 60000) / 1000).toString().padStart(2, '0');
        document.getElementById('timer').innerText = `${h}:${m}:${s}`;
    }, 1000);
}

// ── Debate Logic ─────────────────────────────────────────────────────────────
async function initiateDebate() {
    const startBtn = document.querySelector('.btn-start');
    if (startBtn && startBtn.disabled) return;

    const topic = document.getElementById('topicInput').value.trim();
    if (!topic) return;

    // Transition UI
    document.getElementById('wizardOverlay').classList.add('hidden');
    document.getElementById('arena').classList.remove('hidden');
    document.getElementById('displayTitle').innerText = topic;
    
    debateActive = true;
    startTimer();
    clearFeed();

    try {
        const response = await fetch('/api/debate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: topic, dynamics: 'dialectical' })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const event = JSON.parse(line.slice(6));
                    handleDebateEvent(event);
                }
            }
        }
    } catch (error) {
        console.error('Debate error:', error);
    } finally {
        clearInterval(timerInterval);
        document.getElementById('debateStatus').innerText = "Ended";
        document.getElementById('newDebateContainer').classList.remove('hidden');
    }
}

let activeBubbleText = null;

function escapeHtml(unsafe) {
    return (unsafe || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function handleDebateEvent(event) {
    if (event.phase === 'status') {
        const feed = document.getElementById('argumentFeed');
        const statusDiv = document.createElement('div');
        statusDiv.style.textAlign = 'center';
        statusDiv.style.color = 'var(--text-muted)';
        statusDiv.style.margin = '10px 0';
        statusDiv.style.fontSize = '0.9rem';
        statusDiv.innerText = event.content;
        feed.appendChild(statusDiv);
        statusDiv.scrollIntoView({ behavior: 'smooth' });
        return;
    }

    if (event.phase === 'token') {
        if (activeBubbleText) {
            activeBubbleText.innerHTML += escapeHtml(event.content).replace(/\n/g, '<br>');
            const isNearBottom = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 200;
            if (isNearBottom) {
                window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' });
            }
        }
        return;
    }

    if (event.content === "") {
        const bubble = addArgumentBubble(event);
        activeBubbleText = bubble.querySelector('.bubble-text');
        activeBubbleText.innerHTML = "";
    } else if (event.content) {
        if (!activeBubbleText) {
             const bubble = addArgumentBubble(event);
             activeBubbleText = bubble.querySelector('.bubble-text');
        }
        activeBubbleText.innerHTML = escapeHtml(event.content).replace(/\n/g, '<br>');
        activeBubbleText = null;
        updateSidebarPersona(event);
    }

    if (event.metrics) {
        if (event.metrics.progress !== undefined) {
            updateProgressBar(event.metrics.progress);
        }
        if (event.metrics.strength) {
            updateStrengthMetrics(event.metrics.strength);
        }
    }
}

function addArgumentBubble(event) {
    const feed = document.getElementById('argumentFeed');
    const bubble = document.createElement('div');
    
    let typeClass = 'bubble-synthesis';
    let prefix = 'SYNTHESIS';
    
    if (event.phase === 'search') prefix = 'NETWORK SEARCH';
    else if (event.phase === 'answer') prefix = 'PROVOCATEUR';
    else if (event.phase === 'critique') prefix = 'ADVERSARY';
    else if (event.phase === 'factcheck') prefix = 'FINAL VERDICT';

    if (event.persona_key === 'critic') {
        typeClass = 'bubble-ethicist';
    } else if (event.persona_key === 'factchecker') {
        typeClass = 'bubble-catalyst';
    } else if (event.persona_key === 'answerer') {
        typeClass = 'bubble-synthesis';
    } else if (event.phase === 'search') {
        typeClass = 'bubble-search';
    }

    bubble.className = `bubble ${typeClass}`;
    
    const content = escapeHtml(event.content || "");
    
    let modelName = 'DeepSeek R1';
    if (event.persona_key === 'answerer') modelName = 'Gemma 4';
    else if (event.persona_key === 'critic') modelName = 'Llama 3.1';
    else if (event.persona_key === 'factchecker') modelName = 'DeepSeek R1';
    else if (event.phase === 'search') modelName = 'System';

    bubble.innerHTML = `
        <div class="bubble-text">${content}</div>
        <div class="bubble-meta">${prefix} ● ${modelName} ● Just now</div>
    `;
    
    feed.appendChild(bubble);
    const isNearBottom = window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 300;
    if (isNearBottom || event.phase === 'initial') {
        bubble.scrollIntoView({ behavior: 'smooth' });
    }
    return bubble;
}

function updateSidebarPersona(event) {
    if (event.persona_key === 'ethicist') {
        const quote = document.getElementById('ethicistQuote');
        quote.innerText = `"${truncate(event.content, 80)}"`;
    } else if (event.persona_key === 'catalyst') {
        const quote = document.getElementById('catalystQuote');
        quote.innerText = `"${truncate(event.content, 80)}"`;
    } else if (event.persona_key === 'synthesizer' || event.persona_key === 'consensus') {
        const quote = document.getElementById('synthesizerQuote');
        if (quote) quote.innerText = `"${truncate(event.content, 80)}"`;
    }
}

function updateProgressBar(progress) {
    if (progress === undefined) return;
    
    const barProgress = document.getElementById('bar-progress');
    if (barProgress) {
        barProgress.style.width = `${progress}%`;
        barProgress.innerText = `${Math.round(progress)}%`;
    }
}

function updateStrengthMetrics(strength) {
    if (!strength) return;

    updateMetric('coherence', strength.coherence);
    updateMetric('accuracy', strength.accuracy);
    updateMetric('resonance', strength.resonance);
}

function updateMetric(id, val) {
    document.getElementById(`met-${id}`).innerText = `${Math.round(val)}%`;
    document.getElementById(`fill-${id}`).style.width = `${val}%`;
}

function clearFeed() {
    document.getElementById('argumentFeed').innerHTML = '';
}

function truncate(str, n) {
    return (str.length > n) ? str.substr(0, n-1) + '...' : str;
}

function resetDebate() {
    document.getElementById('newDebateContainer').classList.add('hidden');
    document.getElementById('arena').classList.add('hidden');
    document.getElementById('wizardOverlay').classList.remove('hidden');
    document.getElementById('topicInput').value = '';
    debateActive = false;
    document.getElementById('debateStatus').innerText = "Standby";
    document.getElementById('timer').innerText = "00:00:00";
    clearInterval(timerInterval);
    updateProgressBar(0);
}

function showToast(msg) {
    console.log("Toast:", msg);
}

function submitRebuttal() {
    const input = document.getElementById('rebuttalInput');
    const text = input.value.trim();
    if (!text) return;

    const feed = document.getElementById('argumentFeed');
    const bubble = document.createElement('div');
    bubble.className = `bubble bubble-synthesis`;
    
    bubble.innerHTML = `
        <div class="bubble-text">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
        <div class="bubble-meta">CONTINUE DEBATE ● User ● Just now</div>
    `;
    
    feed.appendChild(bubble);
    bubble.scrollIntoView({ behavior: 'smooth' });

    input.value = '';
}
