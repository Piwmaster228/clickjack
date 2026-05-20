import json
import os
import sqlite3
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'tracking.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source      TEXT,
            timestamp   TEXT,
            ip          TEXT,
            user_agent  TEXT,
            screen      TEXT,
            timezone    TEXT,
            language    TEXT,
            canvas_fp   TEXT,
            webgl_fp    TEXT,
            fonts       TEXT,
            plugins     INTEGER,
            click_event INTEGER DEFAULT 0,
            profile_id  INTEGER DEFAULT NULL
        )
    ''')
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_matching():
    conn = get_db()
    rows = conn.execute('SELECT * FROM visits').fetchall()
    visits = [dict(r) for r in rows]
    conn.close()

    if len(visits) < 2:
        return

    conn = get_db()
    row_max = conn.execute('SELECT MAX(profile_id) FROM visits').fetchone()[0]
    pid_new = (row_max or 0) + 1

    visits = [dict(r) for r in conn.execute('SELECT * FROM visits').fetchall()]

    flag = True
    while flag:
        flag = False
        for i in range(len(visits)):
            for j in range(i + 1, len(visits)):
                v1 = visits[i]
                v2 = visits[j]

                if v1['source'] == v2['source']:
                    continue

                if (v1['profile_id'] and v2['profile_id'] and
                        v1['profile_id'] == v2['profile_id']):
                    continue

                pts = 0

                if (v1['canvas_fp'] and v2['canvas_fp'] and
                        v1['canvas_fp'] == v2['canvas_fp']):
                    pts += 1

                if (v1['webgl_fp'] and v2['webgl_fp'] and
                        v1['webgl_fp'] == v2['webgl_fp']):
                    pts += 1

                if (v1['timezone'] == v2['timezone'] and
                        v1['language'] == v2['language'] and
                        v1['screen'] == v2['screen'] and
                        v1['plugins'] == v2['plugins']):
                    pts += 1

                if pts >= 2:
                    pid = v1['profile_id'] or v2['profile_id'] or pid_new
                    if pid == pid_new:
                        pid_new += 1

                    conn.execute(
                        'UPDATE visits SET profile_id = ? WHERE id = ?', (pid, v1['id']))
                    conn.execute(
                        'UPDATE visits SET profile_id = ? WHERE id = ?', (pid, v2['id']))
                    conn.commit()

                    visits[i]['profile_id'] = pid
                    visits[j]['profile_id'] = pid
                    flag = True

    conn.close()


@app.route('/track', methods=['POST', 'OPTIONS'])
def track():
    if request.method == 'OPTIONS':
        resp = app.make_response('')
        resp.headers['Access-Control-Allow-Origin']  = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'message': 'empty body'}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    conn = get_db()
    conn.execute('''
        INSERT INTO visits
            (source, timestamp, ip, user_agent, screen, timezone, language,
             canvas_fp, webgl_fp, fonts, plugins, click_event)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('source', ''),
        data.get('timestamp', ''),
        ip,
        data.get('user_agent', ''),
        data.get('screen', ''),
        data.get('timezone', ''),
        data.get('language', ''),
        data.get('canvas_fp', ''),
        data.get('webgl_fp', ''),
        json.dumps(data.get('fonts', []), ensure_ascii=False),
        int(data.get('plugins', 0)),
        1 if data.get('click_event') else 0
    ))
    conn.commit()
    conn.close()

    run_matching()

    return jsonify({'status': 'ok'})


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/api/visits')
def api_visits():
    conn = get_db()
    rows = conn.execute('SELECT * FROM visits ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/profiles')
def api_profiles():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM visits WHERE profile_id IS NOT NULL ORDER BY profile_id, id'
    ).fetchall()
    conn.close()

    groups: dict = {}
    for r in rows:
        r = dict(r)
        pid = r['profile_id']
        if pid not in groups:
            groups[pid] = []
        groups[pid].append(r)

    profiles = []
    for pid, visits in groups.items():
        sources = list({v['source'] for v in visits})
        timestamps = [v['timestamp'] for v in visits if v['timestamp']]

        matching = []
        v_list = sorted(visits, key=lambda v: v['source'])
        if len(v_list) >= 2:
            v1, v2 = v_list[0], v_list[1]
            if v1['canvas_fp'] and v1['canvas_fp'] == v2['canvas_fp']:
                matching.append('Canvas Fingerprint')
            if v1['webgl_fp'] and v1['webgl_fp'] == v2['webgl_fp']:
                matching.append('WebGL Fingerprint')
            if (v1['timezone'] == v2['timezone'] and
                    v1['language'] == v2['language'] and
                    v1['screen'] == v2['screen'] and
                    v1['plugins'] == v2['plugins']):
                matching.append('Timezone + Language + Screen + Plugins')

        profiles.append({
            'profile_id':        pid,
            'visit_count':       len(visits),
            'sources':           sources,
            'matching_criteria': matching,
            'time_first':        min(timestamps) if timestamps else None,
            'time_last':         max(timestamps) if timestamps else None,
            'visits':            visits
        })

    return jsonify(profiles)


@app.route('/api/match', methods=['POST'])
def api_match():
    run_matching()
    conn = get_db()
    n = conn.execute(
        'SELECT COUNT(DISTINCT profile_id) FROM visits WHERE profile_id IS NOT NULL'
    ).fetchone()[0]
    conn.close()
    return jsonify({'status': 'ok', 'profiles_formed': n})


if __name__ == '__main__':
    init_db()
    print('Трекинг-сервер запущен на http://localhost:5002')
    print('Панель администратора: http://localhost:5002/admin')
    app.run(host='0.0.0.0', port=5002, debug=True)
