from flask import Flask
from flask_pymongo import PyMongo
from flask_caching import Cache

mongo = PyMongo()  # Create a global mongo object
cache = Cache()  # Create a global cache object

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')  # Load Config

    # Configure cache
    app.config['CACHE_TYPE'] = 'simple'  # Can be changed to 'redis', 'memcached', etc. for production
    app.config['CACHE_DEFAULT_TIMEOUT'] = 60 * 60 * 24  # 24 hours in seconds
    
    # Initialize extensions
    mongo.init_app(app)
    cache.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
