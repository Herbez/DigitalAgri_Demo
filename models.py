from flask_login import UserMixin
from datetime import datetime
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    district = db.Column(db.String(100))
    farm_size = db.Column(db.Float)  # in hectares
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with recommendations
    recommendations = db.relationship('RecommendationHistory', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'

class RecommendationHistory(db.Model):
    __tablename__ = 'recommendation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Input data
    district = db.Column(db.String(100), nullable=False)
    soil_type = db.Column(db.String(50))
    soil_ph = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    farm_size = db.Column(db.Float)
    
    # ML Model results
    recommended_crops = db.Column(db.Text)  # JSON string of recommendations
    confidence_score = db.Column(db.Float)
    planting_season = db.Column(db.String(50))
    
    # Weather data at time of recommendation
    weather_data = db.Column(db.Text)  # JSON string
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recommendation {self.id} for User {self.user_id}>'

class CropData(db.Model):
    __tablename__ = 'crop_data'
    
    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(150))
    
    # Growing conditions
    optimal_ph_min = db.Column(db.Float)
    optimal_ph_max = db.Column(db.Float)
    optimal_rainfall_min = db.Column(db.Float)
    optimal_rainfall_max = db.Column(db.Float)
    optimal_temperature_min = db.Column(db.Float)
    optimal_temperature_max = db.Column(db.Float)
    
    # Rwanda specific data
    suitable_districts = db.Column(db.Text)  # JSON string of suitable districts
    planting_season = db.Column(db.String(50))
    harvest_time_days = db.Column(db.Integer)
    
    # Market and yield data
    average_yield_per_hectare = db.Column(db.Float)
    market_price_per_kg = db.Column(db.Float)
    demand_level = db.Column(db.String(20))  # High, Medium, Low
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Crop {self.crop_name}>'

class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.String(100), nullable=False)
    
    # Current weather
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    
    # Weather forecast
    forecast_7days = db.Column(db.Text)  # JSON string
    
    # Timestamps
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Weather for {self.district}>'

class SoilData(db.Model):
    __tablename__ = 'soil_data'
    
    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.String(100), nullable=False)
    
    # Soil properties
    soil_type = db.Column(db.String(50))  # Clay, Loam, Sand, etc.
    ph_level = db.Column(db.Float)
    organic_matter = db.Column(db.Float)
    nitrogen_content = db.Column(db.Float)
    phosphorus_content = db.Column(db.Float)
    potassium_content = db.Column(db.Float)
    
    # Soil classification
    soil_fertility = db.Column(db.String(20))  # High, Medium, Low
    drainage_quality = db.Column(db.String(20))  # Good, Moderate, Poor
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Soil for {self.district}>'
