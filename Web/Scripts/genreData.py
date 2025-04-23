from sqlalchemy import create_engine, MetaData, Table

DATABASE_URI = 'mysql+pymysql://root:aryan2424@localhost/book_bros'

def get_genres():
    engine = create_engine(DATABASE_URI)
    metadata = MetaData()

    genres_table = Table('genres', metadata, autoload_with=engine)

    with engine.connect() as connection:
        result = connection.execute(genres_table.select()).fetchall()

        genres_dict = {genre_id: (genre_name, genre_img) for genre_id, genre_name, genre_img in result}

        return genres_dict


