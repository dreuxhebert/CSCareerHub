from flask import Flask, render_template, redirect, request, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename
import pandas as pd
import pdfplumber
import os
from dotenv import load_dotenv
from matcher_model import recommend_jobs
from models import grade_resume, process_docx
from flask_migrate import Migrate

load_dotenv()
secret_key = os.urandom(24)
app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
@app.before_request
def before_request():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        return redirect(request.url.replace("http://", "https://"), code=301)

uri = os.getenv('SQLALCHEMY_DATABASE_URI')  # Get the database URI from environment variables
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_pdf(file):
    extracted_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            extracted_data.append(text)

    rows = [{'type': 'text', 'label': line} for line in "\n".join(extracted_data).split('\n') if line.strip()]
    return pd.DataFrame(rows)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
oauth = OAuth(app)

oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'read:user user:email'},
)

oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    client_kwargs={'scope': 'openid email profile'},
)

class User(UserMixin, db.Model):
    __tablename__ = 'credentials'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def home():
    return redirect(url_for('login'))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        # If user exists, but it is an OAuth login (no password stored), skip password check
        if user and (not user.password or user.password == ""):
            login_user(user, remember=True)
            return redirect(url_for('index'))

        # Regular login: check password
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else:
            error = "Incorrect email or password. Please try again."
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/login/google')
def login_google():
    # Redirect to Google's authorization URL
    redirect_uri = url_for('authorize_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/login/github')
def login_github():
    redirect_uri = url_for('authorize_github', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    try:
        # Exchange the authorization code for an access token
        token = oauth.google.authorize_access_token()
        print("Access Token:", token)  # Log the entire token response

        # Fetch user information
        user_info = oauth.google.get('userinfo').json()
        print("User Info:", user_info)

        email = user_info.get('email')
        if not email:
            print("No email found in user info!")
            return "Failed to retrieve email. Check your OAuth scopes.", 400

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, password=None)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for('index'))

    except Exception as e:
        print("Error during authorization:", str(e))
        return f"Authorization failed: {str(e)}", 500

@app.route('/authorize/github')
def authorize_github():
    token = oauth.github.authorize_access_token()
    user_info = oauth.github.get('user').json()
    email = user_info.get('email') or user_info.get('login')

    if not email:
        flash("GitHub did not provide an email address. Please update your GitHub settings.")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, password=None)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('index'))   #

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error = "This email is already registered. Please log in or use a different email."
            return render_template('register.html', error=error)

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/resume_checker', methods=['GET', 'POST'])
def resume_checker():
    feedback = None

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
        file = request.files['file']


        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)


            try:
                if filename.endswith('.pdf'):
                    resume_df = process_pdf(file_path)
                elif filename.endswith('.docx'):
                    resume_df = process_docx(file_path)
                else:
                    flash('Unsupported file type')
                    return redirect(request.url)

                feedback = grade_resume(resume_df)

            except Exception as e:
                flash(f"Error processing file: {e}")
                return redirect(request.url)

    return render_template('resume_checker.html', feedback=feedback)

@app.route('/job_qualifications')
def job_qualifications():
    return render_template('job_qualifications.html')

@app.route('/school_work')
def school_work():
    return render_template('school_work.html')

@app.route('/about_me')
def about_me():
    return render_template('about_me.html')

@app.route('/machine_learning')
def machine_learning():
    return render_template('machine_learning.html')

@app.route('/webapp')
def webapp():
    return render_template('webapp.html')

@app.route('/java')
def java():
    return render_template('java.html')

@app.route('/python')
def python():
    return render_template('python.html')

@app.route('/js_ts')
def js_ts():
    return render_template('js_ts.html')

@app.route('/sql')
def sql():
    return render_template('sql.html')

@app.route('/privacy-policy')
def privacy_policy():
    return "Privacy Policy Placeholder"

@app.route('/terms-of-service')
def terms_of_service():
    return "Terms of Service Placeholder"

@app.route('/job_matcher', methods=['GET', 'POST'])
def job_matcher():
    recommendations = None

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                # Process file
                if filename.endswith('.pdf'):
                    resume_df = process_pdf(file_path)
                elif filename.endswith('.docx'):
                    resume_df = process_docx(file_path)
                else:
                    flash('Unsupported file format')
                    return redirect(request.url)

                # Debug log for DataFrame
                app.logger.debug("Processed Resume DataFrame: %s", resume_df)

                # Generate recommendations
                recommendations = recommend_jobs(resume_df)
                app.logger.debug("Job Recommendations: %s", recommendations)

                # Ensure recommendations is a list
                if not recommendations:
                    recommendations = []

            except Exception as e:
                flash(f"Error processing file: {e}")
                return redirect(request.url)

    return render_template('job_matcher.html', recommendations=recommendations)



if __name__ == '__main__':
    app.run(debug=True)


def config():
    return None