from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import tempfile
import mimetypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.form.get('message', '').strip()
        files = request.files.getlist('files')
        prompt_parts = []

        # --- FIX: handle uploaded files with MIME type ---
        for file in files:
            if file.filename == "":
                continue
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file.name)

                mime_type, _ = mimetypes.guess_type(file.filename)
                if not mime_type:
                    mime_type = "application/octet-stream"

                uploaded_file = genai.upload_file(
                    path=temp_file.name,
                    display_name=file.filename,
                    mime_type=mime_type
                )
            prompt_parts.append(uploaded_file)

        if message:
            prompt_parts.append(message)

        if not prompt_parts:
            return jsonify({"reply": "Please provide a message or upload a file."})

        # Create Gemini model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")

        # Generate content
        response = model.generate_content(prompt_parts)

        reply_text = getattr(response, "text", "Sorry, I couldn’t generate a response.")

        return jsonify({"reply": reply_text})

    except Exception as e:
        print(f"An error occurred in /chat: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
