import pandas as pd
from sqlalchemy import create_engine, MetaData, Table
import random

DATABASE_URI = 'mysql+pymysql://root:aryan2424@localhost/book_bros'

def get_authors():
    engine = create_engine(DATABASE_URI)
    metadata = MetaData()

    authors_table = Table('author', metadata, autoload_with=engine)

    with engine.connect() as connection:
        stmt = authors_table.select().where(authors_table.c.is_verified == True)
        result = connection.execute(stmt).fetchall()

        authors_list = [(name, email, image) for name, email, image, _, _ in result]
        random.shuffle(authors_list)  # Shuffle the authors

        authors_dict = {index + 1: author for index, author in enumerate(authors_list)}

        return authors_dict
        