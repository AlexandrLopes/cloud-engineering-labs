import os
import socket
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    # Get the hostname (inside Docker, this is the Container ID)
    hostname = socket.gethostname()
    
    # Get the Environment Variable (Default to 'Development' if not set)
    env_name = os.getenv('APP_ENV', 'Development')
    
    return f'''
    <h1>Hello from {env_name} Environment!</h1>
    <p>I am a Python application running inside a Container.</p>
    <p><b>Container ID (Hostname):</b> {hostname}</p>
    '''

if __name__ == '__main__':
    # Run on all available interfaces (0.0.0.0)
    app.run(host='0.0.0.0', port=5000)