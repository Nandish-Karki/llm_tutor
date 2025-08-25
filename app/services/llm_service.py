import ollama
from openai import OpenAI
from app.helpers.prompt_helper import get_prompt
import json

from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def call_llama_for_module_name(text):
    prompt = f"""
You are an expert course designer.

Given the following content from a learning module, return only a short, descriptive title (3 to 6 words max) that summarizes the content.

Do not explain. Do not list multiple titles. Just return a single title.
No extra slashes, quotes, or formatting.

Content:
\"\"\"
{text}
\"\"\"

Title:
    """
    response = ollama.chat(
        model='llama3.2:latest',
        messages=[{"role": "user", "content": prompt}]
    )

    # Clean and return plain title
    raw_title = response['message']['content']
    clean_title = raw_title.strip().strip('"').strip("'")
    print(clean_title)
    return clean_title


client = OpenAI(
    api_key=OPENAI_API_KEY
)

def generate_answer(question, module_content, emotion):
    prompt = get_prompt(question, module_content, emotion)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()

    try:
        # parse the JSON your prompt asked for
        answer_obj = json.loads(raw)
    except json.JSONDecodeError:
        # fallback: wrap the entire raw text as the answer
        answer_obj = {
            "answer": raw,
            "supporting_texts": []
        }

    return answer_obj