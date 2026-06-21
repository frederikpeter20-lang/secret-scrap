from flask import Flask, render_template_string
import psutil
import subprocess
from datetime import datetime

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>ek-scraper Dashboard</title>
<style>
body {font-family: Arial; background: #f0f0f0; padding: 20px;}
.green {color: green;}
.yellow {color: orange;}
.red {color: red;}
</style>
</head>
<body>
<h1>ek-scraper Monitoring</h1>
<p><strong>CPU:</strong> {{ cpu }}% | <strong>RAM verfügbar:</strong> {{ ram }} MB</p>
<h2>Laufende Scraper</h2>
<table border="1">
<tr><th>Name</th><th>Status</th><th>CPU</th><th>Letzter Lauf</th></tr>
{% for s in scrapers %}
<tr>
<td>{{ s.name }}</td>
<td class="{{ s.status_class }}">{{ s.status }}</td>
<td>{{ s.cpu }}%</td>
<td>{{ s.last_run }}</td>
</tr>
{% endfor %}
</table>
</body>
</html>
"""

@app.route("/")
def dashboard():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
        if 'ek-scraper' in ' '.join(proc.info['cmdline'] or []):
            processes.append({
                "name": proc.info['name'],
                "status": "running",
                "status_class": "green",
                "cpu": round(proc.info['cpu_percent'], 1),
                "last_run": datetime.now().strftime("%H:%M:%S")
            })
    
    return render_template_string(HTML, 
                                  cpu=psutil.cpu_percent(),
                                  ram=round(psutil.virtual_memory().available / (1024**2)),
                                  scrapers=processes or [{"name":"Kein Scraper", "status":"inactive", "status_class":"yellow", "cpu":0, "last_run":"-"}])

if __name__ == "__main__":
    print("Dashboard läuft auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
