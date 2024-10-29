from app import create_app, db
from app.models import User, GameSession
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)  # Initialize Flask-Migrate with the app and db

# For CLI access to the database models
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'GameSession': GameSession}

if __name__ == '__main__':
    app.run(debug=True)
