from flask import Flask, render_template, redirect, send_from_directory, url_for, request, session, flash
from flask_socketio import SocketIO, send
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from flask_bcrypt import Bcrypt
from itertools import islice
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from Scripts.bookData import get_books_genre, get_books1
from Scripts.genreData import get_genres
from Scripts.booksData import get_books
from Scripts.authorData import get_authors

DATABASE_URL = "mysql+pymysql://root:aryan2424@localhost/book_bros"


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
bcrypt = Bcrypt(app)
ALLOWED_EXTENSIONS = {'pdf', 'epub', 'mobi'}
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

login_manager = LoginManager(app)
login_manager.login_view = "login"




class User(db.Model, UserMixin):
    id = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_verified_author = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(255), default="author.png")
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User('{self.id}', '{self.email}', '{self.is_premium}')"

class Author(db.Model, UserMixin):
    id = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # books = db.relationship('Book', backref='author_details', lazy=True)
    profile_image = db.Column(db.String(255), default="author.png")
    is_verified = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Author('{self.id}', '{self.email}', '{self.email}')"

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(100), unique=True, nullable=False)
    messages = db.relationship('Message', backref='chatroom', lazy=True)

    def __repr__(self):
        return f"ChatRoom('{self.genre}')"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)

    sender = db.relationship('User', backref='messages_sent', lazy=True)

    def __repr__(self):
        return f"Message('{self.sender_id}', '{self.content}', '{self.timestamp}')"
    
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    genre = db.Column(db.String(100), nullable=False)
    author_id = db.Column(db.String(20), db.ForeignKey('author.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # New field for verification status

    author = db.relationship('Author', backref='books')

    def __repr__(self):
        return f"Book('{self.title}', '{self.genre}', '{self.author_id}', Verified={self.is_verified})"
    
class Webinar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    author_id = db.Column(db.String(255), db.ForeignKey('author.id'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

    attendees = db.relationship('User', secondary='webinar_registration', backref=db.backref('webinars', lazy='dynamic'))

    def __repr__(self):
        return f'<Webinar {self.title}>'
    

class Card(db.Model):
    __tablename__ = 'dummy_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    cardholder_name = db.Column(db.String(100), nullable=False)
    card_number = db.Column(db.String(20), unique=True, nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)  # Format: MM/YY
    cvv = db.Column(db.String(4), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=1000.00)

    def __repr__(self):
        return f"<Card {self.cardholder_name} - {self.card_number}>"
    
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)

    user = db.relationship('User', backref='reviews')
    book = db.relationship('Book', backref='reviews')


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user:
        return user
    return Author.query.get(user_id)

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

class AuthorRegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6), EqualTo("confirm", message="Passwords must match")])
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Register as Author")

class WebinarRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), db.ForeignKey('user.id'), nullable=False)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinar.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('registrations', lazy=True))
    webinar = db.relationship('Webinar', backref=db.backref('registrations', lazy=True))

    def __repr__(self):
        return f'<Registration user_id={self.user_id} webinar_id={self.webinar_id}>'

@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()

        user = User.query.filter_by(id=username).first()
        author = Author.query.filter_by(id=username).first()

        # If user exists and password matches
        if user and bcrypt.check_password_hash(user.password, password):
            if user.is_blocked:
                flash("You are blocked. Please contact support.")
                return redirect(url_for("login"))
            login_user(user)
            if user.is_admin:
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("home"))

        # If author exists and password matches
        elif author and bcrypt.check_password_hash(author.password, password):
            login_user(author)
            if author.is_verified:
                return redirect(url_for("author_home"))
            else:
                flash("Not a Verified Author")
                return redirect(url_for("login"))

        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        if User.query.filter_by(id=username).first():
            flash("Username already exists!", "danger")
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(id=username, email=email, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/author_register", methods=["GET", "POST"])
def author_register():
    form = AuthorRegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        if Author.query.filter_by(id=username).first():
            flash("Username already exists!", "danger")
        else:
            new_author = Author(id=username, email=email, password=password, is_verified=False)
            db.session.add(new_author)
            db.session.commit()
            flash("Author registration successful! Please wait for verification.", "success")
            return redirect(url_for("login"))
    
    return render_template("author_register.html", form=form)

@app.route('/schedule_webinar', methods=['GET', 'POST'])
@login_required
def schedule_webinar():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        duration = request.form['duration']
        genre = request.form['genre']
        
        new_webinar = Webinar(
            title=title,
            description=description,
            date=date,
            duration=duration,
            genre=genre,
            author_id=current_user.id,
            is_verified=False
        )

        db.session.add(new_webinar)
        db.session.commit()

        return redirect(url_for('home'))

    return render_template('webinar.html')

@app.route('/user_webinars')
def user_webinars():
    current_time = datetime.now()

    webinars = Webinar.query.filter(Webinar.date >= current_time).all()

    return render_template('user_webinars.html', webinars=webinars)

@app.route('/upcoming_webinars')
def upcoming_webinars():
    current_time = datetime.now()

    isAuth = False
    if current_user.__class__.__name__ == "Author":
        isAuth=True

    webinars = Webinar.query.filter(
        Webinar.date >= current_time,
        Webinar.is_verified == True
    ).all()

    

    return render_template('upcoming_webinars.html', webinars=webinars, isAuth=isAuth)

@app.route("/register_webinar/<int:webinar_id>", methods=["GET", "POST"])
@login_required
def register_webinar(webinar_id):
    webinar = Webinar.query.get_or_404(webinar_id)

    # Check if user is already registered
    if current_user in webinar.attendees:
        return redirect(url_for("upcoming_webinars"))

    if request.method == "POST":
        # Simulating a successful payment
        webinar.attendees.append(current_user)
        db.session.commit()

        return redirect(url_for("upcoming_webinars"))

    return render_template("register_webinar.html", webinar=webinar)


@app.route("/chat/<genre>", methods=["GET", "POST"])
@login_required
def chat(genre):
    isAuth = False
    if current_user.__class__.__name__ == "Author":
        isAuth = True

    chat_room = ChatRoom.query.filter_by(genre=genre).first()
    if not chat_room:
        chat_room = ChatRoom(genre=genre)
        db.session.add(chat_room)
        db.session.commit()

    messages = Message.query.filter_by(chatroom_id=chat_room.id).order_by(Message.timestamp.asc()).all()
    messages_data = [
        {"user_id": message.sender_id, "message": message.content, "timestamp": message.timestamp}
        for message in messages
    ]

    return render_template("chat.html", genre=genre, messages=messages_data, isAuth=isAuth)

@app.route("/premium")
@login_required
def premium():
    isPrem = current_user.is_premium
    return render_template('premium.html', isPrem=isPrem)

@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    if request.method == "POST":
        name = request.form["cardholder"]
        cardnumber = request.form["cardnumber"]
        expiry = request.form["expiry"]
        cvv = request.form["cvv"]

        card = db.session.query(Card).filter_by(
            card_number=cardnumber,
            expiry_date=expiry,
            cvv=cvv
        ).first()

        if card and card.balance >= 129:
            card.balance -= 129
            db.session.commit()
            current_user.is_premium = True
            db.session.commit()

            flash("Payment successful! You've been upgraded to Premium.", "success")
            return redirect(url_for("premium"))
        else:
            flash("Payment failed. Invalid card details or insufficient balance.", "error")

    return render_template("payment.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/home")
@login_required
def home():
    genres = get_genres()
    books = {book.id: book for book in Book.query.filter_by(is_verified=True).limit(5).all()}
    
    authors = dict(islice(get_authors().items(), 5))
    
    return render_template("home.html", username=current_user.id, genres=genres, books=books, authors=authors)

@app.route("/author_home")
@login_required
def author_home():
    genres = get_genres()
    books = dict(islice(get_books().items(), 5))
    authors = dict(islice(get_authors().items(), 5))
    
    return render_template("author_home.html", username=current_user.id, genres=genres, books=books, authors=authors)

@app.route("/books/<string:author_id>")
@login_required
def author_books(author_id):
    books = Book.query.filter_by(author_id=author_id).all()
    isAuth = False
    if current_user.__class__.__name__ == "Author":
        isAuth=True
    return render_template('author_books.html', books=books, isAuth=isAuth)

@app.route('/book/<int:book_id>/review', methods=['POST'])
@login_required
def add_review(book_id):
    content = request.form['content']
    rating = int(request.form['rating'])
    review = Review(content=content, rating=rating, user_id=current_user.id, book_id=book_id)
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('author_book_detail', book_id=book_id))

# @app.route('/home/<string:genre>')
# def books_by_genre(genre):
#     isAuth = False
#     if current_user.__class__.__name__ == "Author":
#         isAuth = True
#     books = get_books1(genre)
#     genres = get_genres()
#     for i, j in genres.items():
#         if genres[i][0] == genre:
#             genreImg = genres[i][1]
#     return render_template('genre.html', genre=genre, books=books, genreImg=genreImg, isAuth=isAuth)

@app.route('/home/<string:genre>')
def books_by_genre(genre):
    isAuth = False
    if current_user.__class__.__name__ == "Author":
        isAuth = True

    # Get current page number from query params
    page = request.args.get('page', 1, type=int)
    books_per_page = 14  # Adjust this number as needed

    all_books = get_books1(genre)  # full dict of books
    total_books = len(all_books)

    # Sort keys to ensure consistent order
    book_keys = sorted(all_books.keys())

    # Calculate paginated slice
    start = (page - 1) * books_per_page
    end = start + books_per_page
    paginated_keys = book_keys[start:end]

    # Filter only the books for the current page
    paginated_books = {key: all_books[key] for key in paginated_keys}

    genres = get_genres()
    genreImg = next((img for name, img in genres.values() if name == genre), None)

    total_pages = (total_books + books_per_page - 1) // books_per_page

    return render_template(
        'genre.html',
        genre=genre,
        books=paginated_books,
        genreImg=genreImg,
        isAuth=isAuth,
        page=page,
        total_pages=total_pages
    )

@app.route("/publish_book", methods=["GET", "POST"])
@login_required
def publish_book():
    isAuth = False
    if current_user.__class__.__name__ == "Author":
        isAuth=True

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        genre = request.form["genre"]
        image_url = request.form["image_url"]

        if 'book_file' not in request.files:
            return redirect(request.url)

        file = request.files['book_file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            new_book = Book(
                title=title,
                description=description,
                genre=genre,
                image_url=image_url,
                author_id=current_user.id,
                file_path=file_path,
                is_verified=False  # Set book as unverified
            )

            db.session.add(new_book)
            db.session.commit()

            if isAuth:
                return redirect(url_for('author_home'))
            else:
                return redirect(url_for("home"))
        else:
            flash()

    return render_template('publish_book.html', isAuth=isAuth)

@app.route("/read_book/<int:book_id>")
@login_required
def read_book(book_id):
    book = Book.query.get_or_404(book_id)
    genres = get_genres()
    genreImg = "home-background.webp"
    for i, j in genres.items():
        if genres[i][0] == book.genre:
            genreImg = genres[i][1]


    file_path = book.file_path  # Example: 'static/uploads/CSET_207_Lab_Assignment_Week_8.pdf'
    upload_folder = app.config['UPLOAD_FOLDER']  # Example: 'static/uploads'

        # Extract filename from the file path
    filename = os.path.basename(file_path)

        # Debugging Prints
    print(f"Book File Path: {file_path}")
    print(f"Upload Folder: {upload_folder}")
    print(f"Extracted Filename: {filename}")
    print(f"Full Path Exists? {os.path.exists(file_path)}")  # Check if full path exists (relative to app root)
    print(f"Final Path Exists? {os.path.exists(os.path.join(upload_folder, filename))}")  # Check expected directory

        # Ensure the file exists in the upload folder
    file_full_path = os.path.join(upload_folder, filename)
    print(file_full_path)
    if not os.path.exists(file_full_path):
        
        return redirect(url_for('home'))


    return send_from_directory(upload_folder, filename)

@app.route('/home/<string:genre>/<int:book_id>', methods=['GET', 'POST'])
def book_detail(genre, book_id):
    books = get_books_genre(genre)
    book = books.get(book_id)
    isAuth = False
    if isAuth.__class__.__name__ == "Author":
        isAuth = True

    genres = get_genres()
    for i, j in genres.items():
        if genres[i][0] == genre:
            genreImg = genres[i][1]

    if not book:
        
        return redirect(url_for('books_by_genre', genre=genre))

    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.timestamp.desc()).all()

    return render_template("book_details.html", book=book, reviews=reviews, genreImg=genreImg, isAuth=isAuth, book_id=book_id)

@app.route('/<int:book_id>', methods=['GET', 'POST'])
def author_book_detail(book_id):
    book = Book.query.filter_by(id=book_id).first()
    genres = get_genres()
    genreImg = "home-background.webp"
    for i, j in genres.items():
        if genres[i][0] == book.genre:
            genreImg = genres[i][1]

    if not book:
        
        return redirect(url_for('author_books'))
    
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.timestamp.desc()).all()

    return render_template("author_book_details.html", book=book, genreImg=genreImg, reviews=reviews)

@app.route("/admin/verify_author/<string:author_id>")
@login_required
def verify_author(author_id):
    author = Author.query.filter_by(id=author_id).first()
    
    author.is_verified = True 
    db.session.commit()

    return redirect(url_for("verify_authors"))

@app.route("/admin/reject_author/<string:author_id>")
@login_required
def reject_author(author_id):
    author = Author.query.filter_by(id=author_id).first()
    
    db.session.delete(author)
    db.session.commit()

    return redirect(url_for("verify_authors"))

@app.route("/admin/verify_book/<int:book_id>")
@login_required
def verify_book(book_id):
    book = Book.query.get_or_404(book_id)
    book.is_verified = True
    db.session.commit()
    
    return redirect(url_for("verify_books"))

@app.route("/admin/reject_book/<int:book_id>")
@login_required
def reject_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    
    return redirect(url_for("verify_books"))

@app.route("/admin")
@login_required
def admin():
    return render_template("admin_dashboard.html")

@app.route("/admin/verify_books")
@login_required
def verify_books():
    publish = Book.query.filter_by(is_verified=False).all()
    print(publish)

    return render_template("publish_requests.html", publish=publish)

@app.route("/admin/verify_talkshow")
@login_required
def verify_talkshows():
    webinars = Webinar.query.filter_by(is_verified=False).all()

    return render_template("talk_show.html", webinars=webinars)

@app.route("/admin/reject_talkshow/<int:webinar_id>")
@login_required
def reject_talkshow(webinar_id):
    webinar = Webinar.query.get_or_404(webinar_id)
    db.session.delete(webinar)
    db.session.commit()
    return redirect(url_for("verify_talkshows"))

@app.route("/admin/verify_talkshow/<int:webinar_id>")
@login_required
def verify_talkshow(webinar_id):
    webinar = Webinar.query.get_or_404(webinar_id)
    webinar.is_verified = True
    db.session.commit()
    return redirect(url_for('verify_talkshows'))

@app.route("/admin/verify_authors")
@login_required
def verify_authors():
    authors = Author.query.filter_by(is_verified=False).all()

    return render_template("verify_authors.html", authors=authors)

@app.route("/admin/users")
@login_required
def users():
    users = User.query.all()
    return render_template("users.html", users=users)

@app.route('/admin/chatrooms')
@login_required
def chatrooms():
    genres = get_genres()
    print(genres)
    return render_template("chatrooms.html", genres=genres)

@app.route('/admin/blocked_users')
def blocked_users():
    users = User.query.filter_by(is_blocked=True).all()
    return render_template("blocked_users.html", users=users)

@app.route('/admin/block_user/<string:user_id>')
def block_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        user.is_blocked = True
        db.session.commit()
    return redirect(url_for('users'))

@app.route('/admin/unblock_user/<string:user_id>')
def unblock_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        user.is_blocked = False
        db.session.commit()
    return redirect(url_for('blocked_users'))

@app.route("/admin/add_book", methods=["GET", "POST"])
@login_required
def add_books():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        description = request.form["description"]
        genre = request.form["genre"]
        image_url = request.form["image_url"]

        if 'book_file' not in request.files:
            
            return redirect(request.url)

        file = request.files['book_file']

        if file.filename == '':
            
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            new_book = Book(
                title=title,
                description=description,
                genre=genre,
                image_url=image_url,
                author_id=author,
                file_path=file_path,
                is_verified=False  # Set book as unverified
            )

            db.session.add(new_book)
            db.session.commit()

            
            return redirect(url_for('home'))
        else:
            flash()

    return render_template('add_books.html')


@app.route('/author_details/<string:author_id>', methods=['GET', 'POST'])
def author_detail(author_id):
    author = Author.query.filter_by(id=author_id).first()
    isAuth = False
    if current_user.__class__.__name__ == "Author":
        isAuth = True

    return render_template("author_details.html", author=author, isAuth=isAuth)

@app.route('/privacy_policy')
def privacy_policy():
    return render_template("privacy.html")



@socketio.on("join")
def join_room(genre):
    """Handle user joining a chat room (genre)."""
    join_room(genre)
    send(f"{current_user.id} has entered the {genre} chat room.", room=genre)

@socketio.on("message")
def handle_message(data):
    msg = data.get('msg')
    genre = data.get('genre')
    
    if current_user.is_authenticated:
        chat_room = ChatRoom.query.filter_by(genre=genre).first()

        new_message = Message(
            content=msg,
            sender_id=current_user.id,
            chatroom_id=chat_room.id
        )
        
        db.session.add(new_message)
        db.session.commit()

        message = f"{current_user.id} in {genre}: {msg}"
        send(message, broadcast=True)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)