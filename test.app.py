import streamlit as st
import requests
import base64


# Google Books API Key
API_KEY = "AIzaSyCR0ngXFex4uVhkcE07WYQVylRlHqRM-lE"

# Function to fetch books from the Google Books API
def fetch_books(query, max_price=None, min_rating=0):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&langRestrict=en&key={API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        st.error(f"Error fetching books: {response.status_code}")
        return []
    
    data = response.json()
    books = []

    if "items" in data:
        for item in data["items"]:
            volume_info = item.get("volumeInfo", {})
            sale_info = item.get("saleInfo", {})
            price_info = sale_info.get("retailPrice", {})
            rating = volume_info.get("averageRating", 0)
            ratings_count = volume_info.get("ratingsCount", 0)
            price = price_info.get("amount", None)
            currency = price_info.get("currencyCode", "")

            # Apply rating and price filters
            if (rating >= min_rating) and (max_price is None or (price is not None and price <= max_price)):
                books.append({
                    "title": volume_info.get("title", "Unknown Title"),
                    "authors": volume_info.get("authors", ["Unknown"]),
                    "description": volume_info.get("description", "No description available."),
                    "categories": volume_info.get("categories", ["Unknown category"]),
                    "average_rating": rating,
                    "ratings_count": ratings_count,
                    "price": f"{price} {currency}" if price else "Not for sale",
                    "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", None),
                })

    return books[:10]  # Return top 10 results


def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string

encoded_image = get_base64_image("Assets/background.jpg")

# Background
page_bg_img = f'''
<style>
.stApp {{
    background-image: url("data:image/jpg;base64,{encoded_image}");
    background-size: cover;
    background-position: center;
}}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)

# Streamlit App
st.title("Tale Finder")
st.write("Find your next favorite book based on genre or similar interests!")

# User filters
liked_book = st.text_input("Enter a book you liked (optional):")
genre = st.text_input("Enter a genre you like (e.g., Fiction, Romance, Science):")
max_price = st.number_input("Maximum Price (optional):", min_value=0.0, value=50.0)
min_rating = st.slider("Minimum Rating (out of 5):", min_value=0.0, max_value=5.0, value=3.0)

# Checkbox to apply additional filters
if st.checkbox("Apply advanced filters"):
    year = st.slider("Year Published (optional):", min_value=1900, max_value=2024, value=(2000, 2024))
    st.write(f"Filtering books published between {year[0]} and {year[1]}")
    year_range = st.slider("Select publication year range:", 1900, 2024, (2000, 2024))
    st.write(f"Filtering books published between {year_range[0]} and {year_range[1]}")
    
favorite_author = st.selectbox(
    "Choose your favorite author (optional):",
    ["", "J.K. Rowling", "George R.R. Martin", "J.R.R. Tolkien", "Agatha Christie", "Stephen King"]
)
if favorite_author:
    st.write(f"Showing recommendations from {favorite_author}'s work...")

sort_option = st.radio(
    "How would you like to sort the recommendations?",
    ("Highest Rated", "Lowest Price", "Most Recent")
)
st.write(f"Recommendations sorted by: {sort_option}")



if st.button("Get Recommendations"):
    query = ""
    if liked_book:
        query = liked_book
    elif genre:
        query = f"subject:{genre}"
    else:
        st.error("Please enter a book you liked or a genre.")
        st.stop()
    
        # Loading spinner
    with st.spinner('Fetching your book recommendations...'):
        # Fetch books based on filters
        books = fetch_books(query, max_price=max_price, min_rating=min_rating)

    # Display books
    if books:
        for book in books:
            st.subheader(book["title"])
            st.write(f"**Authors:** {', '.join(book['authors'])}")
            st.write(f"**Categories:** {', '.join(book['categories'])}")
            st.write(f"**Description:** {book['description']}")
            st.write(f"**Average Rating:** {book['average_rating']} (from {book['ratings_count']} ratings)")
            st.write(f"**Price:** {book['price']}")
            if book["thumbnail"]:
                st.image(book["thumbnail"], width=150)
            st.write("---")
            # Allows user to rate the book
            user_rating = st.slider(f"Rate '{book['title']}' (out of 5):", min_value=0.0, max_value=5.0, key=book["title"])
            st.write(f"Your rating: {user_rating}")
    else:
        st.warning("No books found matching your criteria. Try adjusting the filters.")


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
