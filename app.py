"""Flask web application for ek-scraper with web interface."""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib
from datetime import datetime

from flask import Flask, jsonify, render_template_string
from werkzeug.exceptions import HTTPException

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ek_scraper.cli import configure_logging, run as run_scraper
from ek_scraper.config import Config
from ek_scraper.data_store import DataStore

configure_logging(verbose=False)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

scraper_running = False
last_run_results = None
last_run_time = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ek-scraper Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 { color: #333; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; font-size: 14px; }
        .status { display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-left: auto; }
        .status.idle { background: #e3f2fd; color: #1976d2; }
        .status.running { background: #fff3e0; color: #f57c00; }
        .status.success { background: #e8f5e9; color: #388e3c; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee; }
        .controls { display: flex; gap: 10px; flex-wrap: wrap; }
        button { padding: 10px 20px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; transform: translateY(-2px); }
        .btn-primary:disabled { background: #ccc; cursor: not-allowed; }
        .btn-secondary { background: #f5f5f5; color: #333; }
        .btn-secondary:hover { background: #eeeeee; }
        .results-section { margin-top: 30px; }
        .results-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px; }
        .result-item { background: #f9f9f9; border-left: 4px solid #667eea; padding: 15px; margin-bottom: 10px; border-radius: 4px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .result-item strong { color: #333; }
        .result-item a { color: #667eea; text-decoration: none; }
        .result-item a:hover { text-decoration: underline; }
        .no-results { text-align: center; padding: 40px; color: #999; }
        .error { background: #ffebee; border-left: 4px solid #f44336; color: #c62828; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .success { background: #e8f5e9; border-left: 4px solid #4caf50; color: #2e7d32; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .info-box { background: #f5f7fa; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
        .info-box-title { font-size: 12px; color: #999; text-transform: uppercase; font-weight: 600; margin-bottom: 5px; }
        .info-box-value { font-size: 20px; font-weight: 600; color: #333; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; font-size: 12px; color: #999; }
        @media (max-width: 768px) { .container { padding: 20px; } .header { flex-direction: column; align-items: flex-start; gap: 15px; } .status { margin-left: 0; } .result-item { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🔍 ek-scraper Dashboard</h1>
                <p class="subtitle">Kleinanzeigen.de Scraper Web Interface</p>
            </div>
            <div class="status" id="status">Idle</div>
        </div>
        
        <div class="controls">
            <button class="btn-primary" id="runBtn" onclick="runScraper()">Run Scraper Now</button>
            <button class="btn-secondary" onclick="refreshStatus()">Refresh</button>
        </div>
        
        <div id="message"></div>
        <div class="info-grid" id="infoGrid" style="display: none;">
            <div class="info-box"><div class="info-box-title">Last Run</div><div class="info-box-value" id="lastRunTime">-</div></div>
            <div class="info-box"><div class="info-box-title">Results Found</div><div class="info-box-value" id="resultsCount">0</div></div>
            <div class="info-box"><div class="info-box-title">Searches</div><div class="info-box-value" id="searchesCount">0</div></div>
        </div>
        
        <div class="results-section" id="resultsSection" style="display: none;">
            <div class="results-title">Latest Results</div>
            <div id="resultsList"></div>
        </div>
        
        <div class="no-results" id="noResults">Click "Run Scraper Now" to start scraping</div>
        <div class="footer">ek-scraper v2.0.0 | <a href="https://github.com/frederikpeter20-lang/secret-scrap" style="color: #667eea;">GitHub</a></div>
    </div>
    
    <script>
        async function runScraper() {
            const btn = document.getElementById('runBtn');
            btn.disabled = true;
            showMessage('Running scraper...', 'info');
            try {
                const response = await fetch('/api/run', { method: 'POST' });
                const data = await response.json();
                if (response.ok) { showMessage('✓ Completed', 'success'); setTimeout(refreshStatus, 1000); }
                else { showMessage('✗ Error: ' + data.error, 'error'); }
            } catch (error) { showMessage('✗ Failed: ' + error, 'error'); }
            finally { btn.disabled = false; }
        }
        async function refreshStatus() {
            try { const r = await fetch('/api/status'); const d = await r.json(); updateUI(d); }
            catch (e) { console.error(e); }
        }
        function updateUI(d) {
            const s = document.getElementById('status');
            s.textContent = d.running ? 'Running' : (d.last_run ? 'Ready' : 'Idle');
            s.className = 'status ' + (d.running ? 'running' : (d.last_run ? 'success' : 'idle'));
            if (d.last_run) {
                document.getElementById('infoGrid').style.display = 'grid';
                document.getElementById('lastRunTime').textContent = new Date(d.last_run).toLocaleString();
                document.getElementById('resultsCount').textContent = d.total_results || 0;
                document.getElementById('searchesCount').textContent = d.searches_count || 0;
            }
            if (d.results && d.results.length > 0) {
                document.getElementById('resultsList').innerHTML = d.results.map(i => `
                    <div class="result-item">
                        <div><strong>${i.title}</strong><br><small>${i.location}</small></div>
                        <div><strong>${i.price}</strong><br><a href="${i.url}" target="_blank">View →</a></div>
                    </div>
                `).join('');
                document.getElementById('resultsSection').style.display = 'block';
                document.getElementById('noResults').style.display = 'none';
            }
        }
        function showMessage(msg, type) {
            const e = document.getElementById('message');
            e.innerHTML = `<div class="${type}">${msg}</div>`;
            setTimeout(() => { e.innerHTML = ''; }, 5000);
        }
        refreshStatus();
        setInterval(refreshStatus, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    return jsonify({
        'running': scraper_running,
        'last_run': last_run_time,
        'results': last_run_results or [],
        'total_results': len(last_run_results) if last_run_results else 0,
        'searches_count': get_searches_count(),
    })

@app.route('/api/run', methods=['POST'])
def api_run():
    global scraper_running, last_run_results, last_run_time
    if scraper_running:
        return jsonify({'error': 'Scraper is already running'}), 429
    try:
        scraper_running = True
        config_path = pathlib.Path('config.json')
        if not config_path.exists():
            raise FileNotFoundError('config.json not found')
        data_store_path = pathlib.Path('/tmp') / '.ek-scraper' / 'data.json'
        data_store_path.parent.mkdir(parents=True, exist_ok=True)
        asyncio.run(run_scraper(config_file=config_path, data_store=data_store_path, send_notifications=False))
        with DataStore(data_store_path) as store:
            store.open()
            last_run_results = [
                {'id': ad.id, 'title': ad.title, 'url': ad.url, 'location': ad.location, 'price': ad.price}
                for ad in list(store._data.ad_items.values())[:10]
            ]
        last_run_time = datetime.now().isoformat()
        return jsonify({'success': True, 'results_count': len(last_run_results)})
    except Exception as e:
        logger.error('Scraper error: %s', e)
        return jsonify({'error': str(e)}), 500
    finally:
        scraper_running = False

def get_searches_count() -> int:
    try:
        config_path = pathlib.Path('config.json')
        if config_path.exists():
            config = Config.model_validate_json(config_path.read_text())
            return len(config.searches)
    except Exception as e:
        logger.warning('Failed to load config: %s', e)
    return 0

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
