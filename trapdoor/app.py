import os
import subprocess
import threading
import time
from flask import Flask, render_template, jsonify, Response

app = Flask(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(SCRIPT_DIR, 'on_complete.sh')

# Global countdown state
countdown_state = {
    'running': False,
    'current_time': 60,  # Default 60 seconds
    'initial_time': 60,
    'triggered': False,
    'trigger_success': None,
    'trigger_error': None
}
countdown_lock = threading.Lock()
countdown_thread = None


def run_countdown():
    """Background thread that runs the countdown."""
    global countdown_state

    while True:
        with countdown_lock:
            if not countdown_state['running']:
                break
            if countdown_state['current_time'] <= 0:
                countdown_state['running'] = False
                countdown_state['triggered'] = True
                # Execute bash script when countdown reaches zero
                try:
                    result = subprocess.run(['bash', SCRIPT_PATH], check=True, cwd=SCRIPT_DIR, capture_output=True, text=True)
                    countdown_state['trigger_success'] = True
                    countdown_state['trigger_error'] = None
                except subprocess.CalledProcessError as e:
                    countdown_state['trigger_success'] = False
                    countdown_state['trigger_error'] = f"Script failed: {e.stderr or e.stdout or str(e)}"
                except FileNotFoundError:
                    countdown_state['trigger_success'] = False
                    countdown_state['trigger_error'] = f"{SCRIPT_PATH} not found"
                break
            countdown_state['current_time'] -= 1

        time.sleep(1)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/status')
def status():
    """Return current countdown status."""
    with countdown_lock:
        return jsonify({
            'running': countdown_state['running'],
            'current_time': countdown_state['current_time'],
            'initial_time': countdown_state['initial_time'],
            'triggered': countdown_state['triggered'],
            'trigger_success': countdown_state['trigger_success'],
            'trigger_error': countdown_state['trigger_error']
        })


@app.route('/start', methods=['POST'])
def start():
    """Start the countdown."""
    global countdown_thread

    with countdown_lock:
        if countdown_state['running']:
            return jsonify({'status': 'already running'})

        if countdown_state['current_time'] <= 0:
            countdown_state['current_time'] = countdown_state['initial_time']

        countdown_state['running'] = True

    countdown_thread = threading.Thread(target=run_countdown, daemon=True)
    countdown_thread.start()

    return jsonify({'status': 'started'})


@app.route('/stop', methods=['POST'])
def stop():
    """Stop the countdown."""
    with countdown_lock:
        countdown_state['running'] = False

    return jsonify({'status': 'stopped'})


@app.route('/reset', methods=['POST'])
def reset():
    """Reset the countdown to initial time."""
    with countdown_lock:
        countdown_state['running'] = False
        countdown_state['current_time'] = countdown_state['initial_time']
        countdown_state['triggered'] = False
        countdown_state['trigger_success'] = None
        countdown_state['trigger_error'] = None

    return jsonify({'status': 'reset'})


@app.route('/set_time/<int:seconds>', methods=['POST'])
def set_time(seconds):
    """Set the initial countdown time."""
    with countdown_lock:
        if countdown_state['running']:
            return jsonify({'status': 'error', 'message': 'Cannot set time while running'})

        countdown_state['initial_time'] = seconds
        countdown_state['current_time'] = seconds

    return jsonify({'status': 'time set', 'seconds': seconds})


@app.route('/stream')
def stream():
    """Server-Sent Events endpoint for real-time updates."""
    def generate():
        while True:
            with countdown_lock:
                data = {
                    'running': countdown_state['running'],
                    'current_time': countdown_state['current_time']
                }
            yield f"data: {data}\n\n"
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=False, threaded=True, host='0.0.0.0', port=5001)
