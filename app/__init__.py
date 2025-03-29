from flask import Flask
from flask_pymongo import PyMongo

mongo = PyMongo()  # Create a global mongo object

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')  # Load Config

    # Initialize PyMongo
    mongo.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
