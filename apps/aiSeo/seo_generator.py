import spacy
import re
import nltk
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from collections import Counter
from bs4 import BeautifulSoup

# Pastikan nltk 'punkt' sudah terinstal
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

# Load model NLP (model universal mendukung berbagai bahasa)
nlp = spacy.load("xx_ent_wiki_sm")

def extract_keywords(text, num_keywords=5):
    """
    Ekstrak keyword utama menggunakan spaCy dengan penyaringan kata-kata umum.
    """
    doc = nlp(text.lower())
    words = [token.text for token in doc if token.is_alpha and not token.is_stop]
    keyword_freq = Counter(words)
    sorted_keywords = [word for word, freq in keyword_freq.most_common(num_keywords)]
    # Filter kata-kata umum yang tidak relevan
    common_words = {"yang", "dan", "dengan", "adalah", "ini", "untuk", "seperti", "anda", "atau", "dalam"}
    filtered_keywords = [word for word in sorted_keywords if word not in common_words]
    return ", ".join(filtered_keywords)

def clean_html(text):
    """
    Membersihkan teks dari HTML dan karakter aneh menggunakan BeautifulSoup.
    """
    return BeautifulSoup(text, "html.parser").get_text()

def summarize_text(text, max_sentences=2):
    """
    Menggunakan Sumy (LSA Summarizer) untuk merangkum teks.
    Jika hasil ringkasan terlalu pendek, gunakan 2 kalimat pertama sebagai fallback.
    """
    text = clean_html(text)
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, max_sentences)
    summary_text = " ".join([str(sentence) for sentence in summary]).strip()
    if not summary_text or len(summary_text) < 50:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary_text = " ".join(sentences[:2]).strip()
    return summary_text

def smart_truncate_complete(text, max_length):
    """
    Memotong teks secara cerdas agar tidak terpotong di tengah kata atau kalimat.
    Fungsi ini mencoba mengembalikan teks hingga batas maksimum pada akhir kalimat.
    Jika tidak ada batas kalimat yang cocok, dipotong di akhir kata.
    """
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= max_length:
        return text
    # Coba potong di akhir kalimat
    sentences = re.split(r'(?<=[.!?])\s+', text)
    truncated = ""
    for sentence in sentences:
        if len(truncated) + len(sentence) <= max_length:
            truncated += sentence + " "
        else:
            break
    truncated = truncated.strip()
    if truncated:
        return truncated
    # Fallback: potong di spasi terakhir
    pos = text.rfind(" ", 0, max_length)
    if pos != -1:
        return text[:pos].strip()
    return text[:max_length].strip()

def generate_seo(title, description, custom_format=None):
    """
    Menghasilkan meta title dan meta description dengan langkah:
    - Membersihkan HTML dari deskripsi.
    - Mengekstrak entitas utama (misalnya, ORG, GPE, PRODUCT, WORK_OF_ART) dan keyword.
    - Menggabungkan elemen tersebut dengan format default (atau custom) secara natural.
    - Memotong hasil dengan smart truncation agar tidak terpotong di tengah kalimat.
    """
    description = clean_html(description)
    doc = nlp(description)
    
    # Ekstrak entitas utama dan pertahankan urutan kemunculan (hindari duplikasi)
    entities = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "GPE", "PRODUCT", "WORK_OF_ART"]]
    entity_part = ", ".join(sorted(set(entities), key=entities.index)[:2]) if entities else ""
    
    # Ekstrak keyword utama
    keywords = extract_keywords(description)
    
    # Jika entitas sudah ada dalam title, hilangkan agar tidak duplikat
    if entity_part and entity_part.lower() in title.lower():
        entity_part = ""
    
    # Bangun meta title
    if custom_format:
        meta_title = custom_format.format(title=title, location=entity_part, keywords=keywords)
    else:
        meta_title = title
        if entity_part:
            meta_title += f" | {entity_part}"
        if keywords:
            meta_title += f" - {keywords}"
    
    meta_title = re.sub(r'\s+', ' ', meta_title).strip()
    meta_title = smart_truncate_complete(meta_title, 65)  # Ideal: 60-65 karakter
    
    # Bangun meta description
    meta_description = summarize_text(description)
    meta_description = smart_truncate_complete(meta_description, 160)  # Ideal: 150-160 karakter
    
    # Fallback: jika meta description terlalu pendek, gunakan 2 kalimat pertama dari deskripsi
    if not meta_description or len(meta_description) < 50:
        sentences = re.split(r'(?<=[.!?])\s+', description)
        meta_description = " ".join(sentences[:2]).strip()
        meta_description = smart_truncate_complete(meta_description, 160)
    
    return meta_title, meta_description
