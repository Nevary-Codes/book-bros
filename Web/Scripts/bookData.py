import ast
import requests
from sqlalchemy import create_engine, MetaData, Table
import random
# API URL for Thriller books
DATABASE_URI = 'mysql+pymysql://root:aryan2424@localhost/book_bros'

def get_books_genre(genre = "thriller"):
    url = f"https://www.googleapis.com/books/v1/volumes?q=subject:{genre}&maxResults=40"

    # Fetch data from Google Books API
    response = requests.get(url)
    data = response.json()

    # Dictionary to store book details
    books = {}

    # Loop through each book item
    for index, item in enumerate(data.get("items", [])):
        volume_info = item.get("volumeInfo", {})
        
        # Extract book details
        title = volume_info.get("title", "No Title")
        authors = ", ".join(volume_info.get("authors", ["Unknown Author"]))
        description = volume_info.get("description", "No Description Available")
        thumbnail = volume_info.get("imageLinks", {}).get("smallThumbnail", "No Image")
        published_data = volume_info.get("publishedDate", "Unknown Published Date")
        publisher = volume_info.get("publisher", "No Publisher")

        # Store data in dictionary with index as key
        books[index] = {
            "title": title,
            "author": authors,
            "description": description,
            "thumbnail": thumbnail,
            "published_date": published_data,
            "publisher": publisher
        }
    return books

def get_books1(genre):
    engine = create_engine(DATABASE_URI)
    metadata = MetaData()

    books_table = Table('books', metadata, autoload_with=engine)

    with engine.connect() as connection:
        stmt = books_table.select()
        result = connection.execute(stmt).fetchall()

        books_dict = {}
        for book in result:
            book_id, title, author, _, description, genres, publisher, _, _, cover = book
            try:
                genre_list = [g.strip().lower() for g in ast.literal_eval(genres)]
            except Exception:
                genre_list = []

            if genre.lower() in genre_list:
                books_dict[book_id] = {
                    "title": title,
                    "author": author,
                    "description": description,
                    "thumbnail": cover,
                    "publisher": publisher
                }

        return books_dict

