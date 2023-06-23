from flask import Flask, render_template, request, redirect, url_for
import os
from google.cloud import storage

from flask_sqlalchemy import SQLAlchemy
import pg8000

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from flask_ckeditor import CKEditor, CKEditorField
from wtforms.validators import InputRequired, Length
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config['SECRET_KEY'] = "secret key 2023"
app.config['CKEDITOR_PKG_TYPE'] = 'full'
ckeditor = CKEditor(app)
Bootstrap(app)
app.app_context().push()

#URL_MYSQL_DB = os.environ.get('MY_URL_MYSQL_DB')
#URL_GCLOUD_MYSQL_DB = os.environ.get('MY_URL_GCLOUD_MYSQL_DB')
URL_GCLOUD_POSTRESQL_DB = os.environ.get('MY_URL_GCLOUD_POSTRESQL_DB')

#app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{URL_MYSQL_DB}"
#app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{URL_GCLOUD_MYSQL_DB}"
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+pg8000://{URL_GCLOUD_POSTRESQL_DB}"


db = SQLAlchemy(app)

class myappsn(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    title = db.Column(db.VARCHAR(255), nullable=False)
    show_order = db.Column(db.INTEGER, nullable=False)
    brief = db.Column(db.VARCHAR(1000), nullable=True)
    tools = db.Column(db.VARCHAR(250), nullable=True)
    img1 = db.Column(db.VARCHAR(250), nullable=True)
    img2 = db.Column(db.VARCHAR(250), nullable=True)
    img3 = db.Column(db.VARCHAR(250), nullable=True)
    img_header = db.Column(db.VARCHAR(250), nullable=True)
    app_link = db.Column(db.VARCHAR(250), nullable=True)
    source_code = db.Column(db.VARCHAR(250), nullable=True)
    description = db.Column(db.TEXT, nullable=True)
    description2 = db.Column(db.VARCHAR(2000), nullable=True)
    video_link = db.Column(db.VARCHAR(250), nullable=True)


class CreateEditForm(FlaskForm):
    body = CKEditorField("description", validators=[InputRequired()])
    submit = SubmitField("Submit Post")



def getAppDataFromDB():
    app_data=myappsn.query.all() # read from DB
    app_data=sorted(app_data, key=lambda k: k.show_order, reverse=False) #sort records order
    return app_data


my_portfolio = getAppDataFromDB()

storage_client = storage.Client("my-apps-portfolio")
bucket = storage_client.get_bucket("apppics")
blob = bucket.blob(f"about_me.dat")
with blob.open("r") as f:
    about_me_data = f.read()


@app.route("/edit_about", methods=["GET", "POST"])
def edit_about():
    global about_me_data
    edit_form = CreateEditForm(
        body=about_me_data
    )
    if edit_form.validate_on_submit():
        about_me_data= edit_form.body.data
        # write
        storage_client = storage.Client("my-apps-portfolio")
        bucket = storage_client.get_bucket("apppics")
        blob = bucket.blob(f"about_me.dat")
        with blob.open("w") as f:
            f.write(about_me_data)

        return redirect(url_for("about"))
    return render_template("edit_about.html", form=edit_form)


@app.route("/about")
def about():
    return render_template("about.html", about_me=about_me_data)


@app.route("/")
def get_all_my_apps():
    return render_template("index.html",all_apps=my_portfolio)


@app.route("/edit_app/<int:index>", methods=["GET", "POST"])
def edit_app(index):
    global my_portfolio
    # POST
    if request.method == "POST":
        myapp = myappsn.query.get(index)
        myapp.title = request.form["title"]
        myapp.tools = request.form["tools"]
        myapp.brief = request.form["brief"]
        myapp.description = request.form["description"]
        myapp.description2 = request.form["description2"]
        myapp.video_link = request.form["video_link"]
        myapp.app_link = request.form["app_link"]
        myapp.source_code = request.form["source_code"]
        myapp.show_order = request.form["show_order"]

        storage_client = storage.Client("my-apps-portfolio")
        bucket = storage_client.get_bucket("apppics")
        FILEPATH_APP_DIR = f"https://storage.googleapis.com/apppics/{index}/"

        img1_file = request.files['img1']
        if img1_file:
            img1_filename = img1_file.filename
            myapp.img1= FILEPATH_APP_DIR + img1_filename
            blob_img1 = bucket.blob(f"{index}/{img1_filename}")
            blob_img1.upload_from_file(img1_file)

        img2_file = request.files['img2']
        if img2_file:
            img2_filename = img2_file.filename
            myapp.img2 = FILEPATH_APP_DIR + img2_filename
            blob_img2 = bucket.blob(f"{index}/{img2_filename}")
            blob_img2.upload_from_file(img2_file)

        img3_file = request.files['img3']
        if img3_file:
            img3_filename = img3_file.filename
            myapp.img3 = FILEPATH_APP_DIR + img3_filename
            blob_img3 = bucket.blob(f"{index}/{img3_filename}")
            blob_img3.upload_from_file(img3_file)

        img_header_file = request.files['img_header']
        if img_header_file:
            img_header_filename = img_header_file.filename
            myapp.img_header = FILEPATH_APP_DIR + img_header_filename
            blob_img_header = bucket.blob(f"{index}/{img_header_filename}")
            blob_img_header.upload_from_file(img_header_file)

        db.session.commit()
        my_portfolio = getAppDataFromDB()
        return redirect(url_for("show_my_app", index=myapp.id))
    # GET
    requested_app = None
    for my_app in my_portfolio:
        if my_app.id == index:
            requested_app = my_app
    return render_template("edit_app.html", my_app=requested_app)


@app.route("/new_app/")
def add_new_app():
    newapp = myappsn()
    newapp.title="Add Title"
    newapp.img1 ="/static/assets/img/app-main.jpg"
    newapp.img_header = "/static/assets/img/app-head.jpg"

    newapp.show_order = 1
    db.session.add(newapp)
    db.session.commit()
    my_portfolio = getAppDataFromDB()
    requested_app = None
    for new_app in my_portfolio:
        if new_app.title == "Add Title":
            requested_app = new_app
    return render_template("edit_app.html", my_app=requested_app)


@app.route("/delete_app/<int:index>")
def delete_app(index):
    app_to_delete = myappsn.query.get(index)
    db.session.delete(app_to_delete)
    db.session.commit()

    storage_client = storage.Client("my-apps-portfolio")
    bucket = storage_client.get_bucket("apppics")
    blobs = bucket.list_blobs(prefix=f"{index}/")
    for blob in blobs:
        blob.delete()

    my_portfolio = getAppDataFromDB()
    return render_template("index.html",all_apps=my_portfolio)


@app.route("/myapp/<int:index>")
def show_my_app(index):
    requested_app = None
    for my_app in my_portfolio:
        if my_app.id == index:
            requested_app = my_app
    print(requested_app.img2)
    print(requested_app.img3)
    return render_template("show_app.html", my_app=requested_app)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)