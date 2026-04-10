from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
import joblib
from datetime import datetime
from dotenv import load_dotenv
from extensions import db, init_extensions, login_manager

load_dotenv()

app = Flask(__name__)

# Load ML model
model = None
try:
    model_path = os.path.join(os.path.dirname(__file__), 'best_model.pkl')
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print("ML model loaded successfully")
except Exception as e:
    print(f"Error loading ML model: {e}")

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///digital_agriculture.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
init_extensions(app)

# Import models after db initialization
from models import User, RecommendationHistory

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('components/about.html')

@app.route('/services')
def services():
    return render_template('components/services.html')

@app.route('/contact')
def contact():
    return render_template('components/contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            # Redirect admin users to admin dashboard, others to regular dashboard
            if user.email == 'admin@digitalagri.rw':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        district = request.form.get('district')
        farm_size = request.form.get('farmSize')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            district=district,
            farm_size=float(farm_size) if farm_size else None
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Automatically log in the user after registration
        login_user(user)
        
        # Redirect to appropriate dashboard based on user role
        if user.email == 'admin@digitalagri.rw':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    
    return render_template('auth/register.html')

@app.route('/dashboard/history')
@login_required
def history_page():
    recommendations = RecommendationHistory.query.filter_by(user_id=current_user.id).order_by(RecommendationHistory.created_at.desc()).all()
    return render_template('dashboard/history.html', recommendations=recommendations)

@app.route('/dashboard/recommendation')
@login_required
def recommendation_page():
    return render_template('dashboard/recommendation.html')

@app.route('/dashboard')
@login_required
def dashboard():
    recommendations = RecommendationHistory.query.filter_by(user_id=current_user.id).order_by(RecommendationHistory.created_at.desc()).limit(10).all()
    return render_template('dashboard/user.html', recommendations=recommendations)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/api/recommend', methods=['POST'])
@login_required
def recommend():
    if not model:
        return jsonify({'error': 'ML model not available'}), 503

    try:
        # Extract features from form data
        data = {
            'nitrogen': float(request.form.get('nitrogen', 0)),
            'phosphorus': float(request.form.get('phosphorus', 0)),
            'potassium': float(request.form.get('potassium', 0)),
            'soil_ph': float(request.form.get('soil_ph', 0)),
            'altitude_m': float(request.form.get('altitude_m', 0)),
            'annual_rainfall_mm': float(request.form.get('annual_rainfall_mm', 0)),
            'avg_temperature_C': float(request.form.get('avg_temperature_C', 0)),
            'avg_humidity_pct': float(request.form.get('avg_humidity_pct', 0))
        }

        # Create DataFrame for model input
        input_df = pd.DataFrame([data])
        
        # Predict
        prediction = model.predict(input_df)[0]
        confidence = 1.0 # RandomForest prediction doesn't easily give confidence per sample without more work
        
        # Save recommendation history
        rec_history = RecommendationHistory(
            user_id=current_user.id,
            district=current_user.district or "Unknown",
            soil_ph=data['soil_ph'],
            rainfall=data['annual_rainfall_mm'],
            temperature=data['avg_temperature_C'],
            humidity=data['avg_humidity_pct'],
            farm_size=current_user.farm_size,
            recommended_crops=prediction,
            confidence_score=confidence
        )
        
        db.session.add(rec_history)
        db.session.commit()

        flash(f'Success! Based on your data, we recommend: {prediction.replace("_", " ").title()}', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Error in prediction: {e}")
        flash(f'Error processing recommendation: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    # Check if user is admin (you can implement proper role-based access)
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get statistics
    total_users = User.query.filter(User.email != 'admin@digitalagri.rw').count()
    total_recommendations = RecommendationHistory.query.count()
    
    # Get recent users (farmers only)
    recent_users = User.query.filter(User.email != 'admin@digitalagri.rw').order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent recommendations
    recent_recommendations = RecommendationHistory.query.order_by(RecommendationHistory.created_at.desc()).limit(5).all()
    
    # Get user distribution by district
    district_stats = db.session.query(User.district, db.func.count(User.id)).group_by(User.district).all()
    
    # Get top recommended crops
    top_crops = db.session.query(RecommendationHistory.recommended_crops, db.func.count(RecommendationHistory.id)).group_by(RecommendationHistory.recommended_crops).order_by(db.func.count(RecommendationHistory.id).desc()).limit(5).all()
    
    # Get average farm size
    avg_farm_size = db.session.query(db.func.avg(User.farm_size)).scalar() or 0
    
    return render_template('dashboard/admin.html', 
                         total_users=total_users,
                         total_recommendations=total_recommendations,
                         recent_users=recent_users,
                         recent_recommendations=recent_recommendations,
                         district_stats=district_stats,
                         top_crops=top_crops,
                         avg_farm_size=round(avg_farm_size, 2))

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.filter(User.email != 'admin@digitalagri.rw').order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/admin_users.html', users=users)

@app.route('/admin/recommendations')
@login_required
def admin_recommendations():
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    recommendations = RecommendationHistory.query.order_by(
        RecommendationHistory.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/admin_recommendations.html', recommendations=recommendations)

@app.route('/admin/crops')
@login_required
def admin_crops():
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    crops = CropData.query.all()
    return render_template('admin/crops.html', crops=crops)

@app.route('/admin/soil')
@login_required
def admin_soil():
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    soil_data = SoilData.query.all()
    return render_template('admin/soil.html', soil_data=soil_data)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.email == current_user.email:
        flash('You cannot delete your own admin account.', 'warning')
        return redirect(url_for('admin_users'))
    
    try:
        # Delete associated recommendation history first
        RecommendationHistory.query.filter_by(user_id=user.id).delete()
        
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} and their history have been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
        
    return redirect(url_for('admin_users'))

@app.route('/admin/recommendations/delete/<int:rec_id>', methods=['POST'])
@login_required
def delete_recommendation(rec_id):
    if current_user.email != 'admin@digitalagri.rw':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    rec = RecommendationHistory.query.get_or_404(rec_id)
    
    try:
        db.session.delete(rec)
        db.session.commit()
        flash('Recommendation log has been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting recommendation: {str(e)}', 'danger')
        
    return redirect(url_for('admin_recommendations'))

@app.route('/dashboard/recommendation/delete/<int:rec_id>', methods=['POST'])
@login_required
def delete_own_recommendation(rec_id):
    rec = RecommendationHistory.query.get_or_404(rec_id)
    
    # Ensure user can only delete their own records
    if rec.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(rec)
        db.session.commit()
        flash('Recommendation log deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting log: {str(e)}', 'danger')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
