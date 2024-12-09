from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Limit uploads to 10MB

db = SQLAlchemy(app)

# Database Model
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media = db.Column(db.String(300), nullable=True)

# Routes
@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        # Handle file upload safely
        file = request.files.get('media')  # Use `.get()` to avoid KeyError
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_path = f"static/uploads/{filename}"
        else:
            media_path = None

        # Create and save the new post
        new_post = Post(title=title, content=content, media=media_path)
        db.session.add(new_post)
        db.session.commit()

        flash("Post created successfully!")
        return redirect(url_for('index'))

    return render_template('post.html')


# New Admin Route for Managing Posts
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    admin_password = "your_admin_password"  # Change this to a secure password

    # Basic password protection
    if request.args.get('password') != admin_password:
        return "Unauthorized access", 401

    # Fetch all posts for display on the admin page
    posts = Post.query.order_by(Post.id.desc()).all()

    # Handle deletion if a post ID is provided
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

    return render_template('admin.html', posts=posts)  # New admin.html template required


if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create the database tables within the app context
    with app.app_context():
        db.create_all()
    
    # Run the application
    app.run(debug=True)
