from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_socketio import SocketIO, send
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from flask_bcrypt import Bcrypt
from Scripts.bookData import get_books

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


users = {}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    if username in users:
        return User(username)
    return None

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6), EqualTo("confirm", message="Passwords must match")])
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Register")

@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if username in users and bcrypt.check_password_hash(users[username]["password"], password):
            login_user(User(username))
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html", form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        if username in users:
            flash("Username already exists!", "danger")
        else:
            password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            users[username] = {"password": password}
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html", username=current_user.id)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/home")
@login_required
def home():
    return render_template("index.html")

@app.route('/home/<string:genre>')
def books_by_genre(genre):
    books = get_books(genre)
    return render_template('genre.html', genre=genre, books=books)

reviews = {}

class ReviewForm(FlaskForm):
    review_text = TextAreaField('Write a review', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

@app.route('/home/<string:genre>/<book_id>', methods=['GET', 'POST'])
def book_detail(book_id, genre):
    books = get_books(genre)
    book = books.get(int(book_id))  # Fetch the book from the dictionary
    print(book)
    if not book:
        flash("Book not found!", "danger")
        return redirect(url_for('books_by_genre', genre=genre))  # Redirect to home or book list page

    form = ReviewForm()

    if form.validate_on_submit():
        new_review = {"content": form.review_text.data, "author": "Anonymous"}  # Replace with logged-in user
        reviews.setdefault(book_id, []).append(new_review)
        flash("Review submitted successfully!", "success")
        return redirect(url_for('book_detail', book_id=book_id))

    return render_template("book_details.html", book=book, reviews=reviews.get(book_id, []), form=form)


# WebSocket Handling
@socketio.on("message")
def handle_message(msg):
    if current_user.is_authenticated:
        message = f"{current_user.id}: {msg}"
        send(message, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)