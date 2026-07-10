import os
import sqlite3
from datetime import datetime, timedelta
import random
from flask import Flask, render_template_string, request, jsonify

def init_db():
    conn = sqlite3.connect('online_analytics.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            join_date TEXT,
            last_active TEXT,
            is_blocked INTEGER DEFAULT 0,
            is_dummy INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone() == 0:
        now = datetime.now()
        my_custom_id = "admin_boss"
        try:
            cursor.execute(
                "INSERT INTO users (user_id, join_date, last_active, is_blocked, is_dummy) VALUES (?, ?, ?, 0, 0)",
                (my_custom_id, now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S'))
            )
        except:
            pass

        total_random_users = random.randint(400, 700)
        for i in range(total_random_users):
            uid = f"dummy_{1000 + i}"
            join_days = random.randint(0, 45)
            join_time = now - timedelta(days=join_days, hours=random.randint(0, 23))
            active_days = random.randint(0, join_days)
            active_time = now - timedelta(days=active_days, hours=random.randint(0, 23))
            
            cursor.execute(
                "INSERT INTO users (user_id, join_date, last_active, is_blocked, is_dummy) VALUES (?, ?, ?, 0, 1)",
                (uid, join_time.strftime('%Y-%m-%d %H:%M:%S'), active_time.strftime('%Y-%m-%d %H:%M:%S'))
            )
        conn.commit()
    conn.close()

app = Flask(__name__)

@app.route('/api/track', methods=['POST'])
def track_user():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error"}), 400
        
    conn = sqlite3.connect('online_analytics.db')
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (str(user_id),))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id, join_date, last_active, is_dummy) VALUES (?, ?, ?, 0, 0)", (str(user_id), now, now))
    else:
        cursor.execute("UPDATE users SET last_active = ?, is_dummy = 0 WHERE user_id = ?", (now, str(user_id)))
        
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route('/clean')
def clean_dummy_data():
    conn = sqlite3.connect('online_analytics.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE is_dummy = 1")
    conn.commit()
    conn.close()
    return "🧹 सारे नकली यूजर निकाल कर फेंक दिए गए हैं! अब सिर्फ आपकी असली आईडी और असली डेटा बचेगा।"

@app.route('/')
def dashboard():
    conn = sqlite3.connect('online_analytics.db')
    cursor = conn.cursor()
    
    now = datetime.now()
    t_24h = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    t_7d = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    t_30d = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (t_24h,))
    active_24h = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (t_7d,))
    active_7d = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (t_30d,))
    active_30d = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date >= ?", (t_24h,))
    new_24h = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date >= ?", (t_7d,))
    new_7d = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date >= ?", (t_30d,))
    new_30d = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 1")
    blocked = cursor.fetchone()
    
    conn.close()

    html_layout = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Admin Panel</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background-color: #000000; color: #ffffff; font-family: sans-serif; padding: 20px; }}
            .header {{ font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; letter-spacing: 1px; color: #9ca3af; }}
            .tabs {{ display: flex; gap: 8px; margin-bottom: 25px; overflow-x: auto; }}
            .tab {{ background: #111827; color: #9ca3af; padding: 8px 18px; border-radius: 20px; font-size: 13px; font-weight: 500; }}
            .tab.active {{ background: #7c3aed; color: #ffffff; }}
            .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; max-width: 500px; }}
            .card {{ background: #111827; padding: 15px; border-radius: 12px; display: flex; flex-direction: column; justify-content: space-between; min-height: 95px; border: 1px solid #1f2937; }}
            .title {{ font-size: 10px; color: #9ca3af; text-transform: uppercase; font-weight: 600; }}
            .num {{ font-size: 24px; font-weight: bold; margin-top: 4px; }}
            .sub {{ font-size: 10px; color: #4b5563; margin-top: 2px; }}
            .c-active-24 .num, .c-new-24 .num {{ color: #10b981; }}
            .c-new-7 .num, .c-new-30 .num {{ color: #f59e0b; }}
            .c-blocked .num {{ color: #ef4444; }}
        </style>
        <script>
            setInterval(() => {{
                fetch(window.location.href).then(r => r.text()).then(html => {{
                    let doc = new DOMParser().parseFromString(html, 'text/html');
                    document.querySelector('.grid').innerHTML = doc.querySelector('.grid').innerHTML;
                }});
            }}, 3000);
        </script>
    </head>
    <body>
        <div class="header">Admin Panel</div>
        <div class="tabs"><div class="tab active">Analytics</div><div class="tab">Users</div><div class="tab">Broadcasts</div></div>
        <div class="grid">
            <div class="card"><div class="title">Total Users</div><div class="num">{{total_users}}</div></div>
            <div class="card c-active-24"><div class="title">Active (24H)</div><div class="num">{{active_24h}}</div></div>
            <div class="card"><div class="title">Active (7D)</div><div class="num">{{active_7d}}</div></div>
            <div class="card"><div class="title">Active (30D)</div><div class="num">{{active_30d}</div></div>
            <div class="card c-new-24"><div class="title">New (24H)</div><div class="num">{{new_24h}}</div><div class="sub">joined today</div></div>
            <div class="card"><div class="title">New (7D)</div><div class="num">{{new_7d}}</div></div>
            <div class="card"><div class="title">New (30D)</div><div class="num">{{new_30d}}</div></div>
            <div class="card c-blocked"><div class="title">Blocked</div><div class="num">{{blocked}}</div></div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_layout)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
      
