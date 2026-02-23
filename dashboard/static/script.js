const consoleEl = document.getElementById('console');
const statusBadge = document.getElementById('status-badge');
const addressEl = document.getElementById('wallet-address');
const balanceEl = document.getElementById('wallet-balance');
const strategySelect = document.getElementById('strategy');
const vaultGroup = document.getElementById('vault-group');

const btnStatus = document.getElementById('btn-status');
const btnFund = document.getElementById('btn-fund');
const btnRun = document.getElementById('btn-run');
const btnStop = document.getElementById('btn-stop');
const btnClear = document.getElementById('btn-clear');

let eventSource = null;

// Initialize
fetchStatus();
setupEventSource();

// --- Event Listeners ---

strategySelect.addEventListener('change', () => {
    if (strategySelect.value === 'sweep') {
        vaultGroup.classList.remove('hidden');
    } else {
        vaultGroup.classList.add('hidden');
    }
});

btnStatus.addEventListener('click', async () => {
    appendLog('system', 'Checking wallet status...');
    await fetchStatus();
});

btnFund.addEventListener('click', async () => {
    appendLog('system', 'Requesting airdrop...');
    const res = await apiPost('/api/fund');
    if (res.success) setRunning(true);
});

btnRun.addEventListener('click', async () => {
    const data = {
        strategy: strategySelect.value,
        rounds: document.getElementById('rounds').value,
        interval: document.getElementById('interval').value,
        vault: document.getElementById('vault').value
    };

    appendLog('system', `Starting agent with strategy: ${data.strategy}...`);
    const res = await apiPost('/api/run', data);
    if (res.success) setRunning(true);
});

btnStop.addEventListener('click', async () => {
    appendLog('system', 'Stopping agent...');
    await apiPost('/api/stop');
    setRunning(false);
});

btnClear.addEventListener('click', () => {
    consoleEl.innerHTML = '<div class="log-line system">Logs cleared. Ready.</div>';
});

// --- Functions ---

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.success) {
            // Parse common fields from the output
            const output = data.output;
            const address = output.match(/Identity: ([A-Za-z0-9]+)/)?.[1] || 'Unknown';
            const balance = output.match(/Balance: ([0-9.]+) SOL/)?.[1] || '0.0000';

            addressEl.textContent = address;
            balanceEl.textContent = `${balance} SOL`;
            appendLog('system', 'Status refreshed.');
        } else {
            appendLog('error', `Status check failed: ${data.error}`);
        }
    } catch (err) {
        appendLog('error', `Connection error: ${err.message}`);
    }
}

async function apiPost(url, data = {}) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await res.json();
    } catch (err) {
        appendLog('error', `Request failed: ${err.message}`);
        return { success: false, error: err.message };
    }
}

function setupEventSource() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource('/api/logs');

    eventSource.onmessage = (event) => {
        if (event.data === ': keep-alive') return;

        const line = event.data;
        if (line.includes('[XX]') || line.includes('FAILED')) {
            appendLog('error', line);
        } else if (line.includes('[OK]') || line.includes('[~~]') || line.includes('SUCCESS')) {
            appendLog('success', line);
            // Auto refresh balance after success signals
            if (line.includes('Hydrated') || line.includes('altred') || line.includes('Balance')) fetchStatus();
        } else {
            appendLog('info', line);
        }

        if (line.includes('Process finished')) {
            setRunning(false);
        }
    };

    eventSource.onerror = () => {
        console.error('SSE connection lost. Reconnecting...');
    };
}

function appendLog(type, message) {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.textContent = message;
    consoleEl.appendChild(line);
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

function setRunning(running) {
    if (running) {
        statusBadge.textContent = 'Active';
        statusBadge.classList.add('active');
        btnRun.classList.add('hidden');
        btnStop.classList.remove('hidden');
    } else {
        statusBadge.textContent = 'Idle';
        statusBadge.classList.remove('active');
        btnRun.classList.remove('hidden');
        btnStop.classList.add('hidden');
    }
}
