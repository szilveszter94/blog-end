from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date, datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
# import Flask user manager modules
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm, CreatePostForm, CommentForm
from flask_gravatar import Gravatar
import smtplib
import os

# set app
my_email = os.environ.get("EMAIL")
my_password = os.environ.get("PASSWORD")
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL",  "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# login user module
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# set user database model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

# set posts database model
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

# set comments database model
class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    comment_author = relationship("User", back_populates="comments")
    text = db.Column(db.Text, nullable=False)
db.create_all()

# routes available only for admin
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

# set homapage
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user, date=date.today().strftime("%Y"))

# set register page
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        
        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        # getting password from input & salting and hashing password
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        # getting data from input and create new user
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        # add new user to database
        db.session.add(new_user)
        db.session.commit()
        # login user, after successfully register
        login_user(new_user)
        # redirect to home page
        return redirect(url_for("get_all_posts"))

    return render_template("register.html", form=form, current_user=current_user, date=date.today().strftime("%Y"))

# set login route
@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # getting data from the form
        email = form.email.data
        password = form.password.data
        # check if the user email exists
        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("Ez az email cím nem található az adatbázisban, próbálkozz újra.")
            return redirect(url_for('login'))
        # check if the password is wrong
        elif not check_password_hash(user.password, password):
            flash('Helytelen jelszó, próbálkozz újra.')
            return redirect(url_for('login'))
        # login if the email and password is correct
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form, current_user=current_user, date=date.today().strftime("%Y"))

# set logout user route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

# set a single post route
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)
    # check if user is logged in for comment
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Előbb regisztrálj vagy jelentkezz be a hozzászóláshoz.")
            return redirect(url_for("login"))
        # create a new comment
        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        # insert new comment into the database
        db.session.add(new_comment)
        db.session.commit()

    return render_template("post.html", post=requested_post, form=form, current_user=current_user, date=date.today().strftime("%Y"))

# create about route
@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user, date=date.today().strftime("%Y"))

# create contact route
@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        # get the information from the form
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")
        # check if every field is filled
        if len(name) > 0 and len(email) > 0 and len(phone) > 0 and len(message) > 0:
            # sending email using smtplib module
            with smtplib.SMTP("smtp.gmail.com", 587) as connection:
                connection.starttls()
                connection.login(user=my_email, password=my_password)
                connection.sendmail(from_addr=my_email,
                                    to_addrs="s.szilveszter1994@gmail.com",
                                    msg=f"Subject:Blog Üzenet\n\nNév: {name}\nE-mail cím: {email}\n"
                                        f"Telefonszám: {phone}\nÜzenet: {message}".encode("utf-8"))
                connection.quit()
            return render_template("contact.html", request=True, current_user=current_user, date=date.today().strftime("%Y"))
        else:
            return render_template("contact.html", request=None, current_user=current_user, date=date.today().strftime("%Y"))
    else:
        return render_template("contact.html", request=False, current_user=current_user, date=date.today().strftime("%Y"))

# create new post route
@app.route("/new-post", methods=["GET", "POST"])
# @admin_only = this route is available only for admin
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        # getting information from the post form
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%Y.%m.%d.")
        )
        # add new post into the database
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, current_user=current_user, date=date.today().strftime("%Y"))



# create edit route
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
# @admin_only = this route is available only for admin
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    # paste corresponding information about the post (what i like to edit) from the database into the edit post form
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    # getting information from the edit form
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        # modify the post in the database
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user, date=date.today().strftime("%Y"))

# create delete post route
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    # search the post based on the ID
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    # modify the database
    db.session.commit()
    return redirect(url_for('get_all_posts'))

# start the server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
