import os
from flask import Flask
from app.config import Config
from app.extensions import db, jwt, cors, setup_logger

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Setup logger
    setup_logger(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.image import image_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(image_bp, url_prefix='/api/image')

    # Create Database Tables if not exist
    with app.app_context():
        db.create_all()

    return app
