from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import hashlib
import os

# App configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = '/var/data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit uploads to 10MB

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    admin_password = "Iamtooc00l!"  # Secure admin password
    if request.args.get('password') != admin_password:
        return "Unauthorized access", 401

    if request.method == 'POST':
        post_id = request.form.get('post_id')
        action = request.form.get('action')  # 'approve' or 'reject'
        post = Post.query.get(post_id)

        if post:
            if action == 'approve':
                post.status = 'approved'  # Update the status to "approved"
                db.session.commit()      # Commit the change to the database
                flash("Post approved successfully!")
            elif action == 'reject':
                db.session.delete(post)  # Delete the post if rejected
                db.session.commit()      # Commit the deletion
                flash("Post rejected and removed!")
        return redirect(url_for('admin', password=admin_password))

    pending_posts = Post.query.filter_by(status='pending').all()
    return render_template('review.html', posts=pending_posts)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        user_ip = request.remote_addr
        hashed_ip = hashlib.sha256(user_ip.encode()).hexdigest()  # Hash the IP

        content = request.form['content']
        username = request.form.get('username', 'Anonymous')
        file = request.files.get('media')

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_path = f"uploads/{filename}"  # Store relative path only
        else:
            media_path = None

        new_post = Post(content=content, username=username, media=media_path, ip_address=hashed_ip)
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
    admin_password = "Iamtooc00l!"  # Secure admin password
    if request.args.get('password') != admin_password:
        return "Unauthorized access", 401

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
        return redirect(url_for('admin', password=admin_password))

    return render_template('admin.html', posts=posts)

@app.route('/admin/new', methods=['POST'])
def admin_new_post():
    user_ip = request.remote_addr
    hashed_ip = hashlib.sha256(user_ip.encode()).hexdigest()  # Hash the IP

    content = request.form['content']
    username = request.form.get('username', 'Admin')
    file = request.files.get('media')

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        media_path = file_path
    else:
        media_path = None

    new_post = Post(content=content, username=username, media=media_path, ip_address=hashed_ip, status='approved')
    db.session.add(new_post)
    db.session.commit()
    flash("Post created and published successfully!")
    return redirect(url_for('admin', password=request.args.get('password')))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Serve files from the /var/data/uploads directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
