from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import hashlib
import os
import boto3
from botocore.config import Config

print("AWS KEY:", os.environ.get("AWS_ACCESS_KEY_ID"))
print("BUCKET:", os.environ.get("AWS_S3_BUCKET"))

# App configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit uploads to 10MB

# Admin credentials
ADMIN_USERNAME = "orlandobloom"
ADMIN_PASSWORD = "sign-shape-xxx!"

# S3 Configuration
S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
S3_ENDPOINT = os.environ.get("AWS_S3_ENDPOINT_URL")

if not all([S3_BUCKET, S3_ENDPOINT]):
    raise ValueError("Missing S3 configuration in environment variables.")

s3 = boto3.client(
    "s3",
    region_name=os.environ.get("AWS_S3_REGION"),
    endpoint_url=os.environ.get("AWS_S3_ENDPOINT_URL"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    config=Config(s3={'addressing_style': 'path'})
)



# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    media = db.Column(db.String(300), nullable=True)
    username = db.Column(db.String(50), nullable=False, default="Anonymous")
    status = db.Column(db.String(20), nullable=False, default="pending")
    ip_address = db.Column(db.String(64), nullable=True)

# Routes
@app.route('/')
def index():
    posts = Post.query.filter(Post.status == 'approved').order_by(
        db.case((Post.username == 'Admin', 0), else_=1), Post.id.desc()
    ).all()
    return render_template('index.html', posts=posts)

@app.route('/review', methods=['GET', 'POST'])
def review_posts():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        post_id = request.form.get('post_id')
        action = request.form.get('action')
        post = Post.query.get(post_id)

        if post:
            if action == 'approve':
                post.status = 'approved'
                db.session.commit()
                flash("Post approved successfully!")
            elif action == 'reject':
                db.session.delete(post)
                db.session.commit()
                flash("Post rejected and removed!")
        return redirect(url_for('admin'))

    pending_posts = Post.query.filter_by(status='pending').all()
    return render_template('review.html', posts=pending_posts)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        user_ip = request.remote_addr
        hashed_ip = hashlib.sha256(user_ip.encode()).hexdigest()

        content = request.form.get('content', '')
        file = request.files.get('media')

        if not file or file.filename.strip() == '':
            flash("An image file is required to submit a post.")
            return redirect(url_for('new_post'))

        filename = secure_filename(file.filename)
        s3.upload_fileobj(file, S3_BUCKET, filename)
        media_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{filename}"

        new_post = Post(content=content, username="Anonymous", media=media_url, ip_address=hashed_ip, status="pending")
        db.session.add(new_post)
        db.session.commit()

        flash("Post created successfully! Pending review.")
        return redirect(url_for('pending'))

    return render_template('post.html')

@app.route('/pending')
def pending():
    return render_template('pending.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    posts = Post.query.order_by(Post.id.desc()).all()
    if request.method == 'POST':
        post_id = request.form.get('post_id')
        post_to_delete = Post.query.get(post_id)
        if post_to_delete:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash("Post deleted successfully!")
        else:
            flash("Post not found!")
        return redirect(url_for('admin'))

    return render_template('admin.html', posts=posts)

@app.route('/admin/new', methods=['POST'])
def admin_new_post():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    user_ip = request.remote_addr
    hashed_ip = hashlib.sha256(user_ip.encode()).hexdigest()

    content = request.form.get('content', '')
    file = request.files.get('media')

    if not file or file.filename.strip() == '':
        flash("An image file is required to submit a post.")
        return redirect(url_for('admin'))

    filename = secure_filename(file.filename)
    s3.upload_fileobj(file, S3_BUCKET, filename)
    media_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{filename}"

    new_post = Post(content=content, username="Admin", media=media_url, ip_address=hashed_ip, status='approved')
    db.session.add(new_post)
    db.session.commit()

    flash("Post created and published successfully!")
    return redirect(url_for('admin'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            flash("Login successful!")
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials. Please try again.")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("You have been logged out.")
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
