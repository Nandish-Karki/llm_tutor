import textwrap
import re
import json
from pydub import AudioSegment

EMPHASIS_KEYWORDS = {"important", "critical", "alert", "note", "warning"}

def split_text(text, limit=2500):
    return textwrap.wrap(text, width=limit)

def generate_ssml(text, chunk_id=0):
    ssml = '<speak>'
    sentences = re.split(r'(?<=[.!?]) +', text)
    word_index = 0

    for sentence in sentences:
        words = sentence.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word.lower())
            ssml += f'<mark name="w{chunk_id}_{word_index}"/>'

            if clean_word in EMPHASIS_KEYWORDS:
                ssml += f'<emphasis level="moderate">{word}</emphasis>'
            else:
                ssml += word

            if i < len(words) - 1:
                ssml += ' '
            word_index += 1


    ssml += '</speak>'
    return ssml

def merge_audio(files, output_path):
    combined = AudioSegment.empty()
    for f in files:
        combined += AudioSegment.from_mp3(f)
    combined.export(output_path, format="mp3")
    return output_path

def merge_speech_marks(files, output_path):
    combined = []
    offset = 0
    for file in files:
        with open(file) as f:
            try:
                marks = json.load(f)
                for mark in marks:
                    mark["time"] += offset
                    combined.append(mark)
                offset = combined[-1]["time"]
            except:
                continue
    with open(output_path, "w") as f:
        json.dump(combined, f)
    return output_path
