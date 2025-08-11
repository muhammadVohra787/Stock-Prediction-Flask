# For local development
from app import create_app
from livereload import Server
import os

app = create_app()
app.debug = True

if __name__ == '__main__':
    server = Server(app.wsgi_app)
    
    print("Current working directory:", os.getcwd())
    print("Files in templates directory:", os.listdir('./app/templates/'))

    server.watch('./app/templates/**/*.html')
    server.watch('./app/static/**/*')
    server.watch('app/**/*.py')

    server.serve(port=5000, host='127.0.0.1')  # You can also set open_url_delay=True
