from flask import Flask
from flask_cors import CORS
from .routes import main

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for cross-origin requests

    # Register the blueprint for routes
    app.register_blueprint(main)

    return app