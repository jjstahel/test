import streamlit as st
import requests

# API-Key festlegen
API_KEY = "AIzaSyDoQz8vEcuINx70zzQYLg5VTZLVel7qHsE"

# Funktion, um Daten von der Google Books API abzurufen
def fetch_books(query, genre_filter, default_query=False):
    country = "DE"  # Standortparameter

    # Wenn kein Suchbegriff eingegeben wurde, verwenden wir den Genrefilter als Standard-Query
    if default_query and genre_filter != "Alle Genres":
        query = f"subject:{genre_filter}"

    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&key={API_KEY}&country={country}"
    response = requests.get(url)

    if response.status_code == 200:
        books = response.json().get('items', [])
        # Sortierung nach Bewertung
        return sorted(
            books,
            key=lambda b: b.get('volumeInfo', {}).get('averageRating', 0),
            reverse=True
        )
    else:
        st.error(f"Fehler beim Abrufen der Daten: {response.status_code}")
        try:
            error_details = response.json()
            st.json(error_details)
        except ValueError:
            st.write("Keine zusätzliche Fehlermeldung verfügbar.")
        return []

# Funktion, um Buchdetails zu extrahieren
def extract_book_info(book):
    volume_info = book.get('volumeInfo', {})
    sale_info = book.get('saleInfo', {})
    
    title = volume_info.get('title', 'Nicht verfügbar')
    authors = ", ".join(volume_info.get('authors', ['Nicht verfügbar']))
    categories = ", ".join(volume_info.get('categories', ['Nicht verfügbar']))
    price = sale_info.get('retailPrice', {}).get('amount', 'Nicht verfügbar')
    currency = sale_info.get('retailPrice', {}).get('currencyCode', '')
    average_rating = volume_info.get('averageRating', 'Nicht bewertet')
    thumbnail = volume_info.get('imageLinks', {}).get('thumbnail', None)
    
    if price != 'Nicht verfügbar':
        price = f"{price} {currency}"
    
    return {
        "title": title,
        "authors": authors,
        "categories": categories,
        "price": price,
        "average_rating": average_rating,
        "thumbnail": thumbnail
    }

# Streamlit App Layout
st.title("Büchervorschläge mit Google Books API")
st.markdown("Wähle ein Genre aus der Sidebar, um die besten Bücher dieses Genres zu sehen!")

# Sidebar für Genres
genres = ["Fiction", "Romance", "Science", "Mystery", "History", "Fantasy", "Biography"]
selected_genre = st.sidebar.radio("Wähle ein Genre", genres)

# Bücher für das ausgewählte Genre abrufen
books = fetch_books(query="", genre_filter=selected_genre, default_query=True)

# Ergebnisse anzeigen
if not books:
    st.info("Keine Ergebnisse gefunden. Versuche ein anderes Genre.")
else:
    st.subheader(f"Beste Bücher aus dem Genre: {selected_genre}")
    for book in books:
        info = extract_book_info(book)
        st.markdown(f"### {info['title']}")
        st.markdown(f"**Autor(en):** {info['authors']}")
        st.markdown(f"**Genre:** {info['categories']}")
        st.markdown(f"**Preis:** {info['price']}")
        st.markdown(f"**Bewertung:** {info['average_rating']}")
        if info['thumbnail']:
            st.image(info['thumbnail'], width=150)
        st.markdown("---")
