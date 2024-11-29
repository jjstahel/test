import streamlit as st
import requests

# API key
API_KEY = "AIzaSyDoQz8vEcuINx70zzQYLg5VTZLVel7qHsE"

# Function to fetch books from Google Books API
def fetch_books(query, genre_filter, price_min, price_max, default_query=False):
    country = "US"  # Location parameter

    # Use genre filter as default query if no search term is provided
    if default_query and genre_filter != "All Genres":
        query = f"subject:{genre_filter}"

    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&key={API_KEY}&country={country}"
    response = requests.get(url)

    if response.status_code == 200:
        books = response.json().get('items', [])
        # Filter and sort books
        filtered_books = [
            book for book in books
            if filter_genre(book, genre_filter) and filter_price(book, price_min, price_max)
        ]
        return sorted(filtered_books, key=lambda b: b.get('volumeInfo', {}).get('averageRating', 0), reverse=True)
    else:
        st.error(f"Error fetching data: {response.status_code}")
        try:
            error_details = response.json()
            st.json(error_details)
        except ValueError:
            st.write("No additional error details available.")
        return []

# Function to filter books by genre
def filter_genre(book, genre_filter):
    if genre_filter == "All Genres":
        return True  # No filter active
    volume_info = book.get('volumeInfo', {})
    categories = volume_info.get('categories', [])
    for category in categories:
        if genre_filter.lower() in category.lower():
            return True
    return False

# Function to filter books by price
def filter_price(book, price_min, price_max):
    sale_info = book.get('saleInfo', {})
    price = sale_info.get('retailPrice', {}).get('amount', None)
    # Do not exclude books without a price
    if price is None:
        return True
    # Check if price falls within range
    return price_min <= price <= price_max

# Function to extract book details
def extract_book_info(book):
    volume_info = book.get('volumeInfo', {})
    sale_info = book.get('saleInfo', {})
    
    title = volume_info.get('title', 'Not available')
    authors = ", ".join(volume_info.get('authors', ['Not available']))
    categories = ", ".join(volume_info.get('categories', ['Not available']))
    price = sale_info.get('retailPrice', {}).get('amount', 'Not available')
    currency = sale_info.get('retailPrice', {}).get('currencyCode', '')
    average_rating = volume_info.get('averageRating', 'Not rated')
    thumbnail = volume_info.get('imageLinks', {}).get('thumbnail', None)
    
    if price != 'Not available':
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
st.title("Tale Finder")  # Updated title
st.markdown("Enter a book or author you liked, and get recommendations!")

# Sidebar for genre selection
st.sidebar.title("Discover Top Books")
genres_sidebar = [
    "All Genres", "Fiction", "Romance", "Science", 
    "Mystery", "History", "Fantasy", "Biography"
]
selected_genre = st.sidebar.radio("Select a genre:", genres_sidebar)

# Display books in the selected genre
if selected_genre != "All Genres":
    st.sidebar.subheader(f"Top books in {selected_genre}")
    sidebar_books = fetch_books("", selected_genre, 0, 100, default_query=True)
    for book in sidebar_books[:5]:  # Show top 5 books in the sidebar
        info = extract_book_info(book)
        st.sidebar.markdown(f"**{info['title']}**")
        st.sidebar.markdown(f"by {info['authors']}")
        st.sidebar.markdown(f"Rating: {info['average_rating']}")
        st.sidebar.markdown("---")

# Main section for search functionality
st.subheader("Search for books")
query = st.text_input("Search term (e.g., a book or author)", "")

# Genre filter
genres = [
    "All Genres", "Fiction", "Romance", "Science", 
    "Mystery", "History", "Fantasy", "Biography"
]
genre_filter = st.selectbox("Filter by genre", genres)

# Price filter
st.markdown("Filter by price:")
price_min, price_max = st.slider("Select price range (in USD)", 0, 100, (0, 100))

# Search button
if st.button("Show recommendations"):
    # Use default query if no search term is provided
    default_query = query.strip() == ""
    books = fetch_books(query, genre_filter, price_min, price_max, default_query=default_query)

    if not books:
        st.info("No results found. Try another search term or adjust the filters.")
    else:
        st.subheader("Recommendations")
        for book in books:
            info = extract_book_info(book)
            st.markdown(f"### {info['title']}")
            st.markdown(f"**Author(s):** {info['authors']}")
            st.markdown(f"**Genre:** {info['categories']}")
            st.markdown(f"**Price:** {info['price']}")
            st.markdown(f"**Rating:** {info['average_rating']}")
            if info['thumbnail']:
                st.image(info['thumbnail'], width=150)
            st.markdown("---")
