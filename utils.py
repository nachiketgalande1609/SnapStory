import os
from werkzeug.utils import secure_filename

# Function to check if the file extension is allowed
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to save image file
def save_image(image):
    # Ensure the 'static/posts/images' directory exists
    os.makedirs('static/posts/images', exist_ok=True)

    # Generate a secure filename
    filename = secure_filename(image.filename)

    # Save the image to the 'static/posts/images' directory
    image_path = os.path.join('static/posts/images', filename)
    image.save(image_path)

    # Return the relative path of the saved image
    return f'posts/images/{filename}'
