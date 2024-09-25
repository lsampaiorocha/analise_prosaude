# app/__init__.py
from flask import Flask
from .routes import configure_routes
import os

def create_app():
    app = Flask(__name__)
    UPLOAD_FOLDER = 'temp'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 25* 1024 * 1024 # Tamanho máximo: 25MB
    configure_routes(app)
    return app
