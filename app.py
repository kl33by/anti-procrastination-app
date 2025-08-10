from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Plik do przechowywania danych
DATA_FILE = 'tasks_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'tasks': {}, 'incomplete_tasks': []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_ai_comment(task_name, days_late):
    comments = [
        f"Hmm, '{task_name}' czeka już {days_late} dni. Może warto to w końcu załatwić? 🤔",
        f"'{task_name}' - to zadanie jest jak wino, ale niestety nie poprawia się z wiekiem! 😅",
        f"Czy '{task_name}' to może być Twój nowy rekord prokrastynacji? {days_late} dni to całkiem imponujące! 📈",
        f"'{task_name}' pewnie już myśli, że zostało zapomniane. Może warto je pocieszyć wykonaniem? 💙",
        f"{days_late} dni temu '{task_name}' było ważne. Czy nadal jest? Czas to sprawdzić! ⏰",
    ]
    
    if days_late > 7:
        return f"Wow! '{task_name}' to już klasyk - {days_late} dni opóźnienia! Może czas na wielki comeback? 🚀"
    
    return random.choice(comments)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks/<date>')
def get_tasks(date):
    data = load_data()
    tasks = data['tasks'].get(date, [])
    return jsonify(tasks)

@app.route('/api/tasks/<date>', methods=['POST'])
def add_task(date):
    data = load_data()
    task_data = request.json
    
    if date not in data['tasks']:
        data['tasks'][date] = []
    
    new_task = {
        'id': len(data['tasks'][date]) + int(datetime.now().timestamp()),
        'name': task_data['name'],
        'category': task_data['category'],
        'completed': False
    }
    
    data['tasks'][date].append(new_task)
    save_data(data)
    
    return jsonify(new_task)

@app.route('/api/tasks/<date>/<int:task_id>', methods=['PUT'])
def update_task(date, task_id):
    data = load_data()
    task_data = request.json
    
    if date in data['tasks']:
        for task in data['tasks'][date]:
            if task['id'] == task_id:
                task.update(task_data)
                break
    
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/tasks/<date>/<int:task_id>', methods=['DELETE'])
def delete_task(date, task_id):
    data = load_data()
    
    if date in data['tasks']:
        data['tasks'][date] = [t for t in data['tasks'][date] if t['id'] != task_id]
    
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/incomplete-tasks')
def get_incomplete_tasks():
    data = load_data()
    today = datetime.now().strftime('%Y-%m-%d')
    incomplete = []
    
    for date, tasks in data['tasks'].items():
        if date < today:
            days_late = (datetime.now() - datetime.strptime(date, '%Y-%m-%d')).days
            for task in tasks:
                if not task['completed']:
                    incomplete.append({
                        **task,
                        'original_date': date,
                        'days_late': days_late,
                        'ai_comment': generate_ai_comment(task['name'], days_late)
                    })
    
    return jsonify(incomplete)

@app.route('/api/stats')
def get_stats():
    data = load_data()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Statystyki dla dziś
    today_tasks = data['tasks'].get(today, [])
    today_completed = sum(1 for task in today_tasks if task['completed'])
    today_total = len(today_tasks)
    
    # Historia ostatnich dni
    history = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        tasks = data['tasks'].get(date, [])
        completed = sum(1 for task in tasks if task['completed'])
        total = len(tasks)
        percentage = round((completed / total * 100)) if total > 0 else 0
        
        history.append({
            'date': date,
            'completed': completed,
            'total': total,
            'percentage': percentage
        })
    
    return jsonify({
        'today': {
            'completed': today_completed,
            'total': today_total,
            'percentage': round((today_completed / today_total * 100)) if today_total > 0 else 0
        },
        'history': history
    })

if __name__ == '__main__':
    # Sprawdź czy uruchamiamy na telefonie czy komputerze
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"🚀 Aplikacja działa na:")
    print(f"   Komputer: http://localhost:5000")
    print(f"   Telefon: http://{local_ip}:5000")
    print(f"   (Upewnij się, że telefon jest w tej samej sieci WiFi)")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
