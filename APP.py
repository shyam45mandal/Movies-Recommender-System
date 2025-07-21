import streamlit as st
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor


def fetch_poster(movie_id):
    """Fetch poster URL using movie ID from TMDB API"""
    try:
        url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=1d62012d7d5fd2eebaaf97490dd07aa4&language=en-US'
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if 'poster_path' in data and data['poster_path']:
                return "https://image.tmdb.org/t/p/w500" + data['poster_path']
            else:
                return "https://via.placeholder.com/500x750?text=No+Poster+Available"
        else:
            return "https://via.placeholder.com/500x750?text=API+Error"

    except requests.exceptions.Timeout:
        return "https://via.placeholder.com/500x750?text=Timeout+Error"
    except Exception:
        return "https://via.placeholder.com/500x750?text=Error+Loading+Poster"


def recommend_and_display(movie, cols):
    """Get movie recommendations and display them as posters load"""
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    movie_ids = []

    for i in movies_list:
        movie_idx = i[0]
        movie_title = movies.iloc[movie_idx].title

        if 'movie_id' in movies.columns:
            movie_id = movies.iloc[movie_idx]['movie_id']
        elif 'id' in movies.columns:
            movie_id = movies.iloc[movie_idx]['id']
        else:
            movie_id = movies.iloc[movie_idx].name

        recommended_movies.append(movie_title)
        movie_ids.append(movie_id)

    image_placeholders = []
    title_placeholders = []

    for idx in range(5):
        with cols[idx]:
            image_placeholder = st.empty()
            title_placeholder = st.empty()
            image_placeholders.append(image_placeholder)
            title_placeholders.append(title_placeholder)

    def fetch_and_display_poster(args):
        movie_id, idx = args
        try:
            poster_url = fetch_poster(movie_id)
            return idx, poster_url
        except Exception:
            return idx, "https://via.placeholder.com/500x750?text=Failed+to+Load"

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for i in range(len(movie_ids)):
            future = executor.submit(fetch_and_display_poster, (movie_ids[i], i))
            futures[future] = i

        completed_posters = set()

        from concurrent.futures import as_completed
        for future in as_completed(futures, timeout=30):
            try:
                idx, poster_url = future.result()
                completed_posters.add(idx)
                with cols[idx]:
                    image_placeholders[idx].image(poster_url)
                    title_placeholders[idx].markdown(f"**{recommended_movies[idx]}**")
            except Exception:
                idx = futures[future]
                completed_posters.add(idx)
                with cols[idx]:
                    image_placeholders[idx].image("https://via.placeholder.com/500x750?text=Error")
                    title_placeholders[idx].markdown(f"**{recommended_movies[idx]}**")

        for i in range(len(movie_ids)):
            if i not in completed_posters:
                with cols[i]:
                    image_placeholders[i].image("https://via.placeholder.com/500x750?text=Timeout")
                    title_placeholders[i].markdown(f"**{recommended_movies[i]}**")

    return recommended_movies


# Load data files
try:
    movies = pickle.load(open('movies.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    movies_list = movies['title'].values
except FileNotFoundError as e:
    st.error(f"Required file not found: {e}")
    st.stop()

# Streamlit UI
st.title('🎬 Movie Recommender System')
st.markdown("### Find movies similar to your favorites!")

# Movie selection dropdown
selected_movie_name = st.selectbox(
    "Select a movie to get recommendations:",
    movies_list
)

# Recommendation button
if st.button("🔍 Get Recommendations", type="primary"):
    if selected_movie_name:
        try:
            st.markdown(f"**Movies similar to {selected_movie_name}:**")
            cols = st.columns(5)
            recommended_movies = recommend_and_display(selected_movie_name, cols)
        except Exception as e:
            st.error(f"Error getting recommendations: {e}")

# Sidebar dataset info
with st.sidebar:
    st.header("📊 Dataset Info")
    if 'movies' in locals():
        st.info(f"Total Movies: {len(movies)}")
