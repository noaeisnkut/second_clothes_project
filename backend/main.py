import os
import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings

VAULT_URL = os.getenv("AZURE_KEYVAULT_URL") 
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER", "clothes-images")
credential = DefaultAzureCredential()
try:
    secret_client = SecretClient(vault_url=VAULT_URL, credential=credential)
    response = secret_client.get_secret("flask-app-secret")
    secrets = json.loads(response.value)
except Exception as e:
    raise RuntimeError(f"Failed to retrieve secrets from Azure: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
)

app.secret_key = os.getenv("SECRET_KEY", "change_this_in_production")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  

DB_USER = os.getenv("DB_USER", "psqladmin")
DB_PASSWORD = secrets["DB_PASSWORD"]
DB_HOST = os.getenv("DB_HOST") 
DB_NAME = os.getenv("DB_NAME", "second_hand_shop")
DB_PORT = os.getenv("DB_PORT", 5432)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
blob_service_client = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net", 
    credential=credential
)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

def get_s3_url(filename):
    """Generates an Azure SAS URL (Equivalent to S3 Presigned URL)"""
    try:
        sas_token = generate_blob_sas(
            account_name=STORAGE_ACCOUNT_NAME,
            container_name=CONTAINER_NAME,
            blob_name=filename,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
            user_delegation_key=blob_service_client.get_user_delegation_key(
                datetime.utcnow(), datetime.utcnow() + timedelta(hours=1)
            )
        )
        return f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{filename}?{sas_token}"
    except Exception:
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
    user_id = db.Column(db.Integer, db.ForeignKey("app_user.id"), nullable=False)
    s3_key = db.Column(db.String(200)) # We keep the name 's3_key' to avoid DB migrations
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
        try:
            price = Decimal(request.form.get("price"))
        except (InvalidOperation, TypeError):
            flash("Invalid price.", "error")
            return redirect(url_for("add"))

        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename != "":
            filename = f"{uuid.uuid4()}_{secure_filename(image_file.filename)}"
            try:
                blob_client = container_client.get_blob_client(filename)
                blob_client.upload_blob(
                    image_file, 
                    content_settings=ContentSettings(content_type=image_file.content_type)
                )
                image_filename = filename
            except Exception:
                flash("Azure Image upload failed.", "error")
                return redirect(url_for("add"))

        new_item = AddClothe(
            name=name, user_id=user_id, s3_key=image_filename,
            price=price, contact_info=contact_info, size=size,
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
        if User.query.filter_by(username=username).first():
            flash("Username exists.", "error")
            return redirect(url_for("sign_up"))
        hashed = generate_password_hash(password)
        db.session.add(User(username=username, password=hashed))
        db.session.commit()
        flash("Account created!", "success")
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
    return render_template("log_in.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/delete/<int:clothe_id>", methods=["POST"])
def delete(clothe_id):
    user_id = session.get("user_id")
    clothe = AddClothe.query.get_or_404(clothe_id)
    if clothe.user_id != user_id:
        flash("Denied.", "error")
        return redirect(url_for("index"))

    if clothe.s3_key:
        try:
            blob_client = container_client.get_blob_client(clothe.s3_key)
            blob_client.delete_blob()
        except Exception:
            pass  

    db.session.delete(clothe)
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)