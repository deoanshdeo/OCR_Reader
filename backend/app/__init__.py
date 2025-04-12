# Welcome to my Flask app setup! This file is the starter for the web server.
# Setting up the basics and connecting different parts of the project.

from flask import Flask
from flask_cors import CORS
from .routes import main

def create_app():
    app = Flask(__name__)

    # This lets our app talk to websites from different domains safely,

    CORS(app)  # Enable CORS for cross-origin requests

    # Register the blueprint for routes
    app.register_blueprint(main)

    return app