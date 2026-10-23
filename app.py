from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "codex_super_secret_key_change_this"

DB_NAME = "codex_licensing.db"
ADMIN_USER = "codex_admin"
ADMIN_PASS = "bhai_ka_secure_password_123"  # Yahan apna password rakh lena

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            device_id TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY,
            latest_version TEXT,
            download_url TEXT
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO app_settings (id, latest_version, download_url) VALUES (1, '26.09.14.1', 'https://yourwebsite.com/download/jiohotstar.apk')")
    conn.commit()
    conn.close()

init_db()

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Codex Master Admin</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: monospace; padding: 20px; }
        h1, h2 { color: #f97316; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #334155; padding: 10px; text-align: left; }
        th { background: #1e293b; }
        button, input { background: #334155; color: white; border: none; padding: 8px 12px; margin: 5px 0; cursor: pointer; }
        button:hover, input[type="submit"] { background: #f97316; }
        .box { background: #1e293b; padding: 15px; margin-bottom: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>CODEX // SECURE MASTER ADMIN PANEL</h1>
    <a href="/codex-logout" style="color: #ef4444;">[ Logout ]</a>

    <div class="box">
        <h2>App Version Control</h2>
        <form method="POST" action="/update-app-settings">
            <label>Latest App Version:</label><br>
            <input type="text" name="version" value="{{ settings[1] }}"><br>
            <label>New APK Download URL:</label><br>
            <input type="text" name="url" value="{{ settings[2] }}" style="width: 400px;"><br>
            <button type="submit">Update Config</button>
        </form>
    </div>

    <div class="box">
        <h2>License Keys & Active Users</h2>
        <form method="POST" action="/codex-super-secret-admin-panel/generate">
            <button type="submit">Generate New License Key</button>
        </form>
        <table>
            <tr><th>ID</th><th>Key</th><th>Device ID (Client)</th><th>Status</th><th>Action</th></tr>
            {% for row in keys %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] or 'Not Logged In Yet' }}</td>
                <td>{{ row[3] }}</td>
                <td>
                    <form method="POST" action="/codex-super-secret-admin-panel/toggle/{{ row[0] }}" style="display:inline;">
                        <button type="submit">{{ 'Revoke / Block' if row[3] == 'active' else 'Activate' }}</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Admin Login</title></head>
<body style="background: #0f172a; color: white; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh;">
    <form method="POST" style="background: #1e293b; padding: 30px; border-radius: 8px;">
        <h2 style="color: #f97316;">CODEX ADMIN LOGIN</h2>
        {% if error %}<p style="color: red;">{{ error }}</p>{% endif %}
        <label>Username:</label><br><input type="text" name="username" required><br><br>
        <label>Password:</label><br><input type="password" name="password" required><br><br>
        <button type="submit" style="background: #f97316; border: none; padding: 10px 20px; color: white; cursor: pointer;">Login</button>
    </form>
</body>
</html>
"""

@app.route('/codex-super-secret-admin-panel', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Galat username ya password!"
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/codex-panel-dashboard')
def admin_panel():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, license_key, device_id, status FROM keys")
    keys = cursor.fetchall()
    cursor.execute("SELECT * FROM app_settings WHERE id = 1")
    settings = cursor.fetchone()
    conn.close()
    return render_template_string(ADMIN_HTML, keys=keys, settings=settings)

@app.route('/codex-logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/codex-super-secret-admin-panel/generate', methods=['POST'])
def generate_key():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    import uuid
    new_key = f"CODEX-{uuid.uuid4().hex[:8].upper()}"
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keys (license_key, created_at) VALUES (?, ?)", (new_key, str(datetime.now())))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/codex-super-secret-admin-panel/toggle/<int:key_id>', methods=['POST'])
def toggle_key(key_id):
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM keys WHERE id = ?", (key_id,))
    current = cursor.fetchone()[0]
    new_status = 'revoked' if current == 'active' else 'active'
    cursor.execute("UPDATE keys SET status = ? WHERE id = ?", (new_status, key_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/update-app-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    version = request.form.get('version')
    url = request.form.get('url')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE app_settings SET latest_version = ?, download_url = ? WHERE id = 1", (version, url))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/api/verify', methods=['POST'])
def verify_key():
    data = request.json or {}
    license_key = data.get('key')
    device_id = data.get('device_id')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT latest_version, download_url FROM app_settings WHERE id = 1")
    app_info = cursor.fetchone()
    
    cursor.execute("SELECT device_id, status FROM keys WHERE license_key = ?", (license_key,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"status": "invalid", "message": "Key galat hai!"})
        
    bound_device, status = row
    if status != 'active':
        return jsonify({"status": "revoked", "message": "Key block kar di gayi hai!"})
        
    if bound_device is None:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE keys SET device_id = ? WHERE license_key = ?", (device_id, license_key))
        conn.commit()
        conn.close()
    elif bound_device != device_id:
        return jsonify({"status": "mismatch", "message": "Yeh key kisi aur device ki hai!"})
        
    return jsonify({
        "status": "success", 
        "message": "Access granted",
        "latest_version": app_info[0],
        "download_url": app_info[1]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
