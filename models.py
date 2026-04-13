from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(255), nullable=False)
    province = db.Column(db.String(255), nullable=True)
    farm_size_ha = db.Column(db.Float, nullable=True)
    role = db.Column(db.String(50), nullable=False, default="farmer")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    recommendation_history = db.relationship("RecommendationHistory", back_populates="user", lazy=True)


class RecommendationHistory(db.Model):
    __tablename__ = "recommendation_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    district = db.Column(db.String(255), nullable=False)
    province = db.Column(db.String(255), nullable=True)
    soil_ph = db.Column(db.Float, nullable=False)
    nitrogen = db.Column(db.Float, nullable=False)
    phosphorus = db.Column(db.Float, nullable=False)
    potassium = db.Column(db.Float, nullable=False)
    annual_rainfall_mm = db.Column(db.Float, nullable=False)
    avg_temperature_C = db.Column(db.Float, nullable=False)
    avg_humidity_pct = db.Column(db.Float, nullable=False)
    altitude_m = db.Column(db.Float, nullable=False)
    predicted_crop = db.Column(db.String(255), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    score_payload = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="recommendation_history")
