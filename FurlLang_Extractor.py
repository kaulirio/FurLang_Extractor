
#Import libraries
import streamlit as st
import re
import unicodedata
import zipfile
from io import StringIO, BytesIO

# --- Text Processing Functions ---
def normalize_text(text, remove_accents=True):
    if remove_accents:
        text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"[^\w\s]", "", text)

def extract_unique_words(text, case_sensitive=False, remove_accents=True):
    if not case_sensitive:
        text = text.lower()
    text = normalize_text(text, remove_accents)
    words = text.split()
    return sorted(set(words), key=str.lower)

def split_words_by_letter(words):
    by_letter = {}
    for word in words:
        if word:
            first_letter = word[0].upper()
            by_letter.setdefault(first_letter, []).append(word)
    return by_letter

def generate_zip(letter_dict):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
        for letter, word_list in letter_dict.items():
            content = "\n".join(word_list)
            zf.writestr(f"{letter}.txt", content)
    zip_buffer.seek(0)
    return zip_buffer

# --- Streamlit UI/App ---
st.set_page_config(page_title="Fur Word Dictionary", layout="centered")
st.title("📂 Fur Word Dictionary")
st.caption("Extract, Sort, Build a Dictionary")

uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
text_input = st.text_area("Or paste text here:")

col1, col2 = st.columns(2)
with col1:
    case_sensitive = st.checkbox("Case Sensitive", False)
with col2:
    remove_accents = st.checkbox("Normalize (remove accents)", True)

if st.button("🔍 Process Text"):
    raw_text = ""
    if uploaded_file:
        raw_text = uploaded_file.read().decode("utf-8")
    elif text_input:
        raw_text = text_input

    if not raw_text.strip():
        st.warning("Please upload a file or paste some text.")
    else:
        words = extract_unique_words(raw_text, case_sensitive, remove_accents)
        grouped = split_words_by_letter(words)

        st.success(f"{len(words)} unique words found.")
        st.download_button("📥 Download All Words File (.txt)", "\n".join(words), "all_words.txt")

        zip_bytes = generate_zip(grouped)
        st.download_button("📚 Download A–Z Files (.zip)", zip_bytes, "words_by_letter.zip")

        st.markdown("### 🔎 Preview:")
        st.code("\n".join(words[:20]) or "No words found.")
