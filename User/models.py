from flask_login import UserMixin

# Define a User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, email=None, username=None, password=None, profile_image=None, following=None, followers=None):
        self.id = user_id
        self.email = email
        self.username = username
        self.password = password
        self.profile_image = profile_image
        self.following = following
        self.followers = followers

    def get_id(self):
        return str(self.id)