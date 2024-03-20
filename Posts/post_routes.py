from bson import ObjectId
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from utils import allowed_file, save_image
from notifications import create_notification
from datetime import datetime, timedelta

post_blueprint = Blueprint('post', __name__)

# Route for adding a post
@post_blueprint.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        image = request.files['image']
        caption = request.form['caption']
        user_id = request.form['user_id']
        username = request.form['username']

        utc_time = datetime.utcnow()
        ist_time = utc_time + timedelta(hours=5, minutes=30)

        if image.filename == '':
            return redirect(request.url)

        if image and allowed_file(image.filename):
            image_filename = save_image(image)

            # Insert post data into MongoDB
            db.posts.insert_one({
                'image_filename': image_filename,
                'caption': caption,
                'user_id': user_id,
                'username': username,
                'creation_date': ist_time
            })

            # Create a notification for each follower
            for follower in current_user.followers:
                print(follower)
                create_notification(follower, current_user.id, f"{current_user.username} added a new post.")
            return redirect(url_for('home'))
        else:
            return redirect(request.url)
    else:
        return render_template('addpost.html')
    
# Post details page
@post_blueprint.route('/post_details/<post_id>')
def post_details(post_id):
    # Fetch post data from MongoDB based on post_id
    post = db.posts.find_one({'_id': ObjectId(post_id)})
    if post:
        # Fetch comments associated with the post
        comments = db.comments.find({'post_id': ObjectId(post_id)})
        post_profile_image = db.users.find_one({'_id': ObjectId(post['user_id'])})['profile_image']
        # Fetch commenter's profile image for each comment
        comments_with_profile_images = []
        for comment in comments:
            commenter_id = comment.get('commenter_id')  # Use .get() to safely retrieve 'commenter_id'
            if commenter_id:
                commenter = db.users.find_one({'_id': ObjectId(commenter_id)})
                if commenter and 'profile_image' in commenter:
                    comment['profile_image'] = commenter['profile_image']
                if commenter and 'username' in commenter:
                    comment['commenter_username'] = commenter['username']
            else:
                comment['profile_image'] = None
            comments_with_profile_images.append(comment)
        
        # Fetch likes associated with the post (if applicable)
        likes = db.likes.count_documents({'post_id': ObjectId(post_id)})
        return render_template('post_details.html', post=post, comments=comments_with_profile_images, likes=likes, post_profile_image=post_profile_image)
    else:
        return redirect(url_for('home'))
    
@post_blueprint.route('/add_comment/<post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    if request.method == 'POST':
        comment_text = request.form.get('comment')
        commenter_id = current_user.id
        
        # Store comment and commenter ID in the database
        db.comments.insert_one({'post_id': ObjectId(post_id), 'text': comment_text, 'commenter_id': commenter_id})

        post_details = db.posts.find_one({'_id': ObjectId(post_id)})
        create_notification(post_details['user_id'], current_user.id, f"{current_user.username} commented on your post.")

        return redirect(url_for('post.post_details', post_id=post_id))

# Route for liking a post
@post_blueprint.route('/like_post/<post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    liker_id = current_user.id
    liker_present = db.posts.find_one({'_id': ObjectId(post_id), 'likers': liker_id})
    post_details = db.posts.find_one({'_id': ObjectId(post_id)})
    if liker_present:
        db.posts.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': -1}, '$pull': {'likers': liker_id}})
    else:
        db.posts.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': 1}, '$push': {'likers': liker_id}})
        create_notification(post_details['user_id'], current_user.id, f"{current_user.username} liked your post.")
    return redirect(url_for('post.post_details', post_id=post_id))

@post_blueprint.route('/delete_comment/<comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    # Check if the current user has permission to delete the comment (optional)
    comment = db.comments.find_one({'_id': ObjectId(comment_id)})
    if comment['commenter_id'] != current_user.id:
        return jsonify({'error': 'You do not have permission to delete this comment'}), 403
    
    # Delete the comment
    result = db.comments.delete_one({'_id': ObjectId(comment_id)})
    if result.deleted_count == 1:
        return redirect(url_for('post.post_details',post_id=comment['post_id']))
    else:
        return jsonify({'error': 'Failed to delete comment'}), 500