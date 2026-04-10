"""
Database Initialization Script for Digital Agriculture Advisory System
Run this script to create the database and initial data
"""

from app import app, db
from models import User, RecommendationHistory, CropData, WeatherData, SoilData
from werkzeug.security import generate_password_hash
import json

def create_tables():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def add_sample_data():
    """Add sample data for testing"""
    with app.app_context():
        # Sample user
        if not User.query.filter_by(email='admin@digitalagri.rw').first():
            admin_user = User(
                name='Admin User',
                email='admin@digitalagri.rw',
                password=generate_password_hash('admin123'),
                district='Kigali',
                farm_size=5.0
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created!")

        if not User.query.filter_by(email='testuser@digitalagri.rw').first():
            test_user = User(
                name='Test User',
                email='testuser@digitalagri.rw',
                password=generate_password_hash('test1234'),
                district='Northern Province',
                farm_size=2.5
            )
            db.session.add(test_user)
            db.session.commit()
            print("Test user created!")

        # Sample crop data
        sample_crops = [
            {
                'crop_name': 'Maize',
                'scientific_name': 'Zea mays',
                'optimal_ph_min': 5.5,
                'optimal_ph_max': 7.0,
                'optimal_rainfall_min': 500,
                'optimal_rainfall_max': 800,
                'optimal_temperature_min': 18,
                'optimal_temperature_max': 30,
                'suitable_districts': json.dumps(['Kigali', 'Northern Province', 'Southern Province']),
                'planting_season': 'March-May',
                'harvest_time_days': 120,
                'average_yield_per_hectare': 3.5,
                'market_price_per_kg': 0.3,
                'demand_level': 'High'
            },
            {
                'crop_name': 'Beans',
                'scientific_name': 'Phaseolus vulgaris',
                'optimal_ph_min': 6.0,
                'optimal_ph_max': 7.5,
                'optimal_rainfall_min': 400,
                'optimal_rainfall_max': 600,
                'optimal_temperature_min': 15,
                'optimal_temperature_max': 25,
                'suitable_districts': json.dumps(['Northern Province', 'Southern Province', 'Eastern Province']),
                'planting_season': 'February-April',
                'harvest_time_days': 90,
                'average_yield_per_hectare': 1.2,
                'market_price_per_kg': 0.8,
                'demand_level': 'High'
            },
            {
                'crop_name': 'Coffee',
                'scientific_name': 'Coffea arabica',
                'optimal_ph_min': 6.0,
                'optimal_ph_max': 6.5,
                'optimal_rainfall_min': 1200,
                'optimal_rainfall_max': 1500,
                'optimal_temperature_min': 15,
                'optimal_temperature_max': 24,
                'suitable_districts': json.dumps(['Western Province', 'Northern Province']),
                'planting_season': 'March-May',
                'harvest_time_days': 270,
                'average_yield_per_hectare': 0.8,
                'market_price_per_kg': 3.5,
                'demand_level': 'High'
            }
        ]

        for crop_data in sample_crops:
            if not CropData.query.filter_by(crop_name=crop_data['crop_name']).first():
                crop = CropData(**crop_data)
                db.session.add(crop)

        # Sample soil data
        sample_soils = [
            {
                'district': 'Kigali',
                'soil_type': 'Loam',
                'ph_level': 6.2,
                'organic_matter': 3.5,
                'nitrogen_content': 0.15,
                'phosphorus_content': 0.08,
                'potassium_content': 0.25,
                'soil_fertility': 'High',
                'drainage_quality': 'Good'
            },
            {
                'district': 'Northern Province',
                'soil_type': 'Clay',
                'ph_level': 5.8,
                'organic_matter': 4.2,
                'nitrogen_content': 0.18,
                'phosphorus_content': 0.10,
                'potassium_content': 0.30,
                'soil_fertility': 'High',
                'drainage_quality': 'Moderate'
            },
            {
                'district': 'Eastern Province',
                'soil_type': 'Sand',
                'ph_level': 6.5,
                'organic_matter': 2.8,
                'nitrogen_content': 0.12,
                'phosphorus_content': 0.06,
                'potassium_content': 0.20,
                'soil_fertility': 'Medium',
                'drainage_quality': 'Good'
            }
        ]

        for soil_data in sample_soils:
            if not SoilData.query.filter_by(district=soil_data['district']).first():
                soil = SoilData(**soil_data)
                db.session.add(soil)

        db.session.commit()
        print("Sample data added successfully!")

def main():
    """Main function to initialize database"""
    print("Initializing Digital Agriculture Advisory System Database...")
    
    try:
        create_tables()
        add_sample_data()
        print("\nDatabase initialization completed successfully!")
        print("\nLogin credentials:")
        print("Email: admin@digitalagri.rw")
        print("Password: admin123")
        print("Email: testuser@digitalagri.rw")
        print("Password: test1234")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    main()
