from flask import Flask, request, render_template, redirect, session, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import DateTime
from secretkey import secret_key
from functools import wraps
import bcrypt

app = Flask(__name__)
app.secret_key = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_date = db.Column(DateTime, default=datetime.now)
    published_date = db.Column(DateTime, nullable=True)

    def publish(self):
        self.published_date = datetime.now()
        db.session.commit()

    def __repr__(self):
        return f'<Blog {self.title}>'


with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'email' not in session:
            flash('Please log in to access that page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('blog'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'email' in session:
        return redirect(url_for('blog'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
            return render_template('register.html')

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('blog'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['name'] = user.name
            session['email'] = user.email
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('blog'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/blog')
def blog():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('Blogs.html', blogs=blogs)


@app.route('/blog/<int:blog_id>')
def view_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('view_blog.html', blog=blog)


@app.route('/create_blog', methods=['GET', 'POST'])
@login_required
def create_blog():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        text = request.form.get('text', '').strip()

        if not title or not text:
            flash('Title and content are required.', 'error')
            return render_template('create_blog.html')

        new_blog = Blog(
            author=session['name'],
            author_email=session['email'],
            title=title,
            text=text
        )
        db.session.add(new_blog)
        db.session.commit()
        flash('Blog post created!', 'success')
        return redirect(url_for('blog'))

    return render_template('create_blog.html')


@app.route('/blog/<int:blog_id>/delete', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if blog.author_email != session['email']:
        abort(403)
    db.session.delete(blog)
    db.session.commit()
    flash('Blog post deleted.', 'success')
    return redirect(url_for('blog'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_users = User.query.count()
    total_posts = Blog.query.count()
    my_posts = Blog.query.filter_by(author_email=session['email']).order_by(Blog.created_date.desc()).all()
    recent_posts = Blog.query.order_by(Blog.created_date.desc()).limit(5).all()
    return render_template('dashboard.html',
                           total_users=total_users,
                           total_posts=total_posts,
                           my_posts=my_posts,
                           recent_posts=recent_posts)


if __name__ == '__main__':
    app.run(debug=True)
