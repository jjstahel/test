import streamlit as st
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from urllib.parse import quote  #import the URL encoding
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

#insert the API key
API_KEY = "AIzaSyDoQz8vEcuINx70zzQYLg5VTZLVel7qHsE"

#if the user has not rated books yet, then a dictionary is opened for them and new ratings will be inserted there
if "user_ratings" not in st.session_state:
    st.session_state.user_ratings = {}

#get the books from the Google API
def fetch_books(query, genre_filter, price_min, price_max, default_query=False):
    country = "US"  #keep the location to the US to only give books in English. Our Google accounts are in German, so this was necessary
    if default_query:
        query = f"subject:{genre_filter}" if genre_filter != "All Genres" else "subject:fiction"
    
    #URL encode query to avoid issues with special characters
    query = quote(query)
    
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=40&key={API_KEY}&country={country}"
    response = requests.get(url)
    
    if response.status_code == 200:
        books = response.json().get("items", [])
        filtered_books = [
            book for book in books
            if filter_genre(book, genre_filter) and filter_price(book, price_min, price_max)
        ]
        return sorted(filtered_books, key=lambda b: b.get("volumeInfo", {}).get("averageRating", 0), reverse=True)
    else:
        st.error(f"Error fetching data: {response.status_code}")
        try:
            error_details = response.json()
            st.json(error_details)
        except ValueError:
            st.write("No additional error details available.")
        return []

#filter the books by genere. Romance and Fantasy are included in Fiction 
def filter_genre(book, genre_filter):
    if genre_filter == "All Genres":
        return True
    volume_info = book.get("volumeInfo", {})
    categories = volume_info.get("categories", ["Unknown"])
    for category in categories:
        if genre_filter.lower() in category.lower():
            return True
    return False

#the books are filtered by price 
def filter_price(book, price_min, price_max):
    sale_info = book.get("saleInfo", {})
    retail_price = sale_info.get("retailPrice")
    if not retail_price or "amount" not in retail_price:
        return True  #also give books that do not have a price. Just show them without a price 
    price = retail_price["amount"]
    return price_min <= price <= price_max

#give informations about the books such as the title, the author and the price 
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

#the rated books are then saved and new books are recommended based on them 
def recommend_books_based_on_ratings (books, user_ratings):
    book_data = []
    for book in books: 
        info = extract_book_info (book)
        book_data.append ({
            "title":info["title"],
            "authors":info["authors"],
            "categories":info["categories"],
            "average_rating":info["average_rating"],
            "user_rating":user_ratings.get(info["title"], None),
        })
    df = pd.DataFrame(book_data)
    if df.empty:
        return []
    rated_books = df[df["user_rating"].notnull()]
    if rated_books.empty:
        return []
    df["features"]=df["authors"]+" "+ df["categories"]
    tfidf=TfidfVectorizer(stop_words="english")
    tfidf_matrix=tfidf.fit_transform(df["features"])
    similarity_matrix=cosine_similarity(tfidf_matrix, tfidf_matrix)
    recommendations = []
    for _, rated_book in rated_books.iterrows():
        book_index = df.index [df["title"] == rated_book ["title"]].tolist()[0]
        similar_books = list(enumerate(similarity_matrix[book_index]))
        similar_books = sorted(similar_books, key=lambda x: x[1], reverse=True)
        for idx, _ in similar_books[1:6]:
            if df.iloc [idx]["title"] not in rated_books ["title"].values:
                recommendations.append(df.iloc[idx])
    recommendations_df = pd.DataFrame(recommendations).drop_duplicates (subset="title")
    return recommendations_df.to_dict(orient="records")

#the website can switch between dark and light mode
def set_theme(theme):
    if theme == "Dark":
        st.markdown(
            """
            <style>
            /* Main app styling */
            body, .stApp {
                background-color: #1e1e1e;
                color: white;
            }

            /* Ensure text in main section is white */
            .stApp div, .stApp span, .stApp p, .stApp h1, .stApp h2, .stApp h3 {
                color: white !important;
            }

            /* Sidebar styling */
            section[data-testid="stSidebar"] {
                background-color: #2c2c2c !important;
                color: white;
            }
            section[data-testid="stSidebar"] .css-17eq0hr {
                color: white;
            }

            /* Sidebar header and text */
            section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {
                color: white !important;
            }

            /* Sidebar buttons and inputs */
            section[data-testid="stSidebar"] button, section[data-testid="stSidebar"] input, 
            section[data-testid="stSidebar"] select, section[data-testid="stSidebar"] textarea {
                background-color: #444;
                border: 1px solid #666;
            }

            /* Sidebar buttons' text color specifically set */
            section[data-testid="stSidebar"] button div {
                color: black !important; /* Ensures button text remains black */
            }

            section[data-testid="stSidebar"] button:hover {
                background-color: #555;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    elif theme == "Light":
        st.markdown(
            """
            <style>
            /* Main app styling */
            body, .stApp {
                background-color: #ffffff;
                color: black;
            }

            /* Ensure text in main section is black */
            .stApp div, .stApp span, .stApp p, .stApp h1, .stApp h2, .stApp h3 {
                color: black !important;
            }

            /* Sidebar styling */
            section[data-testid="stSidebar"] {
                background-color: #f5f5f5 !important;
                color: black;
            }
            section[data-testid="stSidebar"] .css-17eq0hr {
                color: black;
            }

            /* Sidebar header and text */
            section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {
                color: black !important;
            }

            /* Sidebar buttons and inputs */
            section[data-testid="stSidebar"] button, section[data-testid="stSidebar"] input, 
            section[data-testid="stSidebar"] select, section[data-testid="stSidebar"] textarea {
                background-color: #fff;
                color: black;
                border: 1px solid #ccc;
            }

            section[data-testid="stSidebar"] button:hover {
                background-color: #eee;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

#the app layout with the title 
st.title("Tale Finder")
st.markdown("Rate a book you read, and get recommendations what to read next!")

#Sidebar design with the theme
st.sidebar.title("Discover Top Books")
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"]) #theme determination 
set_theme(theme) #set the selected theme

#set the sidebars for generes
genres_sidebar = [
    "All Genres", "Fiction", "Science", 
    "Mystery", "History", "Biography"
]
selected_genre = st.sidebar.radio("Select a genre:", genres_sidebar)

#show the top books in the sidebar 
if selected_genre != "All Genres":
    st.sidebar.subheader(f"Top books in {selected_genre}")
    sidebar_books = fetch_books("", selected_genre, 0, 100, default_query=True)
    for book in sidebar_books[:5]: #show the top 5 books in the sidebar
        info = extract_book_info(book)
        st.sidebar.markdown(f"**{info['title']}**")
        st.sidebar.markdown(f"by {info['authors']}")
        st.sidebar.markdown(f"Rating: {info['average_rating']}")
        st.sidebar.markdown("---")

st.sidebar.title("Navigate")
page = st.sidebar.selectbox("Go to", ["Book Recommendations", "My Ratings and Visualizations"])

#this displays the main page with the search bar etc. 
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

    if st.button("Rate books"):
        default_query = query.strip() == ""
        books = fetch_books(query, genre_filter, price_min, price_max, default_query=default_query)
        st.session_state.books = books  #the user ratings are saved in the dictionary 
    else:
        books = st.session_state.get("books", [])
        
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
            
            #have a slider bar to rate the books from 1 to 5  
            current_rating = st.session_state.user_ratings.get(info['title'], 3)  #if no rating was manually given, set it to 3 as a default 
            rating = st.slider(
                f"Rate '{info['title']}'", 
                1, 5, value=current_rating, 
                key=f"slider_{info['title']}"
            )

            #have a button to save the rating into the dictionary                  
            if st.button(f"Save rating for '{info['title']}'", key=f"save_{info['title']}"):
                st.session_state.user_ratings[info['title']] = rating
                st.success(f"Rating for '{info['title']}' saved!")
            st.markdown("---")

elif page == "My Ratings and Visualizations":
    st.title("My Ratings and Genre Insights")

    if not st.session_state.user_ratings:
        st.info("No ratings available. Go to 'Book Recommendations' and rate books to see insights.")
    else:
        st.subheader("Ratings Distribution")

        #visualization through creating a histogram from the ratings  
        ratings = list(st.session_state.user_ratings.values())
        plt.figure(figsize=(8, 4))
        sns.histplot(ratings, bins=5, kde=False, color="blue")
        plt.title("Your Ratings Distribution")
        plt.xlabel("Ratings")
        plt.ylabel("Frequency")
        st.pyplot(plt)

        st.subheader("Ratings Table")
        rated_books = [
            {"Title": title, "Rating": rating}
            for title, rating in st.session_state.user_ratings.items()
        ]
        st.table(rated_books)

        #create content-based recommendations based on the ratings of past read books 
        st.subheader ("New Recommendations Based on Your Ratings")
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
