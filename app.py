import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import MODEL_NAME, SYSTEM_PROMPT, WELCOME_MESSAGE

load_dotenv()

app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MAX_MESSAGE_LENGTH = 1000
MAX_HISTORY_TURNS = 20


def build_contents(history, user_message):
    """Convert chat history from the browser into Gemini's format."""
    contents = []
    for item in history[-MAX_HISTORY_TURNS:]:
        role = "user" if item.get("role") == "user" else "model"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=text)])
            )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )
    return contents


@app.route("/")
def index():
    return render_template("index.html", welcome=WELCOME_MESSAGE)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Please type a message."}), 400
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": "Message is too long."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, user_message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        return jsonify({"reply": response.text or "Sorry, I could not respond."})
    except Exception:
        return jsonify({"error": "Something went wrong. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
