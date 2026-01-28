from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def hello_world():
    hostname = socket.gethostname()
    return f'''
    <h1>Hello from Docker!</h1>
    <p>I am a Python application running inside a Container.</p>
    <p><b>Container ID (Hostname):</b> {hostname}</p>
    '''

if __name__ == '__main__':
    # Run on all available interfaces (0.0.0.0)
    app.run(host='0.0.0.0', port=5000)