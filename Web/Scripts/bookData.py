import requests

# API URL for Thriller books

def get_books(genre = "thriller"):
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