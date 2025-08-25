import re
import ftfy
import spacy
import textstat
import statistics
from ollama import chat

nlp = spacy.load("en_core_web_sm")

# === Dynamic Threshold Calculator === #
def get_dynamic_thresholds(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    line_lengths = [len(line) for line in lines]
    avg_line_len = sum(line_lengths) / len(line_lengths) if line_lengths else 0
    stddev_line_len = statistics.stdev(line_lengths) if len(line_lengths) > 1 else 0

    total_chars = len(text)
    total_words = len(text.split())
    reading_score = textstat.flesch_reading_ease(text)

    # LENGTH_THRESHOLD: dynamic based on character size
    length_thresh = max(3000, min(8000, int(total_chars * 0.75)))

    # NOISE_LINE_RATIO: stricter if line length is low and uniform
    noise_ratio = 0.5 if avg_line_len < 40 and stddev_line_len < 20 else 0.65

    # MIN_READABILITY: adjust based on document size
    min_readability = 25 if total_words > 1000 else 10

    return length_thresh, noise_ratio, min_readability

def fix_text(text):
    text = ftfy.fix_text(text)
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def is_noisy(text, noise_ratio_thresh, readability_thresh):
    lines = text.split("\n")
    short_lines = [line for line in lines if len(line.strip()) < 30]
    ratio = len(short_lines) / len(lines) if lines else 0
    readability = textstat.flesch_reading_ease(text)
    return ratio > noise_ratio_thresh or readability < readability_thresh

def is_content_useful(text_chunk):
    prompt = f"""
Given the following text, determine whether it contains educational value (e.g., explanation, theory, exercise, concept).

Avoid keeping unrelated content like tables of contents, references, disclaimers, answer keys, page numbers.

Respond only with 'yes' or 'no'.

Text:
\"\"\"{text_chunk}\"\"\"

Answer:
"""
    try:
        res = chat(model="llama3.2:latest", messages=[{"role": "user", "content": prompt}])
        return "yes" in res["message"]["content"].lower()
    except:
        return True

def preprocess_uploaded_text(raw_text):
    """Fix, score, and intelligently clean text using adaptive thresholds + LLM if needed."""
    text = fix_text(raw_text)

    # Dynamically calculate thresholds
    LENGTH_THRESHOLD, NOISE_LINE_RATIO, MIN_READABILITY = get_dynamic_thresholds(text)

    if len(text) < LENGTH_THRESHOLD and not is_noisy(text, NOISE_LINE_RATIO, MIN_READABILITY):
        return text

    print(f"[INFO] LLM filtering activated — len: {len(text)} | noise_ratio: {NOISE_LINE_RATIO} | readability: {MIN_READABILITY}")
    doc = nlp(text)
    useful_chunks = []
    para = ""

    for sent in doc.sents:
        para += sent.text.strip() + " "
        if len(para) > 400:
            if is_content_useful(para.strip()):
                useful_chunks.append(para.strip())
            para = ""

    if para and is_content_useful(para.strip()):
        useful_chunks.append(para.strip())

    return "\n\n".join(useful_chunks)
