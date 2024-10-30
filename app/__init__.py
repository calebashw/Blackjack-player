from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Redirect users to login if they're not authenticated
    login_manager.login_view = 'auth.login'

    # Import and register blueprints
    from .auth_routes import auth
    from .routes import main
    app.register_blueprint(auth)
    app.register_blueprint(main)

    return app

@login_manager.user_loader
def load_user(user_id):
    # Import User here to avoid circular import
    from .models import User
    return User.query.get(int(user_id))
