from flask import Flask,request,render_template,redirect,session,jsonify,url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import DateTime
from secretkey import secret_key

import bcrypt


app = Flask(__name__)
app.secret_key = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

#User model
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
    title = db.Column(db.String(100), nullable=False)
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



@app.route('/')
def index():
    return 'Welcome to our blog Webpage'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        new_user = User(name=name, email=email, password=password)  
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['name'] = user.name
            session['email'] = user.email

            return redirect('/blog')
        else:
            return render_template('login.html', error='Invalid User')
    
    return render_template('login.html')



@app.route('/create_blog', methods=['GET', 'POST'])
def create_blog():
    if request.method == 'POST':
        
        author = request.form['author']
        title = request.form['title']
        text = request.form['text']
        
        
        new_blog = Blog(author=author, title=title, text=text)
        
        
        db.session.add(new_blog)
        db.session.commit()
        
        
        return redirect(url_for('blog'))
    else:
        
        return render_template('create_blog.html')
   
    
@app.route('/blog')
def blog():
    blogs = Blog.query.order_by(Blog.created_date.desc()).all()
    return render_template('Blogs.html', blogs=blogs)


    
   
if __name__ == '__main__':
    app.run(debug=True)
