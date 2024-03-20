# Author: Nachiket Galande
# Date: 17/03/2024
# Description: This Python script implements a Flask template for user authentication using MongoDB and Flask-Login.

# Import necessary modules
from bson import ObjectId
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from User.models import User
import os
from werkzeug.utils import secure_filename
from config import SECRET_KEY
from werkzeug.utils import secure_filename
from utils import allowed_file
from database import db
from User.user_routes import user_blueprint
from Posts.post_routes import post_blueprint
from notifications import create_notification

# Initialize Flask app
app = Flask("__main__")

# Set secret key for session management
app.secret_key = SECRET_KEY

app.register_blueprint(user_blueprint)
app.register_blueprint(post_blueprint)


# Initialize Flask-Login for user authentication
login_manager = LoginManager(app)

UPLOAD_FOLDER = 'static/user/profileImages'
    
# Callback function to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(user_id):
    # Retrieve user data from MongoDB based on user_id
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        # Create a User object with the retrieved username and user_id
        user = User(user_id=user_id, email=user_data['email'], username=user_data['username'], profile_image=user_data.get('profile_image'), following=user_data.get('following'), followers=user_data.get('followers'))
        return user
    else:
        return None

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@app.context_processor
def notification_count():
    if current_user.is_authenticated:
        unread_notification_count = db.notifications.count_documents({'recipient_user_id': current_user.id})
    else:
        unread_notification_count = 0
    return {'notification_count': unread_notification_count}

# Route for the home page
@app.route('/')
def home():
    query = request.args.get('query')
    if query:
        # If a search query is provided, perform the search
        search_results = db.posts.find({'caption': {'$regex': f'.*{query}.*', '$options': 'i'}})
        return render_template('home.html', posts=search_results, query=query)
    else:
        # If no search query is provided, simply fetch all posts
        posts = db.posts.find().sort('creation_date', -1)
        formatted_posts = []
        for post in posts:
            # Fetch the user's profile image
            user_id = post.get('user_id')
            if user_id:
                user_data = db.users.find_one({'_id': ObjectId(user_id)})
                if user_data:
                    post_profile_image = user_data.get('profile_image')
                    post['post_profile_image'] = post_profile_image
            formatted_posts.append(post)
        return render_template('home.html', posts=formatted_posts)

# Route for the account page, accessible only to logged-in users
@app.route('/account')
@login_required
def account():
    # Ensure that current_user contains the profile_image attribute
    if hasattr(current_user, 'profile_image'):
        profile_image = current_user.profile_image
    else:
        profile_image = None

    posts = db.posts.find({'user_id': current_user.id}).sort('creation_date', -1)
    posts = list(posts)
    post_count = len(posts)
    formatted_posts = []
    for post in posts:
            # Fetch the user's profile image
            user_id = post.get('user_id')
            if user_id:
                user_data = db.users.find_one({'_id': ObjectId(user_id)})
                if user_data:
                    post_profile_image = user_data.get('profile_image')
                    post['post_profile_image'] = post_profile_image
            formatted_posts.append(post)

    user_data = db.users.find_one({'_id': ObjectId(current_user.id)})
    followers_count = len(user_data.get('followers', []))
    following_count = len(user_data.get('following', []))

    return render_template('account.html', profile_image=profile_image, posts=posts, post_count=post_count, followers_count=followers_count, following_count=following_count)

@app.route('/upload_profile_image', methods=['POST'])
@login_required
def upload_profile_image():
    if request.method == 'POST':
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            if profile_image.filename == '' or not allowed_file(profile_image.filename):
                return redirect(request.url)
            filename = f"{current_user.id}_{secure_filename(profile_image.filename)}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            profile_image.save(filepath)
            filepath = filepath.replace('\\', '/')
            current_user.profile_image = filepath
            db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': {'profile_image': filepath}})
            print(current_user.profile_image)
    return redirect(url_for('account'))

@app.route('/search')
def search():
    query = request.args.get('query')
    search_results = db.posts.find({'caption': {'$regex': f'.*{query}.*', '$options': 'i'}})
    return render_template('home.html', posts=search_results)

@app.route('/search_users')
def search_users():
    query = request.args.get('user_search_query')

    post_results = db.posts.find({'caption': {'$regex': f'.*{query}.*', '$options': 'i'}})
    user_results = db.users.find({
        '$or': [
            {'username': {'$regex': f'.*{query}.*', '$options': 'i'}},
            {'email': {'$regex': f'.*{query}.*', '$options': 'i'}}
        ]
    })

    following_list = []
    if current_user.is_authenticated:
        following_list = current_user.following
    return render_template('search_results.html', post_results=post_results, user_results=user_results, query=query, following_list=following_list)

@app.route('/profile/<user_id>')
def profile(user_id):
    # Fetch user data based on user_id
    user_data = db.users.find_one({'_id': ObjectId(user_id)})
    posts = db.posts.find({'user_id': user_id})
    posts = list(posts)
    post_count = len(posts)
    followers_count = len(user_data.get('followers', []))
    following_count = len(user_data.get('following', []))
    
    following_list = []
    if current_user.is_authenticated:
        following_list = current_user.following
    return render_template('profile.html', user=user_data, posts=posts, post_count=post_count, followers_count=followers_count, following_count=following_count, following_list=following_list)


# Route for following a user
@app.route('/follow/<recipient_user_id>', methods=['POST'])
@login_required
def follow_user(recipient_user_id):
    recipient_user = db.users.find_one({'_id': ObjectId(recipient_user_id)})    
    # Check if the current user is already following the recipient
    if current_user.id in recipient_user.get('followers', []):
        return jsonify({'error': 'Already following'}), 400
    
    # Update recipient's follower list and current user's following list
    db.users.update_one({'_id': ObjectId(recipient_user_id)}, {'$push': {'followers': current_user.id}})
    db.users.update_one({'_id': ObjectId(current_user.id)}, {'$push': {'following': recipient_user_id}})

    notification_message = f"{current_user.username} started following you."
    create_notification(recipient_user_id, current_user.id, notification_message)
    
    return redirect(url_for('profile', user_id=recipient_user_id))

# Route for unfollowing a user
@app.route('/unfollow/<recipient_user_id>', methods=['POST'])
@login_required
def unfollow_user(recipient_user_id):
    # Check if recipient_user_id is valid and exists
    recipient_user = db.users.find_one({'_id': ObjectId(recipient_user_id)})
    if not recipient_user:
        return jsonify({'error': 'Recipient user not found'}), 404
    
    # Check if the current user is following the recipient
    if current_user.id not in recipient_user['followers']:
        return jsonify({'error': 'Not following'}), 400
    
    # Update recipient's follower list and current user's following list
    db.users.update_one({'_id': ObjectId(recipient_user_id)}, {'$pull': {'followers': current_user.id}})
    db.users.update_one({'_id': ObjectId(current_user.id)}, {'$pull': {'following': recipient_user_id}})
    
    return redirect(url_for('profile', user_id=recipient_user_id))

@app.route('/notifications')
@login_required
def notifications():
    # Query notifications for the current user
    notifications = db.notifications.find({'recipient_user_id': current_user.id}).sort('timestamp', -1)
    notifications = list(notifications)
    for notification in notifications:
        sender_user_id = notification["sender_user_id"]
        sender_profile_image = db.users.find_one({"_id": ObjectId(sender_user_id)}, {"profile_image": 1})
        # Check if profile_image key exists
        if sender_profile_image:
            notification['profile_image'] = sender_profile_image.get('profile_image')
        else:
            notification['profile_image'] = None
        
    return render_template('notifications.html', notifications=notifications)

# Run the Flask app
if __name__=="__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0')