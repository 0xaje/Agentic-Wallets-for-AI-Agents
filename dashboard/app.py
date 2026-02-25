from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import subprocess
import threading
import queue
import time
import os
import signal

app = Flask(__name__)
CORS(app)

# Global process management
current_process = None
log_queue = queue.Queue()

def stream_logs(process):
    """Read logs from a process and put them into the queue."""
    for line in iter(process.stdout.readline, ''):
        log_queue.put(line)
    process.stdout.close()
    return_code = process.wait()
    log_queue.put(f"Process finished with exit code {return_code}\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Trigger agent.py status and return the result."""
    try:
        result = subprocess.check_output(['python', 'agent.py', 'status'], text=True, stderr=subprocess.STDOUT)
        return jsonify({"success": True, "output": result})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output}), 500

@app.route('/api/fund', methods=['POST'])
def fund_wallet():
    """Trigger agent.py fund."""
    global current_process
    if current_process and current_process.poll() is None:
        return jsonify({"success": False, "error": "A process is already running"}), 400

    current_process = subprocess.Popen(
        ['python', 'agent.py', 'fund'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    threading.Thread(target=stream_logs, args=(current_process,), daemon=True).start()
    return jsonify({"success": True})

@app.route('/api/run', methods=['POST'])
def run_agent():
    """Trigger agent.py run."""
    global current_process
    if current_process and current_process.poll() is None:
        return jsonify({"success": False, "error": "A process is already running"}), 400

    strategy = request.json.get('strategy', 'random')
    rounds = request.json.get('rounds', '1')
    interval = request.json.get('interval', '10')
    vault = request.json.get('vault', '')

    cmd = ['python', 'agent.py', 'run', '--strategy', strategy, '--rounds', str(rounds), '--interval', str(interval)]
    if strategy == 'sweep' and vault:
        cmd.extend(['--vault', vault])

    current_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    threading.Thread(target=stream_logs, args=(current_process,), daemon=True).start()
    return jsonify({"success": True})

@app.route('/api/stop', methods=['POST'])
def stop_agent():
    """Stop the current running process."""
    global current_process
    if current_process and current_process.poll() is None:
        # On Windows, we might need a different way to kill the process tree if it's complex
        # but for simple cases current_process.terminate() works.
        current_process.terminate()
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "No process running"}), 400

@app.route('/api/logs')
def logs():
    """SSE endpoint for streaming logs."""
    def event_stream():
        while True:
            try:
                # Use a small timeout to allow checking for server shutdown etc.
                line = log_queue.get(timeout=10)
                yield f"data: {line}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
    
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Ensure we are running from the root of the project
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app.run(debug=False, port=5000)
