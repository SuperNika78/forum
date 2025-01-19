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

@app.route('/edit_thread/<int:thread_id>', methods=['GET', 'POST'])
def edit_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)

    if 'user_id' not in session or session['user_id'] != thread.user_id:
        flash('You do not have permission to edit this thread')
        return redirect(url_for('thread', id=thread_id))

    if request.method == 'POST':
        thread.title = request.form['title']
        thread.content = request.form['content']
        db.session.commit()
        flash('Thread updated successfully!')
        return redirect(url_for('thread', id=thread_id))

    return render_template('edit_thread.html', thread=thread)

@app.route('/delete_thread/<int:thread_id>', methods=['POST'])
def delete_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)

    if 'user_id' not in session or session['user_id'] != thread.user_id:
        flash('You do not have permission to delete this thread')
        return redirect(url_for('thread', id=thread_id))

    # Delete all comments first
    Comment.query.filter_by(thread_id=thread_id).delete()
    db.session.delete(thread)
    db.session.commit()
    flash('Thread deleted successfully!')
    return redirect(url_for('index'))


@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if 'user_id' not in session or session['user_id'] != comment.user_id:
        flash('You do not have permission to edit this comment')
        return redirect(url_for('thread', id=comment.thread_id))

    if request.method == 'POST':
        comment.content = request.form['content']
        db.session.commit()
        flash('Comment updated successfully!')
        return redirect(url_for('thread', id=comment.thread_id))

    return render_template('edit_comment.html', comment=comment)


@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if 'user_id' not in session or session['user_id'] != comment.user_id:
        flash('You do not have permission to delete this comment')
        return redirect(url_for('thread', id=comment.thread_id))

    thread_id = comment.thread_id
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!')
    return redirect(url_for('thread', id=thread_id))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = User.query.get_or_404(session['user_id'])
    if 'user_id' not in session or session['user_id'] != user.id:
        flash('You do not have permission to access this profile')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            user.username = username
            db.session.commit()
            flash("Profile updated successfully!")

    return render_template("profile.html", user=user)

@app.route('/new_profile_pic', methods=['GET','POST'])
def new_profile_pic():
    user = User.query.get_or_404(session['user_id'])
    if 'user_id' not in session or session['user_id'] != user.id:
        flash('You do not have permission to edit this profile')
        return redirect(url_for('index'))

    user.profile_pic_url=random_picture()
    db.session.commit()

    flash("Profile Picture Updated")
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    user = User.query.get_or_404(session['user_id'])
    if 'user_id' not in session or session['user_id'] != user.id:
        flash('You do not have permission to change your password')
        return redirect(url_for('index'))

    if request.method == 'POST':
        current_password = request.form['currentpassword']
        new_password = request.form['newpassword']

        if user and bcrypt.check_password_hash(user.password_hash, current_password):
            user.password_hash = bcrypt.generate_password_hash(new_password)
            db.session.commit()
            flash("Your password has been changed")
        else:
            flash("Your current password is incorrect")
        return redirect(url_for('profile'))

    return render_template('change_password.html', user=user)