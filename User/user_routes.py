import bcrypt
from bson import ObjectId
from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from User.models import User
from database import db

user_blueprint = Blueprint('user', __name__)

# Route for user login
@user_blueprint.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user exists in the database
        user_data = db.users.find_one({'username': username})
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            # If the user exists and the password is correct, log in the user
            user = User(user_id=str(user_data['_id']), username=user_data['username'])
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    else:
        return render_template('login.html')
    
# Route for user signup
@user_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Check if the user already exists in the database
        existing_user = db.users.find_one({'email': email})
        if existing_user:
            flash('User already exists', 'error')
            return render_template('signup.html')
        
        # Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        password = hashed_password.decode('utf-8')

        # Create a new user model object
        new_user = User(user_id=None, email=email, username=username, password=password)  # Ensure correct parameter order

        # Insert user data into MongoDB
        db.users.insert_one({
            'email': new_user.email,
            'username': new_user.username,
            'password': new_user.password,
            'following': [],
            'followers': []
        })

        # Since User model doesn't provide an ID, you might need to retrieve it from MongoDB
        user = db.users.find_one({'email': new_user.email})  # Query by email

        # Create a new user object using the retrieved user ID
        user_obj = User(user_id=user['_id'], email=user['email'], username=user['username'], password=user['password'])

        login_user(user_obj)

        # Redirect to home page
        return redirect(url_for('home'))
    else:
        return render_template("signup.html")
    
# Route for user logout
@user_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@user_blueprint.route('/reset_password', methods=['POST'])
def reset_password():
    if request.method == 'POST':
        current_pwd = request.form['current_pwd']
        new_pwd = request.form['new_pwd']
        user_data = db.users.find_one({'_id': ObjectId(current_user.id)})
        
        if user_data and bcrypt.checkpw(current_pwd.encode('utf-8'), user_data['password'].encode('utf-8')):
            hashed_password = bcrypt.hashpw(new_pwd.encode('utf-8'), bcrypt.gensalt())
            new_pwd = hashed_password.decode('utf-8')
            db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'password': new_pwd}})
            return redirect(url_for('home'))
    return redirect(url_for('account'))
