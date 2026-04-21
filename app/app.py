from flask import Flask, jsonify, request, abort, send_from_directory
from datetime import datetime
import uuid

app = Flask(__name__, static_folder='static')

# In-memory storage — in productie zou dit een echte database zijn
tasks = {}


# ──────────────────────────────────────────
#  Frontend serveren
# ──────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return send_from_directory('static', 'index.html')


# ──────────────────────────────────────────
#  Health check — Kubernetes gebruikt dit
# ──────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


# ──────────────────────────────────────────
#  Alle taken ophalen
# ──────────────────────────────────────────
@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify({
        "tasks": list(tasks.values()),
        "count": len(tasks)
    }), 200


# ──────────────────────────────────────────
#  Één taak ophalen
# ──────────────────────────────────────────
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    task = tasks.get(task_id)
    if not task:
        abort(404, description="Taak niet gevonden")
    return jsonify(task), 200


# ──────────────────────────────────────────
#  Nieuwe taak aanmaken
# ──────────────────────────────────────────
@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()

    if not data or not data.get('title'):
        abort(400, description="Veld 'title' is verplicht")

    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "title": data['title'],
        "description": data.get('description', ''),
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    }

    tasks[task_id] = task
    return jsonify(task), 201


# ──────────────────────────────────────────
#  Taak bijwerken
# ──────────────────────────────────────────
@app.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    task = tasks.get(task_id)
    if not task:
        abort(404, description="Taak niet gevonden")

    data = request.get_json()
    if not data:
        abort(400, description="Geen data meegegeven")

    allowed_statuses = ['open', 'in_progress', 'done']
    if 'status' in data and data['status'] not in allowed_statuses:
        abort(400, description=f"Status moet één van zijn: {allowed_statuses}")

    task['title'] = data.get('title', task['title'])
    task['description'] = data.get('description', task['description'])
    task['status'] = data.get('status', task['status'])
    task['updated_at'] = datetime.utcnow().isoformat()

    return jsonify(task), 200


# ──────────────────────────────────────────
#  Taak verwijderen
# ──────────────────────────────────────────
@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = tasks.pop(task_id, None)
    if not task:
        abort(404, description="Taak niet gevonden")
    return jsonify({"message": "Taak verwijderd", "id": task_id}), 200


# ──────────────────────────────────────────
#  Error handlers
# ──────────────────────────────────────────
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad Request", "message": str(e.description)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found", "message": str(e.description)}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
