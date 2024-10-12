import subprocess
import os
import sys

# Initialize process references
flask_process = None
laravel_process = None
react_process = None

def run_flask():
    global flask_process
    # Run the Flask app
    flask_process = subprocess.Popen([r'C:\Users\jeflo\Documents\Python\capstone-backend\.venv\Scripts\python.exe', 
                                      r'C:\Users\jeflo\Documents\Python\capstone-backend\main\app.py'])

def run_laravel():
    global laravel_process
    # Run the Laravel server
    os.chdir(r'C:\laragon\www\capstone-backend')
    laravel_process = subprocess.Popen([r'C:\laragon\bin\php\php-8.1.10-Win32-vs16-x64\php.exe', 'artisan', 'serve'])

def run_react():
    global react_process
    # Run the React development server
    os.chdir(r'C:\Users\jeflo\Documents\React\capstone-frontend')
    react_process = subprocess.Popen([r'C:\Program Files\nodejs\npm', 'start'], shell=True)

if __name__ == '__main__':
    try:
        # Run all the servers
        run_flask()
        run_laravel()
        run_react()
        
        # Wait for all processes to finish
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopping all servers...")
        # Terminate all subprocesses
        if flask_process:
            flask_process.terminate()
        if laravel_process:
            laravel_process.terminate()
        if react_process:
            react_process.terminate()
        sys.exit(0)