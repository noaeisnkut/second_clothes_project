import os
import boto3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static")
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "frontend", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(
    os.getenv('DB_USER', 'root'),
    os.getenv('DB_PASSWORD', 'pass'),
    os.getenv('DB_HOST', 'flask_mysql'),
    os.getenv('DB_NAME', 'flask')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "my-second-hand-clothes-storage")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class AddClothe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    owner = db.Column(db.String(100))
    image_filename = db.Column(db.String(200))
    price = db.Column(db.Float)
    contact = db.Column(db.String(100))
    size = db.Column(db.String(20), nullable=True)

@app.route('/')
def index():
    clothes = AddClothe.query.all()
    return render_template("home_page.html", clothes=clothes)
@app.route('/add', methods=["GET"])
def add_page():
    if "username" not in session:
        flash("You must be logged in to add a product.", 'error')
        return redirect(url_for("index"))
    return render_template("add_product.html")


@app.route('/add_product', methods=["POST"])
def add():
    if "username" not in session:
        flash("You must be logged in to add a product.", 'error')
        return redirect(url_for("index"))

    title = request.form.get("title")
    price = request.form.get("price")
    image = request.files.get("image")
    contact = request.form.get("contact")
    size = request.form.get("size")
    image_filename = None

    if image:
      image_filename = secure_filename(image.filename)
      local_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
      image.save(local_path)
      s3.upload_file(local_path, BUCKET_NAME, image_filename)


    new_clothe = AddClothe(title=title, owner=session["username"], image_filename=image_filename, price=price,
                           size=size, contact=contact)
    db.session.add(new_clothe)
    db.session.commit()

    flash("Product added successfully!", 'success')
    return redirect(url_for("index"))


@app.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", 'error')
            return redirect(url_for("sign_up"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully! Please log in.", 'success')
        return redirect(url_for("index"))

    return render_template("sign_up.html")


@app.route('/log-in', methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = user.username
            flash("Logged in successfully.", 'success')
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", 'error')
            return redirect(url_for("log_in"))

    return render_template("log_in.html")


@app.route('/delete/<int:clothe_id>')
def delete(clothe_id):
    if "username" not in session:
        flash("You must be logged in to delete a product.", 'error')
        return redirect(url_for("index"))

    clothe = AddClothe.query.get(clothe_id)
    if clothe and clothe.owner == session["username"]:
        db.session.delete(clothe)
        db.session.commit()
        flash("Item deleted.", 'success')
    else:
        flash("You can only delete your own items.", 'error')
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host=os.getenv('IP', '0.0.0.0'), debug=True)

