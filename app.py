import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
import random

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
bcrypt = Bcrypt(app)
# Flask Condif
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://UAS_hallweight:1ce149cad7c154f0af552127805bf64c9acdf045@s4x97.h.filess.io:3306/UAS_hallweight"
app.config['SECRET_KEY'] = 'belajardoangbang'

db.init_app(app)

# Waifu Profile Pic
BASE_URL = "https://api.waifu.pics"
category = [
    'waifu',
    'neko',
    'shinobu',
    'megumin',
    'bully',
    'cuddle',
    'cry',
    'hug',
    'awoo',
    'kiss',
    'lick',
    'pat',
    'smug',
    'bonk',
    'yeet',
    'blush',
    'smile',
    'wave',
    'highfive',
    'handhold',
    'nom',
    'bite',
    'glomp',
    'slap',
    'kill',
    'kick',
    'happy',
    'wink',
    'poke',
    'dance',
    'cringe']

def random_picture():
    choice = random.choice(category)
    response = requests.get(f"{BASE_URL}/sfw/{choice}")
    API_Data = response.json()
    return API_Data["url"]


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_pic_url = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    threads = db.relationship('Thread', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='thread', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)

with app.app_context():
    db.create_all()

# Routing
@app.route("/", methods=["GET", "POST"])
def index():
    if 'user_id' not in session:
        flash('Please login to create a thread')
        return redirect(url_for('login'))

    if request.method == "POST":
        thread = Thread(
            title=request.form['title'],
            content=request.form['content'],
            user_id=session['user_id']
        )
        db.session.add(thread)
        db.session.commit()
        flash('Thread created successfully!')

    threads = db.session.execute(db.select(Thread)).scalars()
    return render_template("index.html", threads=threads)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=bcrypt.generate_password_hash(password),
            profile_pic_url=random_picture()
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('index'))

        flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!')
    return redirect(url_for('index'))

@app.route("/thread/<int:id>", methods=["GET", "POST"])
def thread(id):
    if request.method == "POST":
        if 'user_id' not in session:
            flash('Please login to comment')
            return redirect(url_for('login'))

        comment = Comment(
            thread_id=id,
            content=request.form['content'],
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!')
    thread = db.get_or_404(Thread, id)
    comments = Comment.query.filter_by(thread_id=id).all()
    return render_template("thread.html", thread=thread, comments=comments)

