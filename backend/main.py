import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import boto3
import botocore
import json



SECRET_NAME = "flask-app-secret"
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

client = boto3.client("secretsmanager", region_name=AWS_REGION)
response = client.get_secret_value(SecretId=SECRET_NAME)
secrets = json.loads(response["SecretString"])


db_password = secrets["DB_PASSWORD"]


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static")
)

app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 


bucket_name = os.getenv("S3_BUCKET", "my-second-hand-clothes-storage")
region = os.getenv("AWS_REGION", "us-east-1")

s3 = boto3.client(
   "s3",
   region_name=region,
)


def get_s3_url(filename):
   try:
       url = s3.generate_presigned_url(
           'get_object',
           Params={'Bucket': bucket_name, 'Key': filename},
           ExpiresIn=3600
       )
       return url
   except botocore.exceptions.ClientError as e:
       print("Error generating S3 URL:", e)
       return None

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = secrets["DB_PASSWORD"]
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "flask")
DB_PORT = os.getenv("DB_PORT", 5432)


app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

class User(db.Model):
   __tablename__ = 'app_user' 
   id = db.Column(db.Integer, primary_key=True)
   username = db.Column(db.String(100), unique=True)
   password = db.Column('password_hash', db.String(200)) 

class AddClothe(db.Model):
   __tablename__ = 'add_clothe'
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column('name', db.String(255))
   user_fk = db.Column('user_fk', db.String(100)) 
   s3_key = db.Column('image_url', db.String(200)) 
   price = db.Column(db.Float)
   contact_info = db.Column(db.String(100))
   size = db.Column(db.String(20), nullable=True)


   @property
   def image_url(self):
       if self.s3_key: 
           return get_s3_url(self.s3_key)
       return None


@app.route('/')
def index():
   clothes = AddClothe.query.all()
   return render_template("home_page.html", clothes=clothes)


@app.route('/add', methods=["GET", "POST"])
def add():
   if "username" not in session:
       flash("Log in first!", "error")
       return redirect(url_for("index"))


   if request.method == "POST":
       name = request.form.get("title")
       price = request.form.get("price")
       contact_info = request.form.get("contact")
       size = request.form.get("size")
       image_file = request.files.get("image")


       image_filename = None
       if image_file:
           filename = secure_filename(image_file.filename)
           s3.upload_fileobj(image_file, bucket_name, filename)
           image_filename = filename


       new_item = AddClothe(
           name=name,
           user_fk=session["username"],
           s3_key=image_filename,
           price=price,
           contact_info=contact_info,
           size=size
       )
       db.session.add(new_item)
       db.session.commit()
       flash("Product added!", "success")
       return redirect(url_for("index"))


   return render_template("add_product.html")


@app.route('/sign-up', methods=["GET", "POST"])
def sign_up():
   if request.method == "POST":
       username = request.form.get("username")
       password = request.form.get("password")
       if User.query.filter_by(username=username).first():
           flash("Username already exists.", "error")
           return redirect(url_for("sign_up"))
       hashed = generate_password_hash(password)
       db.session.add(User(username=username, password=hashed))
       db.session.commit()
       flash("Account created! Log in.", "success")
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
           flash("Logged in!", "success")
           return redirect(url_for("index"))
       else:
           flash("Invalid login.", "error")
           return redirect(url_for("log_in"))
   return render_template("log_in.html")

@app.route('/delete/<int:clothe_id>', methods=["POST"])
def delete(clothe_id):
    if "username" not in session:
        flash("You must be logged in to delete a product.", 'error')
        return redirect(url_for("index"))

    clothe = AddClothe.query.get_or_404(clothe_id)
    if clothe and clothe.user_fk == session["username"]:
        if clothe.s3_key:
            try:
                s3.delete_object(Bucket=bucket_name, Key=clothe.s3_key)
            except botocore.exceptions.ClientError as e:
                print(f"Error deleting from S3: {e}")
        db.session.delete(clothe)
        db.session.commit()
        
        flash("Item deleted.", 'success')
    else:
        flash("You can only delete your own items.", 'error')

    return redirect(url_for("index"))


if __name__ == "__main__":
   with app.app_context():
       pass
   app.run(host='0.0.0.0', port=5000, debug=True)