from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

TANMAY_API = "https://text2img.hideme.eu.org/image"
POLLINATIONS_API = "https://image.pollinations.ai/prompt/"

# API KEY
TANMAY_API_KEY = os.getenv("TANMAY_API_KEY", "tanmay")


@app.route('/')
def index():
    return jsonify({
        "service": "Tanmay AI Image Generator",
        "endpoint": "/gen",
        "usage": "/gen?prompt=your_description&model=tanmay&key=YOUR_KEY",
        "models_available": ["tanmay", "pollination"],
        "default": "tanmay"
    })


@app.route('/gen')
def generate():

    # Check API key
    api_key = request.args.get("key") or request.headers.get("X-API-Key")

    if api_key != TANMAY_API_KEY:
        return jsonify({
            "error": "Invalid or missing API key"
        }), 401

    prompt = request.args.get('prompt')

    if not prompt:
        return Response(
            "Missing 'prompt' parameter",
            status=400
        )

    model = request.args.get('model', 'tanmay').lower()

    if model not in ['tanmay', 'pollination']:
        return Response(
            "Invalid model. Use 'tanmay' or 'pollination'.",
            status=400
        )

    try:
        encoded_prompt = requests.utils.quote(prompt)

        if model == 'tanmay':
            api_url = (
                f"{TANMAY_API}"
                f"?prompt={encoded_prompt}"
                f"&model=flux"
            )
        else:
            api_url = f"{POLLINATIONS_API}{encoded_prompt}"

        resp = requests.get(
            api_url,
            timeout=60
        )

        resp.raise_for_status()

        content_type = resp.headers.get(
            'Content-Type',
            'image/png'
        )

        return Response(
            resp.content,
            content_type=content_type
        )

    except requests.exceptions.RequestException as e:
        return Response(
            f"Error fetching image from {model}: {e}",
            status=502
        )


@app.route('/<path:invalid_path>')
def not_found(invalid_path):
    return jsonify({
        "error": "Invalid endpoint",
        "correct_path": "/gen?prompt=YOUR_PROMPT&key=YOUR_KEY",
        "models": ["tanmay", "pollination"]
    }), 404


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000
    )