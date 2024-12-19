from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import hashlib
import os

# App configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit uploads to 10MB

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
    # Query to fetch approved posts
    posts = Post.query.filter(Post.status == 'approved').order_by(
        db.case((Post.username == 'Admin', 0), else_=1), Post.id.desc()
    ).all()

    # Debugging: Log the retrieved posts
    print("DEBUG: Approved posts retrieved for index.html:")
    for post in posts:
        print(f"ID: {post.id}, Content: {post.content}, Status: {post.status}")

    return render_template('index.html', posts=posts)



@app.route('/review', methods=['GET', 'POST'])
def review_posts():
    admin_password = "Iamtooc00l!"  # Secure admin password
    if request.args.get('password') != admin_password:
        return "Unauthorized access", 401

    if request.method == 'POST':
        post_id = request.form.get('post_id')
        action = request.form.get('action')  # 'approve' or 'reject'

        try:
            post = Post.query.get(post_id)
            if post:
                if action == 'approve':
                    post.status = 'approved'  # Update the status to "approved"
                    db.session.commit()  # Commit the change to the database
                    print(f"DEBUG: Post {post_id} approved successfully. Status: {post.status}")  # Debugging
                    flash("Post approved successfully!")

                elif action == 'reject':
                    db.session.delete(post)  # Delete the post if rejected
                    db.session.commit()  # Commit the deletion
                    print(f"DEBUG: Post {post_id} rejected and removed.")  # Debugging
                    flash("Post rejected and removed!")
            else:
                print(f"DEBUG: Post with ID {post_id} not found.")  # Debugging
                flash("Post not found!")
                

        except Exception as e:
            print(f"ERROR: An error occurred while processing post {post_id}: {e}")  # Debugging
            flash("An error occurred while processing the post.")

        return redirect(url_for('admin', password=admin_password))

    # Fetch pending posts
    pending_posts = Post.query.filter_by(status='pending').all()
    print(f"DEBUG: {len(pending_posts)} pending posts loaded for review.")  # Debugging
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
            media_path = f"static/uploads/{filename}"
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
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        media_path = f"static/uploads/{filename}"
    else:
        media_path = None

    new_post = Post(content=content, username=username, media=media_path, ip_address=hashed_ip, status='approved')
    db.session.add(new_post)
    db.session.commit()
    flash("Post created and published successfully!")
    return redirect(url_for('admin', password=request.args.get('password')))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
