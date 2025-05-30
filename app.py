from flask import Flask, request, Response, jsonify
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

client = genai.Client(
    vertexai=True,
    project=os.getenv("PROJECT_ID"),
    location=os.getenv("LOCATION"),
)

SI_TEXT = (
    "anda adalah asisten virtual dalam memberikan informasi, saran medis awal, "
    "dan panduan lanjutan kepada pengguna untuk penyakit pernafasan seperti "
    "pneumonia, tuberkulosis (TBC), dan COVID-19. tidak bisa menjawab penyakit lainnya."
)

MODEL = "gemini-2.5-pro-preview-05-06"

COMMON_CONFIG = dict(
    temperature=1,
    top_p=0.88,
    seed=0,
    max_output_tokens=3000,
    safety_settings=[
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH", 
            threshold="OFF"
        ), types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT", 
            threshold="OFF"
        ), types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT", 
            threshold="OFF"
        ), types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT", 
            threshold="OFF"
        ),
    ],
    system_instruction=[types.Part.from_text(text=SI_TEXT)],
)

def build_contents(user_query):
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    if isinstance(user_query, list) and all(isinstance(m, dict) and "content" in m for m in user_query):
        contents = []
        for message in user_query:
            role = message.get("role", "user")
            text = message.get("content", "")
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)]
            ))
        return contents
    elif isinstance(user_query, str):
        return [types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_query)]
        )]
    else:
        raise ValueError("Invalid query format: must be string or list of {role,content} dicts")

@app.route('/generate-stream', methods=['POST'])
def generate_stream():
    data = request.json or {}
    user_query = data.get('query', [])
    try:
        contents = build_contents(user_query)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    config = types.GenerateContentConfig(**COMMON_CONFIG)

    stream = client.models.generate_content_stream(
        model=MODEL,
        contents=contents,
        config=config,
    )

    def event_stream():
        for chunk in stream:
            # text_delta = "".join(part.text for part in chunk.choices[0].delta.parts)
            if chunk.text:
                yield chunk.text

    return Response(
        event_stream(),
        mimetype='text/plain; charset=utf-8',
        headers={"Transfer-Encoding": "chunked"}
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
