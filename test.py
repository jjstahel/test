import streamlit as st
import requests

API_KEY = "AIzaSyDoQz8vEcuINx70zzQYLg5VTZLVel7qHsE"

def fetch_books(query):
    country = "DE"  # Standortparameter für Deutschland
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=10&key={API_KEY}&country={country}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        st.error(f"Fehler beim Abrufen der Daten: {response.status_code}")
        try:
            error_details = response.json()
            st.json(error_details)
        except ValueError:
            st.write("Keine zusätzliche Fehlermeldung verfügbar.")
        return []

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

st.title("Büchervorschläge mit Google Books API")
st.markdown("Gib ein Buch oder einen Autor ein, der dir gefallen hat, und erhalte Vorschläge!")

query = st.text_input("Suchbegriff (z.B. ein Buch oder Autor)", "")

if st.button("Vorschläge anzeigen"):
    if not query:
        st.warning("Bitte gib einen Suchbegriff ein.")
    else:
        books = fetch_books(query)
        
        if not books:
            st.info("Keine Ergebnisse gefunden. Versuche es mit einem anderen Suchbegriff.")
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



# Quick Search
st.sidebar.subheader("Quick Book Search")
search_query = st.sidebar.text_input("Search for a book title or author:")

if search_query:
    with st.spinner("Searching..."):
        search_results = fetch_books(search_query)
        if search_results:
            st.sidebar.write("Search Results:")
            for result in search_results:
                st.sidebar.write(result["title"])
        else:
            st.sidebar.write("No results found.")


# List of genres and their respective subgenres
genres_and_subgenres = {
    "Fiction": ["Historical Fiction", "Science Fiction", "Fantasy", "Literary Fiction"],
    "Romance": ["Contemporary Romance", "Historical Romance", "Paranormal Romance", "Romantic Comedy"],
    "Science": ["Physics", "Biology", "Astronomy", "Chemistry", "Earth Science"],
    "Mystery": ["Cozy Mystery", "Crime Thriller", "Detective Fiction", "Noir"],
    "History": ["Ancient History", "Medieval History", "Modern History", "Military History"],
    "Fantasy": ["Epic Fantasy", "Urban Fantasy", "Dark Fantasy", "Sword and Sorcery"],
    "Biography": ["Memoir", "Autobiography", "Political Biography", "Celebrity Biography"]
}

# Always display the sidebar for navigation
st.sidebar.title("Navigation")
st.sidebar.write("Explore the world of genres, we're sure you'll find something!")

# Add genres and subgenres to the sidebar
st.sidebar.subheader("Browse Genres")
for genre, subgenres in genres_and_subgenres.items():
    with st.sidebar.expander(genre):
        for subgenre in subgenres:
            st.write(f"- {subgenre}")

# Quick metrics shown on sidebar
st.sidebar.title("Quick Stats")
st.sidebar.metric(label="Total Genres", value=len(genres_and_subgenres))
st.sidebar.metric(label="Average Rating Filter", value=min_rating)
