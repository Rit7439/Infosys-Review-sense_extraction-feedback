import streamlit as st
import requests
import os
import pandas as pd

# Simple session storage for logged-in user
if "auth_username" not in st.session_state:
    st.session_state["auth_username"] = None

st.set_page_config(page_title="Infosys Review Sense", page_icon="🧠", layout="wide")

# Modern UI theme
def apply_theme():
    st.markdown(
        """
        <style>
        /* App background */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #111827 50%, #1f2937 100%);
            color: #e5e7eb;
        }
        /* Main container */
        .block-container {
            padding-top: 3.5rem;
            padding-bottom: 2rem;
            max-width: 1100px;
        }
        /* Headings */
        h1, h2, h3, h4 { color: #f3f4f6 !important; }
        /* Sidebar */
        [data-testid="stSidebar"] > div {
            background: #0b1220;
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        /* Inputs */
        .stTextInput input, .stPassword input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            color: #e5e7eb;
        }
        .stTextInput input:focus, .stPassword input:focus, .stTextArea textarea:focus {
            outline: none;
            border-color: #60a5fa;
            box-shadow: 0 0 0 1px #60a5fa;
        }
        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, #2563eb, #7c3aed);
            color: white;
            border: none;
            padding: 0.6rem 1rem;
            border-radius: 10px;
            box-shadow: 0 10px 20px rgba(37,99,235,0.25);
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(124,58,237,0.25);
        }
        /* Cards */
        .card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.2rem 1rem;
            margin: 0.6rem 0 1.2rem 0;
        }
        .success-box { background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.35); }
        .error-box { background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.35); }
        /* Dataframe */
        .dataframe { background: rgba(255,255,255,0.04); }
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_theme()

st.markdown(
    "<div style='text-align:center;margin:16px 0 14px 0; overflow:visible;'>"
    "<div style='display:inline-block;padding:10px 16px;border-radius:999px;background:rgba(96,165,250,0.15);color:#bfdbfe;border:1px solid rgba(96,165,250,0.35);font-size:18px;line-height:1.25;white-space:nowrap;font-weight:600;'>Infosys Review Sense • Customer Feedback Intelligence</div>"
    "</div>",
    unsafe_allow_html=True,
)
st.markdown("<h1 style='text-align:center;margin:0;'>Insights from Customer Feedback</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;color:#9ca3af;margin:4px 0 20px 0;'>Extract themes, measure sentiment, and curate datasets to elevate customer experience</p>",
    unsafe_allow_html=True,
)

# Lightweight, dependency-free insight helpers
POSITIVE_WORDS = {"good","great","awesome","excellent","love","like","satisfied","happy","amazing","fantastic","smooth","fast"}
NEGATIVE_WORDS = {"bad","poor","terrible","hate","dislike","unsatisfied","unhappy","awful","slow","bug","issue","problem"}
STOPWORDS = {"the","a","an","and","or","of","to","in","on","for","is","it","this","that","with","was","were","are","be","have","has","had","you","we","they","i"}

def quick_sentiment(text: str) -> tuple[str, int]:
    tokens = [t.strip('.,!?;:"\'').lower() for t in text.split()]
    score = 0
    for t in tokens:
        if t in POSITIVE_WORDS:
            score += 1
        if t in NEGATIVE_WORDS:
            score -= 1
    label = "Neutral"
    if score > 0:
        label = "Positive"
    elif score < 0:
        label = "Negative"
    return label, score

def extract_keywords(text: str, top_k: int = 8) -> list[str]:
    freq = {}
    for raw in text.replace("\n"," ").split():
        w = raw.strip('.,!?;:"\'').lower()
        if not w or w in STOPWORDS or len(w) < 3:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]]
# Helper to safely read JSON or fallback to text
def get_error_detail(response):
    try:
        return response.json().get("detail", None)
    except Exception:
        return None

def get_message(response):
    try:
        return response.json().get("message", None)
    except Exception:
        return None


# Choose between Login, Register, Forgot Password, Profile
choice = st.sidebar.selectbox(
    "Select Option",
    ["Login", "Register", "Forgot Password", "Profile", "Datasets"],
)

# Backend URL
backend_url = "http://127.0.0.1:8000"

if choice == "Register":
    st.subheader("Create a New Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    full_name = st.text_input("Full Name (optional)")
    email = st.text_input("Email (optional)")
    if st.button("Register"):
        response = requests.post(
            f"{backend_url}/register",
            json={
                "username": username,
                "password": password,
                "full_name": full_name,
                "email": email,
            },
        )
        if response.status_code == 200:
            st.success(get_message(response) or "Registration successful! You can now log in.")
        else:
            detail = get_error_detail(response) or response.text or "Registration failed"
            st.error(f"{detail} (status {response.status_code})")

elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        response = requests.post(
            f"{backend_url}/login", json={"username": username, "password": password}
        )
        if response.status_code == 200:
            st.session_state["auth_username"] = username
            st.success(get_message(response) or "Login successful")
        else:
            detail = get_error_detail(response) or response.text or "Invalid credentials"
            st.error(f"{detail} (status {response.status_code})")

elif choice == "Forgot Password":
    st.subheader("Forgot Password")
    step = st.radio("Step", ["1) Email Token", "2) Reset Password"], index=0)

    if step.startswith("1"):
        st.caption("Enter your registered email to receive a reset token (valid 10 minutes)")
        fp_email = st.text_input("Registered Email")
        if st.button("Request reset token"):
            resp = requests.post(f"{backend_url}/forgot_password/request_token", json={"email": fp_email})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state["fp_token"] = data.get("reset_token")
                st.success("Reset token generated (valid 10 minutes). Proceed to step 2 to set a new password.")
                st.text_input("Token", value=st.session_state.get("fp_token"), disabled=True)
            else:
                detail = get_error_detail(resp) or resp.text or "Email not found"
                st.error(f"{detail} (status {resp.status_code})")

    else:
        token = st.session_state.get("fp_token")
        if not token:
            st.info("Please complete Step 1 first.")
        else:
            new_pwd = st.text_input("New Password", type="password")
            if st.button("Reset Password"):
                resp = requests.post(
                    f"{backend_url}/forgot_password/reset",
                    json={"token": token, "new_password": new_pwd},
                )
                if resp.status_code == 200:
                    st.success("Password reset successful. You can now log in.")
                    st.session_state.pop("fp_token", None)
                else:
                    detail = get_error_detail(resp) or resp.text or "Reset failed"
                    st.error(f"{detail} (status {resp.status_code})")

elif choice == "Profile":
    if not st.session_state.get("auth_username"):
        st.info("Please log in first.")
    else:
        st.subheader("Profile Management")
        username = st.session_state["auth_username"]
        prof = requests.get(f"{backend_url}/profile/{username}")
        if prof.status_code != 200:
            detail = get_error_detail(prof) or prof.text or "Failed to load profile"
            st.error(f"{detail} (status {prof.status_code})")
        else:
            data = prof.json()
            st.caption(f"Signed in as: {data.get('email')}")
            full_name = st.text_input("Full Name", value=data.get("full_name", ""))
            email = st.text_input("Email", value=data.get("email", ""))
            if st.button("Save Profile"):
                resp = requests.put(
                    f"{backend_url}/profile/{username}",
                    json={"full_name": full_name, "email": email},
                )
                if resp.status_code == 200:
                    st.success("Profile updated")
                else:
                    detail = get_error_detail(resp) or resp.text or "Update failed"
                    st.error(f"{detail} (status {resp.status_code})")

            st.markdown("---")
            st.subheader("Change Password")
            old_pw = st.text_input("Old Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            if st.button("Change Password"):
                resp = requests.post(
                    f"{backend_url}/change_password",
                    json={
                        "username": username,
                        "old_password": old_pw,
                        "new_password": new_pw,
                    },
                )
                if resp.status_code == 200:
                    st.success("Password changed")
                else:
                    detail = get_error_detail(resp) or resp.text or "Change failed"
                    st.error(f"{detail} (status {resp.status_code})")

            st.markdown("---")
            if st.button("Sign out"):
                st.session_state["auth_username"] = None
                st.success("Signed out")

elif choice == "Datasets":
    st.subheader("Datasets & Text Processing")
    
    # Stage 1: Text Preprocessing Pipeline Results
    st.markdown("### 🎯 Milestone 2: Text Preprocessing Pipeline")
    
    # Amazon Reviews Dataset
    preprocessed_file = os.path.join(os.path.dirname(__file__), "data", "preprocessed_reviews.csv")
    sentiment_file = os.path.join(os.path.dirname(__file__), "data", "preprocessed_sentiment_analysis.csv")
    
    tab1, tab2 = st.tabs(["📦 Amazon Reviews", "💬 Sentiment Analysis"])
    
    with tab1:
        st.markdown("#### Amazon Customer Reviews Dataset")
        if os.path.exists(preprocessed_file):
            st.success("✅ Amazon Reviews preprocessing completed!")
            st.info("📊 4,915 reviews processed and ready for sentiment analysis")
            
            # Load and display preprocessed data
            if st.button("View Amazon Reviews Data", key="view_amazon"):
                try:
                    df_preprocessed = pd.read_csv(preprocessed_file, nrows=100)
                    
                    st.markdown("##### Sample: Original vs Processed Text")
                    if 'reviewText' in df_preprocessed.columns and 'processed_text' in df_preprocessed.columns:
                        comparison_df = df_preprocessed[['reviewText', 'processed_text']].head(10)
                        st.dataframe(comparison_df, use_container_width=True, height=400)
                        
                        # Show statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Reviews", len(df_preprocessed))
                        with col2:
                            avg_original = df_preprocessed['reviewText'].str.len().mean()
                            st.metric("Avg Original Length", f"{avg_original:.0f} chars")
                        with col3:
                            avg_processed = df_preprocessed['processed_text'].str.len().mean()
                            st.metric("Avg Processed Length", f"{avg_processed:.0f} chars")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Amazon Reviews (CSV)",
                            data=open(preprocessed_file, 'rb').read(),
                            file_name="preprocessed_amazon_reviews.csv",
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Error loading data: {e}")
        else:
            st.warning("⚠️ Amazon reviews preprocessing not found.")
            if st.button("Run Amazon Reviews Preprocessing", key="run_amazon"):
                st.info("Execute: `python text_preprocessing.py`")
    
    with tab2:
        st.markdown("#### Sentiment Analysis Dataset")
        if os.path.exists(sentiment_file):
            st.success("✅ Sentiment Analysis preprocessing completed!")
            st.info("📊 96 sentiment-labeled texts processed")
            
            # Load and display preprocessed data
            if st.button("View Sentiment Analysis Data", key="view_sentiment"):
                try:
                    df_sentiment = pd.read_csv(sentiment_file, nrows=100)
                    
                    st.markdown("##### Sample: Original vs Processed Text")
                    if 'Text' in df_sentiment.columns and 'processed_text' in df_sentiment.columns:
                        comparison_df = df_sentiment[['Text', 'processed_text', 'Sentiment']].head(10)
                        st.dataframe(comparison_df, use_container_width=True, height=400)
                        
                        # Show statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Texts", len(df_sentiment))
                        with col2:
                            positive_count = (df_sentiment['Sentiment'] == 'Positive').sum() if 'Sentiment' in df_sentiment.columns else 0
                            st.metric("Positive", positive_count)
                        with col3:
                            negative_count = (df_sentiment['Sentiment'] == 'Negative').sum() if 'Sentiment' in df_sentiment.columns else 0
                            st.metric("Negative", negative_count)
                        with col4:
                            avg_processed = df_sentiment['processed_text'].str.len().mean()
                            st.metric("Avg Length", f"{avg_processed:.0f} chars")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Sentiment Analysis (CSV)",
                            data=open(sentiment_file, 'rb').read(),
                            file_name="preprocessed_sentiment_analysis.csv",
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Error loading data: {e}")
        else:
            st.warning("⚠️ Sentiment analysis preprocessing not found.")
            if st.button("Run Sentiment Preprocessing", key="run_sentiment"):
                st.info("Execute: `python preprocess_sentiment_data.py`")
    
    st.markdown("---")
    
    # Existing file upload section
    st.markdown("### Upload New Datasets")
    uploads_dir = os.path.join(os.path.dirname(__file__), "data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    st.caption("Drag and drop or browse to upload one or more files. They will be saved to data/uploads.")
    files = st.file_uploader(
        "Upload files",
        type=["csv", "json", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    if files:
        for f in files:
            save_path = os.path.join(uploads_dir, f.name)
            with open(save_path, "wb") as out:
                out.write(f.getbuffer())
        st.success(f"Uploaded {len(files)} file(s) to data/uploads")

    st.markdown("### Uploaded files")
    existing = sorted([fn for fn in os.listdir(uploads_dir)])
    if not existing:
        st.info("No files uploaded yet.")
    else:
        # Bulk delete controls
        delete_choice = st.multiselect("Select files to delete", existing, key="delete_files")
        if st.button("Delete selected"):
            removed = 0
            for name in delete_choice:
                try:
                    os.remove(os.path.join(uploads_dir, name))
                    removed += 1
                except Exception as e:
                    st.error(f"Could not delete {name}: {e}")
            if removed:
                st.success(f"Deleted {removed} file(s)")
                try:
                    st.rerun()
                except Exception:
                    pass

        for name in existing:
            path = os.path.join(uploads_dir, name)
            cols = st.columns([6, 2])
            with cols[0]:
                st.write(f"- {name} ({os.path.getsize(path)} bytes)")
            with cols[1]:
                if st.button("Remove", key=f"rm_{name}"):
                    try:
                        os.remove(path)
                        st.success(f"Removed {name}")
                        try:
                            st.rerun()
                        except Exception:
                            pass
                    except Exception as e:
                        st.error(f"Could not remove {name}: {e}")
            lower = name.lower()
            try:
                if lower.endswith(".csv"):
                    df = pd.read_csv(path, nrows=50)
                    # Quick insights for CSV with review text
                    st.dataframe(df)
                    text_cols = [c for c in df.columns if c.lower() in ("review", "reviewtext", "text", "comments")]
                    if text_cols:
                        col = text_cols[0]
                        sample_text = " ".join(map(str, df[col].dropna().astype(str).head(200)))
                        if sample_text:
                            label, score = quick_sentiment(sample_text)
                            keys = extract_keywords(sample_text, top_k=8)
                            st.markdown(
                                f"<div class='card'><b>Quick Insight</b><br/>Sentiment: <b>{label}</b> (score {score})<br/>Top Keywords: <code>{', '.join(keys)}</code></div>",
                                unsafe_allow_html=True,
                            )
                elif lower.endswith(".json"):
                    df = pd.read_json(path, lines=False)
                    st.dataframe(df.head(50))
                    text_cols = [c for c in df.columns if c.lower() in ("review", "reviewtext", "text", "comments")]
                    if text_cols:
                        col = text_cols[0]
                        sample_text = " ".join(map(str, df[col].dropna().astype(str).head(200)))
                        if sample_text:
                            label, score = quick_sentiment(sample_text)
                            keys = extract_keywords(sample_text, top_k=8)
                            st.markdown(
                                f"<div class='card'><b>Quick Insight</b><br/>Sentiment: <b>{label}</b> (score {score})<br/>Top Keywords: <code>{', '.join(keys)}</code></div>",
                                unsafe_allow_html=True,
                            )
                elif lower.endswith((".png", ".jpg", ".jpeg")):
                    st.image(path, caption=name, use_column_width=True)
            except Exception as e:
                st.caption(f"Preview not available: {e}")
