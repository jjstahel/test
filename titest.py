import streamlit as st
import requests
import matplotlib.pyplot as plt
from urllib.parse import quote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# API key
API_KEY = "AIzaSyDoQz8vEcuINx70zzQYLg5VTZLVel7qHsE"

# Initialize session state for books and ratings if not already set
if "user_ratings" not in st.session_state:
    st.session_state.user_ratings = {}

if "books" not in st.session_state:
    st.session_state.books = []

# Function to fetch books from Google Books API
def fetch_books(query, genre_filter, price_min, price_max, default_query=False):
    country = "US"
    if default_query:
        query = f"subject:{genre_filter}" if genre_filter != "All Genres" else "subject:fiction"
    query = quote(query)
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&key={API_KEY}&country={country}"
    response = requests.get(url)
    if response.status_code == 200:
        books = response.json().get("items", [])
        return [
            book for book in books
            if filter_genre(book, genre_filter) and filter_price(book, price_min, price_max)
        ]
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return []

# Function to filter books by genre
def filter_genre(book, genre_filter):
    if genre_filter == "All Genres":
        return True
    volume_info = book.get("volumeInfo", {})
    categories = volume_info.get("categories", ["Unknown"])
    for category in categories:
        if genre_filter.lower() in category.lower():
            return True
    return False

# Function to filter books by price
def filter_price(book, price_min, price_max):
    sale_info = book.get("saleInfo", {})
    retail_price = sale_info.get("retailPrice")
    if not retail_price or "amount" not in retail_price:
        return True
    price = retail_price["amount"]
    return price_min <= price <= price_max

# Function to extract book details
def extract_book_info(book):
    volume_info = book.get("volumeInfo", {})
    sale_info = book.get("saleInfo", {})
    title = volume_info.get("title", "Not available")
    authors = ", ".join(volume_info.get("authors", ["Not available"]))
    categories = ", ".join(volume_info.get("categories", ["Not available"]))
    price = sale_info.get("retailPrice", {}).get("amount", "Not available")
    currency = sale_info.get("retailPrice", {}).get("currencyCode", "")
    average_rating = volume_info.get("averageRating", "Not rated")
    thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", None)
    user_rating = st.session_state.user_ratings.get(title, "Not rated yet")
    if price != "Not available":
        price = f"{price} {currency}"
    return {
        "title": title,
        "authors": authors,
        "categories": categories,
        "price": price,
        "average_rating": average_rating,
        "thumbnail": thumbnail,
        "user_rating": user_rating,
    }

# Function to recommend books based on user ratings
def recommend_books_based_on_ratings(books, user_ratings):
    book_data = []
    for book in books:
        info = extract_book_info(book)
        book_data.append({
            "title": info["title"],
            "authors": info["authors"],
            "categories": info["categories"],
            "average_rating": info["average_rating"],
            "user_rating": user_ratings.get(info["title"], None),
        })
    df = pd.DataFrame(book_data)
    if df.empty:
        return []
    rated_books = df[df["user_rating"].notnull()]
    if rated_books.empty:
        return []
    df["features"] = df["authors"] + " " + df["categories"]
    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(df["features"])
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    recommendations = []
    for _, rated_book in rated_books.iterrows():
        book_index = df.index[df["title"] == rated_book["title"]].tolist()[0]
        similar_books = list(enumerate(similarity_matrix[book_index]))
        similar_books = sorted(similar_books, key=lambda x: x[1], reverse=True)
        for idx, _ in similar_books[1:6]:
            if df.iloc[idx]["title"] not in rated_books["title"].values:
                recommendations.append(df.iloc[idx])
    recommendations_df = pd.DataFrame(recommendations).drop_duplicates(subset="title")
    return recommendations_df.to_dict(orient="records")

# Streamlit App Layout
st.title("Tale Finder")
st.markdown("Enter a book or author you liked, and get recommendations!")

# Sidebar for navigation
st.sidebar.title("Discover Top Books")
genres_sidebar = [
    "All Genres", "Fiction", "Science", 
    "Mystery", "History", "Biography"
]
selected_genre = st.sidebar.radio("Select a genre:", genres_sidebar)

# Display top books in sidebar
if selected_genre != "All Genres":
    st.sidebar.subheader(f"Top books in {selected_genre}")
    sidebar_books = fetch_books("", selected_genre, 0, 100, default_query=True)
    for book in sidebar_books[:5]:  # Show top 5 books in the sidebar
        info = extract_book_info(book)
        st.sidebar.markdown(f"**{info['title']}**")
        st.sidebar.markdown(f"by {info['authors']}")
        st.sidebar.markdown(f"Rating: {info['average_rating']}")
        st.sidebar.markdown("---")

st.sidebar.title("Navigate")
page = st.sidebar.selectbox("Go to", ["Book Recommendations", "My Ratings and Visualizations"])

# Main section
if page == "Book Recommendations":
    st.subheader("Search for books")
    query = st.text_input("Search term (e.g., a book or author)", "")
    genres = [
        "All Genres", "Fiction", "Science", 
        "Mystery", "History", "Biography"
    ]
    genre_filter = st.selectbox("Filter by genre", genres)
    st.markdown("Filter by price:")
    price_min, price_max = st.slider("Select price range (in USD)", 0, 100, (0, 100))

    if st.button("Show recommendations"):
        default_query = query.strip() == ""
        # Reset book results for new searches
        st.session_state.books = fetch_books(query, genre_filter, price_min, price_max, default_query=default_query)
    
    books = st.session_state.books

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
            
            # Display slider to rate the book 
            current_rating = st.session_state.user_ratings.get(info['title'], 3)  # Default to 3 if no rating
            rating = st.slider(
                f"Rate '{info['title']}'", 
                1, 5, value=current_rating, 
                key=f"slider_{info['title']}"
            )

            # Button to save rating                   
            if st.button(f"Save rating for '{info['title']}'", key=f"save_{info['title']}"):
                st.session_state.user_ratings[info['title']] = rating
                st.success(f"Rating for '{info['title']}' saved!")
            st.markdown("---")

elif page == "My Ratings and Visualizations":
    st.title("My Ratings and Genre Insights")

    if not st.session_state.user_ratings:
        st.info("No ratings available. Go to 'Book Recommendations' and rate books to see insights.")
    else:
        # Collect book data with ratings and genres
        rated_books = []
        for book in st.session_state.books:
            info = extract_book_info(book)
            if info["title"] in st.session_state.user_ratings:
                rated_books.append({
                    "Title": info["title"],
                    "Rating": st.session_state.user_ratings[info["title"]],
                    "Genre": info["categories"],
                })

        df = pd.DataFrame(rated_books)
        if df.empty:
            st.info("No genres found for rated books.")
        else:
            # Calculate average rating per genre
            df["Genre"] = df["Genre"].str.split(", ")  # Split multiple genres
            exploded_df = df.explode("Genre")  # Handle multiple genres per book
            genre_avg_ratings = (
                exploded_df.groupby("Genre")["Rating"].mean().sort_values(ascending=False)
            )

            # Bar chart of average ratings by genre
            st.subheader("Average Ratings by Genre")
            plt.figure(figsize=(10, 5))
            genre_avg_ratings.plot(kind="bar")
            plt.title("Average Ratings by Genre")
            plt.xlabel("Genre")
            plt.ylabel("Average Rating")
            st.pyplot(plt)

        st.subheader("Ratings Table")
        st.table(df)

        # Content-based Recommendations
        st.subheader("New Recommendations Based on Your Ratings")
        if "books" in st.session_state and st.session_state.user_ratings:
            recommendations = recommend_books_based_on_ratings(
                st.session_state.books,
                st.session_state.user_ratings,
            )
            if recommendations:
                st.markdown("Here are some books you might like:")
                for rec in recommendations:
                    st.markdown(f"### {rec['title']}")
                    st.markdown(f"**Author(s):** {rec['authors']}")
                    st.markdown(f"**Genre:** {rec['categories']}")
                    st.markdown(f"**Rating:** {rec['average_rating']}")
                    st.markdown("---")
            else:
                st.info("No recommendations available yet. Rate more books to get personalized recommendations!")
        else:
            st.info("No recommendations available. Ensure you have rated books and fetched books from the API.")
