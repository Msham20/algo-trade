/**
 * NIFTY Charts JavaScript
 * Handles chart rendering and real-time data updates
 */

// Global state
let chart = null;
let candleSeries = null;
let ema9Line = null;
let ema21Line = null;
let supertrendLine = null;
let vwapLine = null;
let currentDays = 2;
let refreshInterval = null;
let countdownInterval = null;
let countdown = 10;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadData();
    startAutoRefresh();
    setupEventListeners();
    setupAutoTradingControls();
    loadAutoTradingStatus();
    checkZerodhaConnection();
});

/**
 * Initialize TradingView Lightweight Chart
 */
function initChart() {
    const container = document.getElementById('chartContainer');

    chart = LightweightCharts.createChart(container, {
        layout: {
            background: { type: 'solid', color: '#0d1117' },
            textColor: '#94a3b8',
        },
        grid: {
            vertLines: { color: 'rgba(99, 102, 241, 0.1)' },
            horzLines: { color: 'rgba(99, 102, 241, 0.1)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: 'rgba(99, 102, 241, 0.2)',
        },
        timeScale: {
            borderColor: 'rgba(99, 102, 241, 0.2)',
            timeVisible: true,
            secondsVisible: false,
        },
    });

    // Candlestick series
    candleSeries = chart.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderDownColor: '#ef4444',
        borderUpColor: '#22c55e',
        wickDownColor: '#ef4444',
        wickUpColor: '#22c55e',
    });

    // EMA 9 line
    ema9Line = chart.addLineSeries({
        color: '#3b82f6',
        lineWidth: 1,
        title: 'EMA 9',
    });

    // EMA 21 line
    ema21Line = chart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 1,
        title: 'EMA 21',
    });

    // SuperTrend line
    supertrendLine = chart.addLineSeries({
        color: '#8b5cf6',
        lineWidth: 2,
        title: 'SuperTrend',
    });

    // VWAP line
    vwapLine = chart.addLineSeries({
        color: '#22c55e',
        lineWidth: 1,
        lineStyle: 2, // Dashed
        title: 'VWAP',
    });

    // Responsive chart
    const resizeObserver = new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) return;
        const { width, height } = entries[0].contentRect;
        chart.applyOptions({ width, height });
    });
    resizeObserver.observe(container);
}

/**
 * Load all data
 */
async function loadData() {
    try {
        await Promise.all([
            loadChartData(),
            loadSignals()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
        showToast('Error loading data', 'error');
    }
}

/**
 * Load chart data from API
 */
async function loadChartData() {
    try {
        const response = await fetch(`/api/nifty/chart-data?days=${currentDays}`);
        const data = await response.json();

        if (data.error) {
            console.error('Chart data error:', data.error);
            return;
        }

        // Update candlestick data
        if (data.candles && data.candles.length > 0) {
            candleSeries.setData(data.candles);
        }

        // Update indicator lines
        if (data.indicators) {
            if (data.indicators.ema9) ema9Line.setData(data.indicators.ema9);
            if (data.indicators.ema21) ema21Line.setData(data.indicators.ema21);
            if (data.indicators.supertrend) supertrendLine.setData(data.indicators.supertrend);
            if (data.indicators.vwap) vwapLine.setData(data.indicators.vwap);
        }

        // Fit content
        chart.timeScale().fitContent();

    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

/**
 * Load signals and indicators from API
 */
async function loadSignals() {
    try {
        const response = await fetch('/api/nifty/signals');
        const data = await response.json();

        if (data.error) {
            console.error('Signals error:', data.error);
            return;
        }

        updatePriceCard(data);
        updateSignalCard(data);
        updateRiskManagement(data);
        updateSignalsList(data.signals);
        updateIndicators(data.indicators);
        updateSupportResistance(data.support_resistance);
        updateCPR(data.cpr);
        updateFibonacci(data.fibonacci);
        updatePatterns(data.patterns);
        updateLastUpdated(data.timestamp);

        // Draw levels on chart if it's the 1D view
        if (currentDays === 1) {
            drawChartLevels(data);
        }

    } catch (error) {
        console.error('Error loading signals:', error);
    }
}

/**
 * Update price card
 */
function updatePriceCard(data) {
    document.getElementById('niftyPrice').textContent = `₹${data.price.toLocaleString()}`;
}

/**
 * Update signal card
 */
function updateSignalCard(data) {
    const signalCard = document.getElementById('signalCard');
    const signalValue = document.getElementById('signalValue');
    const signalStrength = document.getElementById('signalStrength');

    // Remove existing classes
    signalCard.classList.remove('buy', 'sell', 'hold');
    signalValue.classList.remove('buy', 'sell', 'hold');

    // Add appropriate class
    let signalClass = 'hold';
    if (data.signal.includes('BUY')) signalClass = 'buy';
    else if (data.signal.includes('SELL')) signalClass = 'sell';

    signalCard.classList.add(signalClass);
    signalValue.classList.add(signalClass);
    signalValue.textContent = data.signal.replace('_', ' ');
    signalStrength.textContent = `Strength: ${data.strength}%`;
}

/**
 * Update stop loss and target
 */
function updateRiskManagement(data) {
    document.getElementById('stopLoss').textContent = `₹${data.stop_loss.toLocaleString()}`;
    document.getElementById('target').textContent = `₹${data.target.toLocaleString()}`;
    document.getElementById('riskReward').textContent = `R:R 1:${data.risk_reward_ratio}`;
}

/**
 * Update signals list
 */
function updateSignalsList(signals) {
    const container = document.getElementById('signalsList');

    if (!signals || signals.length === 0) {
        container.innerHTML = '<div class="no-patterns">No active signals</div>';
        return;
    }

    container.innerHTML = signals.map(signal => {
        let type = 'neutral';
        if (signal.includes('🟢')) type = 'bullish';
        else if (signal.includes('🔴')) type = 'bearish';

        return `<div class="signal-item ${type}">${signal}</div>`;
    }).join('');
}

/**
 * Update indicators panel
 */
function updateIndicators(indicators) {
    if (!indicators) return;

    // RSI
    document.getElementById('rsiValue').textContent = indicators.rsi.toFixed(1);
    const rsiFill = document.getElementById('rsiFill');
    rsiFill.style.width = `${indicators.rsi}%`;

    // MACD
    document.getElementById('macdValue').textContent = indicators.macd.toFixed(2);
    const macdStatus = document.getElementById('macdStatus');
    if (indicators.macd > indicators.macd_signal) {
        macdStatus.textContent = 'Bullish';
        macdStatus.className = 'indicator-status bullish';
    } else {
        macdStatus.textContent = 'Bearish';
        macdStatus.className = 'indicator-status bearish';
    }

    // SuperTrend
    document.getElementById('supertrendValue').textContent = indicators.supertrend.toFixed(2);
    const stStatus = document.getElementById('supertrendStatus');
    stStatus.textContent = indicators.supertrend_direction;
    stStatus.className = `indicator-status ${indicators.supertrend_direction === 'BULLISH' ? 'bullish' : 'bearish'}`;

    // VWAP
    document.getElementById('vwapValue').textContent = indicators.vwap.toFixed(2);
    const vwapStatus = document.getElementById('vwapStatus');
    // Compare with current price from the price card
    const priceText = document.getElementById('niftyPrice').textContent;
    const price = parseFloat(priceText.replace('₹', '').replace(',', ''));
    if (!isNaN(price)) {
        if (price > indicators.vwap) {
            vwapStatus.textContent = 'Above';
            vwapStatus.className = 'indicator-status bullish';
        } else {
            vwapStatus.textContent = 'Below';
            vwapStatus.className = 'indicator-status bearish';
        }
    }

    // EMA
    document.getElementById('emaValue').textContent = `${indicators.ema9.toFixed(0)} / ${indicators.ema21.toFixed(0)}`;
    const emaStatus = document.getElementById('emaStatus');
    if (indicators.ema9 > indicators.ema21) {
        emaStatus.textContent = 'Bullish';
        emaStatus.className = 'indicator-status bullish';
    } else {
        emaStatus.textContent = 'Bearish';
        emaStatus.className = 'indicator-status bearish';
    }

    // ATR
    document.getElementById('atrValue').textContent = indicators.atr.toFixed(2);
}

/**
 * Update support/resistance levels
 */
function updateSupportResistance(sr) {
    if (!sr) return;

    const resistanceList = document.getElementById('resistanceLevels');
    const supportList = document.getElementById('supportLevels');

    if (sr.resistance && sr.resistance.length > 0) {
        resistanceList.innerHTML = sr.resistance.map(r =>
            `<li>₹${r.toLocaleString()}</li>`
        ).join('');
    } else {
        resistanceList.innerHTML = '<li>--</li>';
    }

    if (sr.support && sr.support.length > 0) {
        supportList.innerHTML = sr.support.map(s =>
            `<li>₹${s.toLocaleString()}</li>`
        ).join('');
    } else {
        supportList.innerHTML = '<li>--</li>';
    }
}

/**
 * Update candlestick patterns
 */
function updatePatterns(patterns) {
    const container = document.getElementById('patternsList');

    if (!patterns || Object.keys(patterns).length === 0) {
        container.innerHTML = '<div class="no-patterns">No patterns detected</div>';
        return;
    }

    const bullishPatterns = ['hammer', 'bullish_engulfing', 'morning_star'];

    container.innerHTML = Object.entries(patterns).map(([pattern, detected]) => {
        if (!detected) return '';
        const type = bullishPatterns.includes(pattern) ? 'bullish' : 'bearish';
        const icon = type === 'bullish' ? '🟢' : '🔴';
        const name = pattern.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<span class="pattern-tag ${type}">${icon} ${name}</span>`;
    }).join('');
}

/**
 * Update CPR section
 */
function updateCPR(cpr) {
    if (!cpr) return;

    document.getElementById('cprTC').textContent = `₹${cpr.tc}`;
    document.getElementById('cprPivot').textContent = `₹${cpr.pivot}`;
    document.getElementById('cprBC').textContent = `₹${cpr.bc}`;

    const typeBadge = document.getElementById('cprType');
    typeBadge.textContent = `Type: ${cpr.type}`;
    typeBadge.className = `cpr-badge ${cpr.type.toLowerCase()}`;

    document.getElementById('cprWidth').textContent = `Width: ${cpr.width_perc}%`;

    document.getElementById('pivotR1').textContent = cpr.r1;
    document.getElementById('pivotR2').textContent = cpr.r2;
    document.getElementById('pivotR3').textContent = cpr.r3;
    document.getElementById('pivotS1').textContent = cpr.s1;
    document.getElementById('pivotS2').textContent = cpr.s2;
    document.getElementById('pivotS3').textContent = cpr.s3;
}

/**
 * Update Fibonacci section
 */
function updateFibonacci(fib) {
    if (!fib) return;

    document.getElementById('fibHigh').textContent = `₹${fib.high}`;
    document.getElementById('fib236').textContent = `₹${fib.fib_236}`;
    document.getElementById('fib382').textContent = `₹${fib.fib_382}`;
    document.getElementById('fib500').textContent = `₹${fib.fib_500}`;
    document.getElementById('fib618').textContent = `₹${fib.fib_618}`;
    document.getElementById('fib786').textContent = `₹${fib.fib_786}`;
    document.getElementById('fibLow').textContent = `₹${fib.low}`;
}

/**
 * Draw CPR and Fib levels on chart as price lines
 */
let chartPriceLines = [];

function drawChartLevels(data) {
    // Clear old lines
    chartPriceLines.forEach(line => candleSeries.removePriceLine(line));
    chartPriceLines = [];

    if (data.cpr) {
        const cpr = data.cpr;
        // Draw Pivot, TC, BC
        const levels = [
            { price: cpr.pivot, color: '#6366f1', title: 'Pivot', width: 2 },
            { price: cpr.tc, color: '#4f46e5', title: 'TC', width: 1 },
            { price: cpr.bc, color: '#4f46e5', title: 'BC', width: 1 },
            { price: cpr.r1, color: '#ef4444', title: 'R1', width: 1 },
            { price: cpr.s1, color: '#22c55e', title: 'S1', width: 1 }
        ];

        levels.forEach(l => {
            const priceLine = candleSeries.createPriceLine({
                price: l.price,
                color: l.color,
                lineWidth: l.width,
                lineStyle: 2, // Dashed
                axisLabelVisible: true,
                title: l.title,
            });
            chartPriceLines.push(priceLine);
        });
    }
}

/**
 * Update last updated time
 */
function updateLastUpdated(timestamp) {
    const date = new Date(timestamp);
    document.getElementById('lastUpdated').textContent = date.toLocaleTimeString();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Chart time range buttons
    document.querySelectorAll('.chart-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentDays = parseInt(e.target.dataset.days);
            await loadChartData();
        });
    });

    // Refresh button
    document.getElementById('refreshChart').addEventListener('click', async () => {
        const btn = document.getElementById('refreshChart');
        btn.classList.add('spinning');
        await loadData();
        btn.classList.remove('spinning');
        resetCountdown();
    });

    // Connect Zerodha button - Open Modal
    document.getElementById('connectZerodhaBtn').addEventListener('click', () => {
        document.getElementById('zerodhaModal').style.display = 'block';
    });

    // Close Modal
    document.querySelector('.close-modal').addEventListener('click', () => {
        document.getElementById('zerodhaModal').style.display = 'none';
    });

    // Close Modal on click outside
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('zerodhaModal');
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    // Handle Zerodha Form Submission
    document.getElementById('zerodhaForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const btn = e.target.querySelector('button');
        const originalText = btn.innerHTML;

        const formData = {
            apiKey: document.getElementById('apiKey').value,
            apiSecret: document.getElementById('apiSecret').value,
            userId: document.getElementById('userId').value,
            password: document.getElementById('password').value,
            totpSecret: document.getElementById('totpSecret').value
        };

        try {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving & Connecting...';

            // 1. Update config
            const configResponse = await fetch('/api/config/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const configData = await configResponse.json();

            if (!configData.success) {
                throw new Error(configData.message || 'Failed to update configuration');
            }

            // 2. Connect
            const connectResponse = await fetch('/api/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const connectData = await connectResponse.json();

            if (connectData.success) {
                showToast('✅ Credentials saved & Connected!', 'success');
                document.getElementById('zerodhaModal').style.display = 'none';
                checkZerodhaConnection();
            } else {
                showToast(connectData.message || 'Failed to connect', 'error');
            }
        } catch (error) {
            showToast(error.message || 'Error occurred', 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });
}

/**
 * Check Zerodha connection status
 */
async function checkZerodhaConnection() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const badge = document.getElementById('connectionBadge');
        if (data.is_connected) {
            badge.className = 'connection-badge connected';
            badge.innerHTML = '<i class="fas fa-circle"></i> ZERODHA: ON';
            document.getElementById('connectZerodhaBtn').classList.add('hidden');
        } else {
            badge.className = 'connection-badge disconnected';
            badge.innerHTML = '<i class="fas fa-circle"></i> ZERODHA: OFF';
            document.getElementById('connectZerodhaBtn').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error checking connection status:', error);
    }
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    // Refresh data every 10 seconds
    refreshInterval = setInterval(async () => {
        await loadData();
        resetCountdown();
    }, 10000);

    // Countdown display
    countdownInterval = setInterval(() => {
        countdown--;
        if (countdown < 0) countdown = 10;
        document.getElementById('countdown').textContent = countdown;
    }, 1000);
}

/**
 * Reset countdown
 */
function resetCountdown() {
    countdown = 10;
    document.getElementById('countdown').textContent = countdown;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Add spinning animation for refresh button
const style = document.createElement('style');
style.textContent = `
    .spinning i {
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// ==================== AUTO TRADING FUNCTIONS ====================

/**
 * Setup auto trading button controls
 */
function setupAutoTradingControls() {
    // Start Auto Trading
    document.getElementById('startAutoBtn').addEventListener('click', async () => {
        try {
            const settings = {
                min_strength: document.getElementById('minStrengthInput').value,
                quantity: document.getElementById('quantityInput').value,
                max_trades: document.getElementById('maxTradesInput').value
            };

            const response = await fetch('/api/auto/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            const data = await response.json();

            if (data.success) {
                showToast('🤖 Auto trading started!', 'success');
                updateAutoTradingUI(true);
                loadAutoTradingStatus();
            } else {
                showToast(data.message || 'Failed to start', 'error');
            }
        } catch (error) {
            showToast('Error starting auto trading', 'error');
        }
    });

    // Stop Auto Trading
    document.getElementById('stopAutoBtn').addEventListener('click', async () => {
        try {
            const response = await fetch('/api/auto/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (data.success) {
                showToast('⏹️ Auto trading stopped', 'info');
                updateAutoTradingUI(false);
                loadAutoTradingStatus();
            } else {
                showToast(data.message || 'Failed to stop', 'error');
            }
        } catch (error) {
            showToast('Error stopping auto trading', 'error');
        }
    });

    // Trade Now button
    document.getElementById('tradeNowBtn').addEventListener('click', async () => {
        try {
            const btn = document.getElementById('tradeNowBtn');
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Trading...';

            const response = await fetch('/api/auto/trade-now', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-bolt"></i> Trade Now';

            if (data.success) {
                showToast(`✅ ${data.message}`, 'success');
                loadAutoTradingStatus();
            } else {
                showToast(`⚠️ ${data.message}`, 'warning');
            }
        } catch (error) {
            document.getElementById('tradeNowBtn').innerHTML = '<i class="fas fa-bolt"></i> Trade Now';
            document.getElementById('tradeNowBtn').disabled = false;
            showToast('Error executing trade', 'error');
        }
    });
}

/**
 * Load auto trading status
 */
async function loadAutoTradingStatus() {
    try {
        const response = await fetch('/api/auto/status');
        const data = await response.json();

        if (data.success) {
            const status = data.status;

            // Update running status
            updateAutoTradingUI(status.is_running);

            // Update stats
            document.getElementById('tradesToday').textContent = status.trades_today || 0;
            document.getElementById('openTrades').textContent = status.open_trades?.length || 0;

            // Update paper trading stats
            if (status.paper_stats) {
                const stats = status.paper_stats;

                // Set profit and loss
                const profitEl = document.getElementById('totalProfit');
                const lossEl = document.getElementById('totalLoss');
                const pnlEl = document.getElementById('totalPnl');

                if (profitEl) profitEl.textContent = `₹${stats.total_profit.toLocaleString()}`;
                if (lossEl) lossEl.textContent = `₹${stats.total_loss.toLocaleString()}`;

                if (pnlEl) {
                    pnlEl.textContent = `₹${stats.total_pnl.toLocaleString()}`;
                    pnlEl.classList.remove('profit', 'loss');
                    if (stats.total_pnl > 0) pnlEl.classList.add('profit');
                    else if (stats.total_pnl < 0) pnlEl.classList.add('loss');
                }
            }

            // Update logs
            if (data.auto_logs) {
                updateAutoLogs(data.auto_logs);
            }
        }
    } catch (error) {
        console.error('Error loading auto trading status:', error);
    }
}

/**
 * Update auto logs list
 */
function updateAutoLogs(logs) {
    const container = document.getElementById('autoLogsList');
    if (!logs || logs.length === 0) {
        container.innerHTML = '<div class="log-placeholder">No activity logged yet...</div>';
        return;
    }

    container.innerHTML = logs.map(log => `
        <div class="log-entry log-${log.type}">
            <span class="log-time">[${log.time}]</span>
            <span class="log-msg">${log.message}</span>
        </div>
    `).reverse().join('');
}

/**
 * Update auto trading UI based on running state
 */
function updateAutoTradingUI(isRunning) {
    const statusDot = document.querySelector('.auto-indicator .status-dot');
    const statusText = document.getElementById('autoStatusText');

    if (isRunning) {
        statusDot.classList.remove('off');
        statusDot.classList.add('on');
        statusText.textContent = 'RUNNING';
        statusText.style.color = '#22c55e';
    } else {
        statusDot.classList.remove('on');
        statusDot.classList.add('off');
        statusText.textContent = 'OFF';
        statusText.style.color = '#94a3b8';
    }
}

// Load auto trading status every 30 seconds
setInterval(loadAutoTradingStatus, 30000);
