# Digital Agriculture Advisory System for Crop Selection

A Flask-based web application that provides machine learning-powered crop recommendations for Rwandan farmers.

## Features

- **User Authentication**: Secure login and registration system
- **Crop Recommendations**: ML-based suggestions based on soil, climate, and geographic data
- **Dashboard**: Personalized user dashboard with recommendation history
- **Responsive Design**: Mobile-friendly interface using Bootstrap
- **Database Integration**: MySQL database with comprehensive data models
- **Real-time Weather**: Weather API integration (ready for implementation)

## Requirements

- Python 3.8+
- MySQL 5.7+
- pip package manager

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "Digital Agriculture Advisory System for Crop Selection"
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

#### Create MySQL Database
```sql
CREATE DATABASE digital_agriculture;
CREATE USER 'agri_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON digital_agriculture.* TO 'agri_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Update Database Configuration
Edit the `.env` file:
```
DATABASE_URL=mysql+pymysql://agri_user:your_password@localhost/digital_agriculture
```

### 5. Initialize Database
```bash
python init_db.py
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
Digital Agriculture Advisory System for Crop Selection/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── dashboard.html    # User dashboard
│   ├── about.html       # About page
│   ├── services.html     # Services page
│   └── contact.html     # Contact page
├── static/              # Static files
│   └── assets/         # CSS, JS, images
└── README.md           # This file
```

## Database Schema

### Users Table
- User authentication and profile information
- Stores farm details and preferences

### CropData Table
- Comprehensive crop information
- Growing conditions and requirements
- Market data and yield information

### SoilData Table
- Soil characteristics by district
- Nutrient levels and fertility ratings

### WeatherData Table
- Current and forecast weather data
- District-specific weather information

### RecommendationHistory Table
- User recommendation history
- Input parameters and ML model results

## Default Login Credentials

After running `init_db.py`:

- **Email**: admin@digitalagri.rw
- **Password**: admin123

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Recommendations
- `POST /api/recommend` - Get crop recommendations (requires authentication)

### Pages
- `GET /` - Home page
- `GET /dashboard` - User dashboard (requires authentication)
- `GET /about` - About page
- `GET /services` - Services page
- `GET /contact` - Contact page

## Configuration

### Environment Variables (.env file)
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://username:password@localhost/digital_agriculture
WEATHER_API_KEY=your-weather-api-key
WEATHER_API_URL=https://api.openweathermap.org/data/2.5
MODEL_PATH=models/crop_recommendation_model.pkl
```

## Next Steps

1. **Machine Learning Model Integration**
   - Train crop recommendation models
   - Implement prediction endpoints
   - Add model validation

2. **Weather API Integration**
   - Sign up for weather API service
   - Implement real-time weather data fetching
   - Add weather-based recommendations

3. **Enhanced Features**
   - Email notifications
   - Mobile app integration
   - Advanced analytics dashboard
   - Multi-language support (Kinyarwanda)

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Database**: MySQL
- **Authentication**: Flask-Login, Werkzeug
- **Deployment**: Ready for production deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Email: info@digitalagri.rw
- Phone: +250 788 123 456

---

**Note**: This is a comprehensive agricultural advisory system designed specifically for Rwandan farmers. The system integrates machine learning, real-time data, and user-friendly interfaces to improve agricultural productivity and sustainability.
