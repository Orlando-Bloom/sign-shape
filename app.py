from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = './static/uploads'
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
        file = request.files['media']

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_path = f"static/uploads/{filename}"
        else:
            media_path = None

        new_post = Post(title=title, content=content, media=media_path)
        db.session.add(new_post)
        db.session.commit()
        flash("Post created successfully!")
        return redirect(url_for('index'))

    return render_template('post.html')

if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Create the database tables within the app context
    with app.app_context():
        db.create_all()
    
    # Run the application
    app.run(debug=True)


