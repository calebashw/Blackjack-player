from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
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

    migrate = Migrate(app, db)

    with app.app_context():
        from .models import User, GameSession

    # Enable CORS globally for API routes with credentials
    CORS(
        app,
        resources={r"/api/*": {"origins": "http://localhost:3000"}},
        supports_credentials=True
    )

    # Redirect users to login if they are not authenticated
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Import and register blueprints
    from .auth_routes import auth
    from .routes import main
    app.register_blueprint(auth, url_prefix="/api/auth")  # Authentication routes
    app.register_blueprint(main, url_prefix="/api/main")  # Main app routes

    # Test route for sanity checking
    @app.route("/api/health", methods=["GET"])
    def health_check():
        try:
            db.session.execute("SELECT 1")  # Test database connection
            return {"status": "OK", "message": "API is healthy!"}, 200
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}, 500

    return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))
