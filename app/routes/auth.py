# app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, UserRole, Constituency

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles secure onboarding and role assignment for citizens."""
    if current_user.is_authenticated:
        return redirect(url_for('core.national_dashboard'))
        
    constituencies = Constituency.query.order_by(Constituency.name).all()
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        constituency_id = request.form.get('constituency_id')
        
        # Validation checks
        if not full_name or not email or not password:
            flash('All structural identity fields are required.', 'danger')
            return render_template('register.html', constituencies=constituencies)
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This email address is already registered on KwachaTrack.', 'warning')
            return render_template('register.html', constituencies=constituencies)
            
        # Create user instance (Defaults strictly to Citizen role)
        new_user = User(
            full_name=full_name,
            email=email,
            role=UserRole.CITIZEN,
            constituency_id=int(constituency_id) if constituency_id else None
        )
        new_user.set_password(password) # Triggers secure Werkzeug Bcrypt hashing
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash('An error occurred during secure registration. Please try again.', 'danger')
            
    return render_template('register.html', constituencies=constituencies)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles secure session generation and role-based portal routing."""
    if current_user.is_authenticated:
        return redirect(url_for('core.national_dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        # Verify user existence and cryptographically check password hash
        if not user or not user.check_password(password):
            flash('Invalid credential tracking vectors. Check email and password.', 'danger')
            return render_template('login.html')
            
        login_user(user, remember=remember)
        
        # Contextual UI/UX Redirection based on Administrative clearances
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        elif user.role in [UserRole.CONSTITUENCY_ADMIN, UserRole.NATIONAL_ADMIN]:
            flash(f'Welcome back, Admin {user.full_name}. Oversight console initialized.', 'info')
            return redirect(url_for('core.national_dashboard')) # Or custom admin route
        else:
            flash(f'Welcome back to KwachaTrack, {user.full_name}!', 'success')
            return redirect(url_for('core.national_dashboard'))
            
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Terminates active cookie sessions cleanly."""
    logout_user()
    flash('You have been logged out of the tracking console safely.', 'success')
    return redirect(url_for('core.national_dashboard'))