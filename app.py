from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from image_search import ImageSearchEngine
from database import db
from pathlib import Path
from functools import wraps
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}
app.secret_key = os.getenv('SECRET_KEY', 'searchimage')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')

# Initialize utilities
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)
search_engine = ImageSearchEngine()
serializer = URLSafeTimedSerializer(app.secret_key)

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.get_user_by_id(session['user_id'])
        if not user or not user.get('is_admin', False):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def send_reset_email(email, token):
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = "Password Reset Request"
        
        body = f"""To reset your password, visit the following link:
        {url_for('reset_password', token=token, _external=True)}
        
        If you did not make this request, please ignore this email.
        This link will expire in 1 hour.
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, message = db.register_user(username, email, password)
        
        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, result = db.login_user(email, password)
        
        if success:
            session['user_id'] = str(result['_id'])
            session['username'] = result['username']
            session['is_admin'] = result.get('is_admin', False)
            
            if session['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash(result, 'error')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = db.get_user_by_email(email)
        
        if user:
            token = serializer.dumps(email, salt='password-reset-salt')
            if send_reset_email(email, token):
                flash('Password reset instructions sent to your email.', 'success')
            else:
                flash('Error sending reset email. Please try again.', 'error')
        else:
            flash('Password reset instructions sent if email exists.', 'info')
            
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            if db.reset_password(email, password):
                flash('Your password has been updated.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Error resetting password.', 'error')
    
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = db.get_all_users()
    return render_template('admin/dashboard.html', users=users)

@app.route('/admin/toggle_user/<user_id>')
@admin_required
def toggle_user(user_id):
    success, message = db.toggle_user_status(user_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<user_id>')
@admin_required
def delete_user(user_id):
    success, message = db.delete_user(user_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/make_admin/<user_id>')
@admin_required
def make_admin(user_id):
    success, message = db.make_admin(user_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/revoke_admin/<user_id>')
@admin_required
def revoke_admin(user_id):
    success, message = db.revoke_admin(user_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin_dashboard'))

# File serving routes
@app.route('/static/processed/train/<path:filename>')
def serve_train_data(filename):
    return send_from_directory('static/processed/train', filename)

@app.route('/static/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Search route
@app.route('/search', methods=['POST'])
@login_required
def search():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            results = search_engine.search(filepath, top_k=5)

            if not results:
                return jsonify({'error': 'No similar images found'}), 404

            formatted_results = []
            for result in results:
                image_path = Path(result['path'])
                animal_info = db.get_animal_info(result['class'])
                
                formatted_result = {
                    'class': result['class'],
                    'filename': image_path.name,
                    'similarity': f"{result['similarity']:.2f}",
                    'info': {
                        'description': 'No information available',
                        'scientific_name': 'Not available',
                        'habitat': 'Not available',
                        'diet': 'Not available',
                        'lifespan': 'Not available'
                    }
                }
                
                if animal_info:
                    formatted_result['info'] = {
                        'description': animal_info.get('description', 'No description available'),
                        'scientific_name': animal_info.get('scientific_name', 'Not available'),
                        'habitat': animal_info.get('habitat', 'Not available'),
                        'diet': animal_info.get('diet', 'Not available'),
                        'lifespan': animal_info.get('lifespan', 'Not available')
                    }
                
                formatted_results.append(formatted_result)

            search_data = {
                'query_image': f"/static/uploads/{filename}",
                'results': formatted_results
            }
            db.update_search_history(session['user_id'], search_data)

            return jsonify(search_data)

        except Exception as e:
            return jsonify({'error': f'Search failed: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file type'}), 400

# Profile routes
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                db.update_avatar(session['user_id'], filename)
                flash('Avatar updated successfully', 'success')
                return redirect(url_for('profile'))
            
        if 'current_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
            else:
                success, message = db.change_password(session['user_id'], current_password, new_password)
                if success:
                    flash('Password changed successfully', 'success')
                else:
                    flash(message, 'error')
    
    return render_template('profile.html', user=user)

# Template context processors
@app.context_processor
def utility_processor():
    def is_admin():
        if 'is_admin' in session:
            return session['is_admin']
        return False
    return dict(is_admin=is_admin)
@app.route('/posts')
@login_required
def posts():
    all_posts = db.get_all_posts()
    return render_template('posts.html', posts=all_posts)

@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image uploaded', 'error')
            return redirect(url_for('create_post'))
        
        file = request.files['image']
        caption = request.form.get('caption', '')
        
        if file.filename == '':
            flash('No image selected', 'error')
            return redirect(url_for('create_post'))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            
            success, message = db.create_post(session['user_id'], filename, caption)
            if success:
                flash('Post created successfully!', 'success')
                return redirect(url_for('posts'))
            else:
                flash(message, 'error')
                
    return render_template('create_post.html')

@app.route('/delete-post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    success, message = db.delete_post(post_id, session['user_id'])
    return jsonify({'success': success, 'message': message})
if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=True)