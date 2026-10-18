from flask import Flask, render_template_string, request, redirect, url_for
import os, subprocess, zipfile, psutil

app = Flask(__name__)
BOTS_DIR = "bots"
os.makedirs(BOTS_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Hiro Panel</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: sans-serif; padding: 20px; }
        .card { background: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
        .btn { background: #10b981; color: white; padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px;}
        .btn-red { background: #ef4444; }
        input[type="text"], input[type="file"] { margin-bottom: 10px; padding: 5px; }
        table { width: 100%; text-align: left; border-collapse: collapse; }
        th, td { padding: 10px; border-bottom: 1px solid #334155; }
    </style>
</head>
<body>
    <h1>Hiro Panel (Karbitan)</h1>
    
    <div class="card">
        <h3>Monitor Server</h3>
        <p>CPU: {{ cpu }}% | RAM: {{ ram }}% | Disk: {{ disk }}%</p>
    </div>

    <div class="card">
        <h3>Deploy Bot Baru</h3>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="text" name="name" placeholder="Nama Bot (cth: bot-wa)" required><br>
            <input type="file" name="zipfile" accept=".zip" required><br>
            <button type="submit" class="btn">Upload & Deploy</button>
        </form>
    </div>

    <div class="card">
        <h3>Daftar Bot</h3>
        <table>
            <tr><th>Nama Bot</th><th>Status</th><th>Aksi</th></tr>
            {% for bot in bots %}
            <tr>
                <td>{{ bot.name }}</td>
                <td>{{ "Running" if bot.running else "Stopped" }}</td>
                <td>
                    <form action="/run/{{ bot.name }}" method="post" style="display:inline;">
                        <button type="submit" class="btn" style="padding:5px 10px; font-size:12px;">Start</button>
                    </form>
                    <form action="/stop/{{ bot.name }}" method="post" style="display:inline;">
                        <button type="submit" class="btn btn-red" style="padding:5px 10px; font-size:12px;">Stop</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    bots = []
    for name in os.listdir(BOTS_DIR):
        path = os.path.join(BOTS_DIR, name)
        if os.path.isdir(path):
            is_running = any(name in " ".join(p.info['cmdline'] or []) for p in psutil.process_iter(['cmdline']))
            bots.append({"name": name, "running": is_running})
    
    disk = psutil.disk_usage('/').percent
    return render_template_string(HTML, cpu=psutil.cpu_percent(), ram=psutil.virtual_memory().percent, disk=disk, bots=bots)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['zipfile']
    name = request.form['name']
    bot_path = os.path.join(BOTS_DIR, name)
    os.makedirs(bot_path, exist_ok=True)
    
    zip_path = os.path.join(bot_path, "bot.zip")
    file.save(zip_path)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(bot_path)
    os.remove(zip_path)
    
    req_file = os.path.join(bot_path, "requirements.txt")
    if os.path.exists(req_file):
        subprocess.run(["pip", "install", "-r", req_file])
    
    return redirect(url_for('index'))

@app.route('/run/<bot_name>', methods=['POST'])
def run_bot(bot_name):
    bot_path = os.path.join(BOTS_DIR, bot_name)
    subprocess.Popen(["python3", "main.py"], cwd=bot_path)
    return redirect(url_for('index'))

@app.route('/stop/<bot_name>', methods=['POST'])
def stop_bot(bot_name):
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = " ".join(p.info['cmdline'] or [])
            if bot_name in cmdline and "main.py" in cmdline:
                p.kill()
        except: pass
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2121)
