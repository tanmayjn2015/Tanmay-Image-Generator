from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import os
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

# ============================================================
# APIs
# ============================================================

TANMAY_API = "https://text2img.hideme.eu.org/image"

# Pollinations current API
POLLINATIONS_API = "https://gen.pollinations.ai/image/"

# ============================================================
# API KEY
# ============================================================

TANMAY_API_KEY = os.getenv("TANMAY_API_KEY", "tanmay")

# Optional Pollinations API key
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():
    return jsonify({
        "service": "Tanmay AI Image Generator",
        "status": "online",
        "endpoint": "/gen",
        "usage": "/gen?prompt=your_description&model=tanmay&key=YOUR_KEY",
        "models_available": [
            "tanmay",
            "pollination"
        ],
        "default": "tanmay"
    })


# ============================================================
# IMAGE GENERATOR
# ============================================================

@app.route("/gen", methods=["GET"])
def generate():

    # --------------------------------------------------------
    # Check API key
    # --------------------------------------------------------

    api_key = (
        request.args.get("key")
        or request.headers.get("X-API-Key")
    )

    if api_key != TANMAY_API_KEY:
        return jsonify({
            "success": False,
            "error": "Invalid or missing API key"
        }), 401

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = request.args.get("prompt", "").strip()

    if not prompt:
        return jsonify({
            "success": False,
            "error": "Missing 'prompt' parameter"
        }), 400

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model = request.args.get("model", "tanmay").lower().strip()

    if model not in ("tanmay", "pollination"):
        return jsonify({
            "success": False,
            "error": "Invalid model",
            "available_models": [
                "tanmay",
                "pollination"
            ]
        }), 400

    # URL encode prompt
    encoded_prompt = quote(prompt, safe="")

    try:

        # ====================================================
        # TANMAY API
        # ====================================================

        if model == "tanmay":

            params = {
                "prompt": prompt,
                "model": "flux"
            }

            resp = requests.get(
                TANMAY_API,
                params=params,
                timeout=120
            )

        # ====================================================
        # POLLINATIONS API
        # ====================================================

        else:

            api_url = f"{POLLINATIONS_API}{encoded_prompt}"

            params = {
                "model": "flux"
            }

            headers = {}

            if POLLINATIONS_API_KEY:
                headers["Authorization"] = (
                    f"Bearer {POLLINATIONS_API_KEY}"
                )

            resp = requests.get(
                api_url,
                params=params,
                headers=headers,
                timeout=120
            )

        # ----------------------------------------------------
        # Check HTTP response
        # ----------------------------------------------------

        if resp.status_code != 200:

            error_text = resp.text[:1000]

            return jsonify({
                "success": False,
                "error": f"{model} API returned HTTP {resp.status_code}",
                "details": error_text
            }), 502

        # ----------------------------------------------------
        # Check content
        # ----------------------------------------------------

        if not resp.content:
            return jsonify({
                "success": False,
                "error": f"{model} API returned empty response"
            }), 502

        # ----------------------------------------------------
        # Return image
        # ----------------------------------------------------

        content_type = resp.headers.get(
            "Content-Type",
            "image/png"
        )

        return Response(
            resp.content,
            status=200,
            content_type=content_type,
            headers={
                "Cache-Control": "no-cache"
            }
        )

    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "error": f"{model} API request timed out"
        }), 504

    except requests.exceptions.ConnectionError as e:

        return jsonify({
            "success": False,
            "error": f"Unable to connect to {model} API",
            "details": str(e)
        }), 502

    except requests.exceptions.RequestException as e:

        return jsonify({
            "success": False,
            "error": f"Request failed for {model}",
            "details": str(e)
        }), 502

    except Exception as e:

        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500


# ============================================================
# INVALID ENDPOINT
# ============================================================

@app.route("/<path:invalid_path>")
def not_found(invalid_path):

    return jsonify({
        "success": False,
        "error": "Invalid endpoint",
        "correct_path": "/gen?prompt=YOUR_PROMPT&key=YOUR_KEY",
        "models": [
            "tanmay",
            "pollination"
        ]
    }), 404


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(os.getenv("PORT", "5000"))

    app.run(
        host="0.0.0.0",
        port=port
    )        
