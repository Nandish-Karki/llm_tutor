# def get_prompt(question, content, emotion):
#     tone_instruction = {
#         "happy": "Use an engaging and enthusiastic tone.",
#         "sad": "Be empathetic and gently explain.",
#         "angry": "Be calm and direct.",
#         "confused": "Simplify and clarify concepts step by step.",
#         "neutral": "Provide a clear and factual explanation."
#     }.get(emotion, "Be clear and concise.")

#     return f"""
# You are an AI tutor. Answer the following question based on the module content.

# Strictly it should be in the context of the module content provided. Do not provide any additional information or context outside of this content.
# Include supporting texts from the module and include in your answer
# Also, if outside the content simplely say "I don't know" or "I cannot answer this question based on the provided content."

# Tone: {tone_instruction}

# Question: "{question}"

# Context::
# {content}

# Answer in 3-5 sentences, using clear educational language in the below format:
# Return **only** a valid JSON object (no markdown code fences) exactly like:
# {{
#   "answer": "<your answer here>",
#   "supporting_texts": ["<supporting text 1>", "<supporting text 2>"]
# }}
# """
def get_prompt(question, content, emotion):
    tone_instruction = {
        "happy": "Use an engaging and enthusiastic tone.",
        "sad": "Be empathetic and gently explain.",
        "angry": "Be calm and direct.",
        "confused": "Simplify and clarify concepts step by step.",
        "neutral": "Provide a clear and factual explanation."
    }.get(emotion, "Be clear and concise.")

    return f"""
You are an AI tutor. Answer the following question using **only the provided context**.

Strictly stay within the context provided below. Do not make up any information.
If the answer is not present, say: "I don't know" or "I cannot answer this question based on the provided content."

Tone: {tone_instruction}

Question: "{question}"

Context:
{content}

Answer in 3–5 sentences using clear educational language.

Return **only** a valid JSON object like:
{{
  "answer": "<your answer here>",
  "supporting_texts": ["<supporting text 1>", "<supporting text 2>"]
}}
"""
