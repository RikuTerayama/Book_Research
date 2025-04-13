import requests

def search_books_on_google(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    results = response.json()
    return results.get("items", [])
