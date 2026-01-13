// Trading Bot Web Dashboard JavaScript

const API_BASE = '/api';
let statusCheckInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    startStatusPolling();
});

// Initialize app
function initializeApp() {
    // Setup event listeners
    document.getElementById('connectBtn').addEventListener('click', connectToZerodha);
    document.getElementById('startBtn').addEventListener('click', startBot);
    document.getElementById('stopBtn').addEventListener('click', stopBot);
    document.getElementById('executeTradeBtn').addEventListener('click', executeTrade);
    document.getElementById('analyzeBtn').addEventListener('click', analyzeMarket);
    document.getElementById('refreshPositionsBtn').addEventListener('click', refreshPositions);
    document.getElementById('refreshMarginsBtn').addEventListener('click', refreshMargins);
    document.getElementById('refreshLogsBtn').addEventListener('click', refreshLogs);
    document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);
    document.querySelector('.close-modal').addEventListener('click', closeSettingsModal);
    document.getElementById('settingsForm').addEventListener('submit', saveSettings);

    // Close modal when clicking outside
    window.onclick = (event) => {
        const modal = document.getElementById('settingsModal');
        if (event.target == modal) {
            closeSettingsModal();
        }
    };

    // Load initial data
    updateStatus();
    refreshLogs();
}

// Status polling
function startStatusPolling() {
    statusCheckInterval = setInterval(updateStatus, 3000); // Update every 3 seconds
}

function stopStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

// API Calls
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('API call failed:', error);
        showToast('Error: ' + error.message, 'error');
        return { success: false, message: error.message };
    }
}

// Update status
async function updateStatus() {
    try {
        const status = await apiCall('/status');
        if (status.success !== false) {
            updateStatusUI(status);
        }
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

// Update status UI
function updateStatusUI(status) {
    // Update status indicator
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    if (status.is_running) {
        statusDot.className = 'status-dot running';
        statusText.textContent = 'Bot Running';
    } else if (status.is_connected) {
        statusDot.className = 'status-dot connected';
        statusText.textContent = 'Connected';
    } else {
        statusDot.className = 'status-dot';
        statusText.textContent = 'Disconnected';
    }

    // Update status cards
    document.getElementById('botStatusText').textContent =
        status.is_running ? 'Running' : 'Stopped';

    document.getElementById('connectionStatusText').textContent =
        status.is_connected ? 'Connected' : 'Disconnected';

    if (status.last_trade) {
        const tradeTime = new Date(status.last_trade.time).toLocaleString();
        document.getElementById('lastTradeText').textContent =
            `Order ID: ${status.last_trade.order_id} at ${tradeTime}`;
    } else {
        document.getElementById('lastTradeText').textContent = 'No trades yet';
    }

    if (status.last_analysis) {
        const analysisTime = new Date(status.last_analysis.time).toLocaleString();
        document.getElementById('lastAnalysisText').textContent =
            `${status.last_analysis.symbol} at ${analysisTime}`;
    } else {
        document.getElementById('lastAnalysisText').textContent = 'No analysis yet';
    }
}

// Connect to Zerodha
async function connectToZerodha() {
    showLoading(true);
    try {
        const result = await apiCall('/connect', 'POST');
        if (result.success) {
            showToast('Connected to Zerodha successfully!', 'success');
            updateStatus();
        } else {
            showToast(result.message || 'Connection failed', 'error');
        }
    } catch (error) {
        showToast('Connection error: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Start bot
async function startBot() {
    if (!confirm('Start the automated trading bot? It will run daily at the configured time.')) {
        return;
    }

    showLoading(true);
    try {
        const result = await apiCall('/start', 'POST');
        if (result.success) {
            showToast('Trading bot started successfully!', 'success');
            updateStatus();
        } else {
            showToast(result.message || 'Failed to start bot', 'error');
        }
    } catch (error) {
        showToast('Error starting bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Stop bot
async function stopBot() {
    if (!confirm('Stop the trading bot?')) {
        return;
    }

    showLoading(true);
    try {
        const result = await apiCall('/stop', 'POST');
        if (result.success) {
            showToast('Trading bot stopped', 'info');
            updateStatus();
        } else {
            showToast(result.message || 'Failed to stop bot', 'error');
        }
    } catch (error) {
        showToast('Error stopping bot: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Execute trade
async function executeTrade() {
    if (!confirm('Execute a trade now? This will analyze the market and place an order if suitable.')) {
        return;
    }

    showLoading(true);
    try {
        const result = await apiCall('/trade/execute', 'POST', { use_analysis: true });
        if (result.success) {
            showToast(`Trade executed! Order ID: ${result.order_id}`, 'success');
            updateStatus();
        } else {
            showToast(result.message || 'Trade execution failed', 'error');
        }
    } catch (error) {
        showToast('Error executing trade: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Analyze market
async function analyzeMarket() {
    const symbol = document.getElementById('symbolInput').value.trim();
    if (!symbol) {
        showToast('Please enter a symbol', 'error');
        return;
    }

    showLoading(true);
    try {
        const result = await apiCall('/analyze', 'POST', { symbol: symbol });
        if (result.success) {
            displayAnalysisResult(result.analysis);
            showToast('Analysis completed!', 'success');
        } else {
            showToast(result.message || 'Analysis failed', 'error');
        }
    } catch (error) {
        showToast('Error analyzing market: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Display analysis result
function displayAnalysisResult(analysis) {
    const resultDiv = document.getElementById('analysisResult');
    resultDiv.className = 'analysis-result show';

    const recommendation = analysis.recommendation || 'N/A';
    const recommendationClass = recommendation.includes('BUY') ? 'buy' :
        recommendation.includes('SELL') ? 'sell' : 'hold';

    let html = `
        <div class="analysis-item">
            <span class="analysis-label">Symbol:</span>
            <span class="analysis-value">${analysis.symbol || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">Current Price:</span>
            <span class="analysis-value">₹${analysis.current_price || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">RSI:</span>
            <span class="analysis-value">${analysis.rsi || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">MACD:</span>
            <span class="analysis-value">${analysis.macd || 'N/A'}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">Score:</span>
            <span class="analysis-value">${analysis.score || 0}/100</span>
        </div>
    `;

    if (analysis.signals && analysis.signals.length > 0) {
        html += '<div style="margin-top: 16px;"><strong>Signals:</strong><ul style="margin-top: 8px; padding-left: 20px;">';
        analysis.signals.forEach(signal => {
            html += `<li style="margin-bottom: 4px; color: var(--text-secondary);">${signal}</li>`;
        });
        html += '</ul></div>';
    }

    html += `
        <div class="recommendation ${recommendationClass}">
            Recommendation: ${recommendation}
        </div>
    `;

    resultDiv.innerHTML = html;
}

// Refresh positions
async function refreshPositions() {
    showLoading(true);
    try {
        const result = await apiCall('/positions');
        const positionsList = document.getElementById('positionsList');

        if (result.success && result.positions && result.positions.length > 0) {
            let html = '';
            result.positions.forEach(pos => {
                html += `
                    <div class="data-item">
                        <div class="data-item-header">
                            <span class="data-item-label">${pos.tradingsymbol || 'N/A'}</span>
                            <span class="data-item-value">Qty: ${pos.quantity || 0}</span>
                        </div>
                        <div style="color: var(--text-secondary); font-size: 14px;">
                            Avg Price: ₹${pos.average_price || 0} | 
                            LTP: ₹${pos.last_price || 0}
                        </div>
                    </div>
                `;
            });
            positionsList.innerHTML = html;
        } else {
            positionsList.innerHTML = '<p class="empty-state">No open positions</p>';
        }
    } catch (error) {
        showToast('Error loading positions: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Refresh margins
async function refreshMargins() {
    showLoading(true);
    try {
        const result = await apiCall('/margins');
        const marginsInfo = document.getElementById('marginsInfo');

        if (result.success && result.margins) {
            const equity = result.margins.equity || {};
            const available = equity.available || {};
            const utilised = equity.utilised || {};

            marginsInfo.innerHTML = `
                <div class="data-item">
                    <div class="data-item-header">
                        <span class="data-item-label">Available Cash</span>
                        <span class="data-item-value">₹${available.cash || 0}</span>
                    </div>
                </div>
                <div class="data-item">
                    <div class="data-item-header">
                        <span class="data-item-label">Utilised</span>
                        <span class="data-item-value">₹${utilised.debits || 0}</span>
                    </div>
                </div>
            `;
        } else {
            marginsInfo.innerHTML = '<p class="empty-state">Could not load margins</p>';
        }
    } catch (error) {
        showToast('Error loading margins: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Refresh logs
async function refreshLogs() {
    try {
        const result = await apiCall('/logs');
        const logsContent = document.getElementById('logsContent');

        if (result.success && result.logs) {
            const lines = result.logs.split('\n');
            let html = '';
            lines.forEach(line => {
                if (line.trim()) {
                    let className = 'log-line';
                    if (line.toLowerCase().includes('error')) {
                        className += ' error';
                    } else if (line.toLowerCase().includes('success') || line.toLowerCase().includes('✅')) {
                        className += ' success';
                    } else if (line.toLowerCase().includes('info')) {
                        className += ' info';
                    }
                    html += `<div class="${className}">${escapeHtml(line)}</div>`;
                }
            });
            logsContent.innerHTML = html || '<p class="empty-state">No logs available</p>';
            logsContent.scrollTop = logsContent.scrollHeight;
        } else {
            logsContent.innerHTML = '<p class="empty-state">Could not load logs</p>';
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

// Utility functions
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 5000);
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

// Settings Modal Logic
async function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'block';

    // Load current config
    showLoading(true);
    try {
        const result = await apiCall('/config');
        if (result.success && result.config) {
            // Note: The /api/config doesn't return passwords/secrets for security
            // But we can fill in what we have if needed. 
            // For now, we'll let user enter them.
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    } finally {
        showLoading(false);
    }
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

async function saveSettings(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        apiKey: formData.get('apiKey'),
        apiSecret: formData.get('apiSecret'),
        userId: formData.get('userId'),
        password: formData.get('password'),
        totpSecret: formData.get('totpSecret')
    };

    showLoading(true);
    try {
        const result = await apiCall('/config/update', 'POST', data);
        if (result.success) {
            showToast('Settings saved successfully!', 'success');
            closeSettingsModal();
            // Automatically try to connect
            await connectToZerodha();
        } else {
            showToast(result.message || 'Failed to save settings', 'error');
        }
    } catch (error) {
        showToast('Error saving settings: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
