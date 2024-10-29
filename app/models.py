from flask_login import UserMixin
from datetime import datetime
from flask_bcrypt import generate_password_hash, check_password_hash

from . import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    bankroll = db.Column(db.Integer, default=1000)  # Starting bankroll
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    games = db.relationship('GameSession', backref='user', lazy=True)

    # Methods for password hashing and checking
    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GameSession(db.Model):
    __tablename__ = 'game_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    outcome = db.Column(db.String(10))  # win/lose/tie
    bet = db.Column(db.Integer)
    final_bankroll = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def record_outcome(self, outcome, user):
        """Update session and user based on outcome."""
        self.outcome = outcome
        if outcome == "win":
            user.bankroll += self.bet * 2  # Winnings are double the bet
        elif outcome == "tie":
            user.bankroll += self.bet  # Bet is refunded on a tie
        # Save the final bankroll in this session
        self.final_bankroll = user.bankroll