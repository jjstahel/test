import streamlit as st
import requests

# API-Key festlegen
API_KEY = "AIzaSyDoQz8vEcuINx70zzQYLg5VTZLVel7qHsE"

# Funktion, um Daten von der Google Books API abzurufen
def fetch_books(query, genre_filter, price_min, price_max):
    country = "DE"  # Standortparameter
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&key={API_KEY}&country={country}"
    response = requests.get(url)
    if response.status_code == 200:
        books = response.json().get('items', [])
        # Bücher filtern
        return [
            book for book in books
            if filter_genre(book, genre_filter) and filter_price(book, price_min, price_max)
        ]
    else:
        st.error(f"Fehler beim Abrufen der Daten: {response.status_code}")
        try:
            error_details = response.json()
            st.json(error_details)
        except ValueError:
            st.write("Keine zusätzliche Fehlermeldung verfügbar.")
        return []

# Funktion, um Genre zu filtern
def filter_genre(book, genre_filter):
    if genre_filter == "Alle Genres":
        return True  # Kein Filter aktiv
    volume_info = book.get('volumeInfo', {})
    categories = volume_info.get('categories', [])
    for category in categories:
        if genre_filter.lower() in category.lower():
            return True
    return False

# Funktion, um Preis zu filtern
def filter_price(book, price_min, price_max):
    sale_info = book.get('saleInfo', {})
    price = sale_info.get('retailPrice', {}).get('amount', None)
    # Bücher ohne Preis werden nicht ausgeschlossen
    if price is None:
        return True
    # Preisprüfung nur für Bücher mit Preisinformationen
    return price_min <= price <= price_max

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
st.markdown("Gib ein Buch oder einen Autor ein, der dir gefallen hat, und erhalte Vorschläge!")

# Eingabe durch den Nutzer
query = st.text_input("Suchbegriff (z.B. ein Buch oder Autor)", "")

# Filter für Genre
genres = [
    "Alle Genres", "Fiction", "Romance", "Science", 
    "Mystery", "History", "Fantasy", "Biography"
]
genre_filter = st.selectbox("Filter nach Genre", genres)

# Filter für Preis
st.markdown("Filter nach Preis:")
price_min, price_max = st.slider("Preisspanne auswählen (in EUR)", 0, 100, (0, 100))

# Button für Suche
if st.button("Vorschläge anzeigen"):
    if not query:
        st.warning("Bitte gib einen Suchbegriff ein.")
    else:
        books = fetch_books(query, genre_filter, price_min, price_max)
        
        if not books:
            st.info("Keine Ergebnisse gefunden. Versuche es mit einem anderen Suchbegriff oder ändere die Filter.")
        else:
            st.subheader("Vorschläge")
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
