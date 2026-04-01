let allQuotes = { US: [], TW: [] };
let currentTab = 'US';
let currentSymbol = null;
let currentPeriod = '1m';
let chart = null;
let candleSeries = null;
let volumeSeries = null;

async function init() {
  await Promise.all([loadQuotes(), loadReport(), loadNews()]);
  document.getElementById('last-updated').textContent =
    '更新時間：' + new Date().toLocaleString('zh-TW');
}

// ── 股票報價 ──────────────────────────────────────────
async function loadQuotes() {
  try {
    const res = await fetch('/api/stocks/latest');
    allQuotes = await res.json();
    renderStockList(currentTab);
  } catch (e) {
    document.getElementById('stock-list').textContent = '載入失敗：' + e.message;
  }
}

function switchTab(market) {
  currentTab = market;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  renderStockList(market);
}

function renderStockList(market) {
  const list = document.getElementById('stock-list');
  const stocks = allQuotes[market] || [];

  if (stocks.length === 0) {
    list.innerHTML = '<div style="padding:20px;color:#8b949e;text-align:center">無資料</div>';
    return;
  }

  list.innerHTML = stocks.map(s => {
    const cls = s.change > 0 ? 'up' : s.change < 0 ? 'down' : 'flat';
    const sign = s.change > 0 ? '+' : '';
    const currency = market === 'US' ? '$' : '';
    const selected = s.symbol === currentSymbol ? ' selected' : '';
    return `
      <div class="stock-item${selected}" onclick="selectStock('${s.symbol}', '${s.name}')">
        <div class="stock-info">
          <div class="name">${s.name}</div>
          <div class="symbol">${s.symbol}</div>
        </div>
        <div class="stock-price">
          <div class="price">${currency}${s.price.toLocaleString()}</div>
          <div class="change ${cls}">${sign}${s.change_pct.toFixed(2)}%</div>
        </div>
      </div>`;
  }).join('');
}

function selectStock(symbol, name) {
  currentSymbol = symbol;
  document.querySelectorAll('.stock-item').forEach(el => el.classList.remove('selected'));
  event.currentTarget.classList.add('selected');
  loadChart(symbol, currentPeriod);
}

// ── K線圖 ─────────────────────────────────────────────
async function loadChart(symbol, period) {
  if (!symbol) return;
  currentPeriod = period;

  // 更新期間按鈕
  document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
  event?.target?.classList.add('active');

  try {
    const res = await fetch(`/api/stocks/${encodeURIComponent(symbol)}/history?period=${period}`);
    const data = await res.json();

    document.getElementById('chart-title').textContent =
      `${data.name}（${data.symbol}）`;

    renderChart(data.data, data.market);
  } catch (e) {
    console.error('載入圖表失敗', e);
  }
}

function renderChart(data, market) {
  const container = document.getElementById('chart-container');
  const placeholder = document.getElementById('chart-placeholder');
  const panel = document.querySelector('.chart-panel');
  const header = document.querySelector('.chart-header');

  placeholder.style.display = 'none';
  container.style.display = 'block';

  if (chart) {
    chart.remove();
    chart = null;
  }

  const chartHeight = panel.clientHeight - header.clientHeight;

  chart = LightweightCharts.createChart(container, {
    layout: {
      background: { color: '#161b22' },
      textColor: '#c9d1d9',
    },
    grid: {
      vertLines: { color: '#21262d' },
      horzLines: { color: '#21262d' },
    },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: '#30363d' },
    timeScale: { borderColor: '#30363d', timeVisible: true },
    width: container.clientWidth,
    height: chartHeight > 100 ? chartHeight : 420,
  });

  candleSeries = chart.addCandlestickSeries({
    upColor: '#3fb950',
    downColor: '#f85149',
    borderUpColor: '#3fb950',
    borderDownColor: '#f85149',
    wickUpColor: '#3fb950',
    wickDownColor: '#f85149',
  });

  const candleData = data.map(d => ({
    time: d.date,
    open: d.open,
    high: d.high,
    low: d.low,
    close: d.close,
  }));

  candleSeries.setData(candleData);
  chart.timeScale().fitContent();

  // resize 監聽
  const ro = new ResizeObserver(() => {
    if (chart) chart.applyOptions({ width: container.clientWidth });
  });
  ro.observe(container);
}

// ── 分析報告 ──────────────────────────────────────────
async function loadReport() {
  const el = document.getElementById('report-content');
  el.textContent = '生成中，請稍候...';
  try {
    const res = await fetch('/api/analysis/today');
    const data = await res.json();
    el.textContent = data.content;
  } catch (e) {
    el.textContent = '載入報告失敗：' + e.message;
  }
}

async function refreshReport() {
  const btn = document.getElementById('refresh-report-btn');
  btn.disabled = true;
  btn.textContent = '生成中...';
  const el = document.getElementById('report-content');
  el.textContent = '重新生成中，請稍候...';
  try {
    const res = await fetch('/api/analysis/refresh', { method: 'POST' });
    const data = await res.json();
    el.textContent = data.content;
  } catch (e) {
    el.textContent = '生成失敗：' + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 重新生成';
  }
}

// ── 新聞 ──────────────────────────────────────────────
async function loadNews() {
  const el = document.getElementById('news-list');
  try {
    const res = await fetch('/api/news/latest?limit=20');
    const news = await res.json();
    if (!news.length) {
      el.innerHTML = '<div style="padding:16px;color:#8b949e">暫無新聞</div>';
      return;
    }
    el.innerHTML = news.map(n => `
      <div class="news-item">
        <a href="${n.link}" target="_blank" rel="noopener">${n.title}</a>
        <div class="news-meta">${n.source || ''} ${n.published ? '· ' + n.published.slice(0, 16) : ''}</div>
      </div>`).join('');
  } catch (e) {
    el.textContent = '載入新聞失敗：' + e.message;
  }
}

// ── 啟動 ──────────────────────────────────────────────
init();
