import os
import uuid
import json
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import boto3
import botocore


SECRET_NAME = "flask-app-secret"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

try:
    secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    secrets = json.loads(response["SecretString"])
except Exception as e:
    raise RuntimeError(f"Failed to retrieve secrets: {e}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
)

app.secret_key = os.getenv("SECRET_KEY", "change_this_in_production")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  



DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = secrets["DB_PASSWORD"]
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "flask")
DB_PORT = os.getenv("DB_PORT", 5432)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


bucket_name = os.getenv("S3_BUCKET", "my-second-hand-clothes-storage")

s3 = boto3.client("s3", region_name=AWS_REGION)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_s3_url(filename):
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": filename},
            ExpiresIn=3600,
        )
    except botocore.exceptions.ClientError:
        return None


class User(db.Model):
    __tablename__ = "app_user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column("password_hash", db.String(200), nullable=False)


class AddClothe(db.Model):
    __tablename__ = "add_clothe"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("app_user.id"),
        nullable=False,
    )

    s3_key = db.Column(db.String(200))

    price = db.Column(db.Numeric(10, 2), nullable=False)

    contact_info = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(20), nullable=False)

    user = db.relationship("User", backref="clothes", lazy=True)

    @property
    def image_url(self):
        if self.s3_key:
            return get_s3_url(self.s3_key)
        return None


@app.route("/")
def index():
    clothes = AddClothe.query.all()
    return render_template("home_page.html", clothes=clothes)


@app.route("/add", methods=["GET", "POST"])
def add():
    user_id = session.get("user_id")
    if not user_id:
        flash("Log in first!", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("title")
        contact_info = request.form.get("contact")
        size = request.form.get("size")

        if not name or not contact_info or not size:
            flash("All fields are required.", "error")
            return redirect(url_for("add"))

        try:
            price = Decimal(request.form.get("price"))
        except (InvalidOperation, TypeError):
            flash("Invalid price.", "error")
            return redirect(url_for("add"))

        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename != "":
            if not allowed_file(image_file.filename):
                flash("Invalid file type.", "error")
                return redirect(url_for("add"))

            filename = f"{uuid.uuid4()}_{secure_filename(image_file.filename)}"

            try:
                s3.upload_fileobj(image_file, bucket_name, filename)
                image_filename = filename
            except botocore.exceptions.ClientError:
                flash("Image upload failed.", "error")
                return redirect(url_for("add"))

        new_item = AddClothe(
            name=name,
            user_id=user_id,
            s3_key=image_filename,
            price=price,
            contact_info=contact_info,
            size=size,
        )

        db.session.add(new_item)
        db.session.commit()

        flash("Product added!", "success")
        return redirect(url_for("index"))

    return render_template("add_product.html")


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("sign_up"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return redirect(url_for("sign_up"))

        hashed = generate_password_hash(password)

        db.session.add(User(username=username, password=hashed))
        db.session.commit()

        flash("Account created! Log in.", "success")
        return redirect(url_for("index"))

    return render_template("sign_up.html")


@app.route("/log-in", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Logged in!", "success")
            return redirect(url_for("index"))

        flash("Invalid login.", "error")
        return redirect(url_for("log_in"))

    return render_template("log_in.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:clothe_id>", methods=["POST"])
def delete(clothe_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("You must be logged in.", "error")
        return redirect(url_for("index"))

    clothe = AddClothe.query.get_or_404(clothe_id)

    if clothe.user_id != user_id:
        flash("You can only delete your own items.", "error")
        return redirect(url_for("index"))

    if clothe.s3_key:
        try:
            s3.delete_object(Bucket=bucket_name, Key=clothe.s3_key)
        except botocore.exceptions.ClientError:
            pass  

    db.session.delete(clothe)
    db.session.commit()

    flash("Item deleted.", "success")
    return redirect(url_for("index"))



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
