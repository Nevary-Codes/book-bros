from sqlalchemy import create_engine, MetaData, Table
import random

DATABASE_URI = 'mysql+pymysql://root:aryan2424@localhost/book_bros'


def get_books():
    engine = create_engine(DATABASE_URI)
    metadata = MetaData()

    books_table = Table('book', metadata, autoload_with=engine)

    with engine.connect() as connection:
        stmt = books_table.select().where(books_table.c.is_verified == True)
        result = connection.execute(stmt).fetchall()

        books_list = [(book_id, title, author, cover, is_verified) for book_id, title, _, author, cover, _, _, is_verified in result]
        
        random.shuffle(books_list)  # Shuffle the list randomly

        books_dict = {book[0]: (book[1], book[2], book[3]) for book in books_list}

        return books_dict