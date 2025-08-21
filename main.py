from pathlib import Path

from flask import (
    Flask, request, redirect, url_for, send_from_directory,
    render_template_string, abort, flash
)
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = "Documents.csv"

app = Flask(__name__)
@app.route("/", methods=["GET"])
def index():
    return "Hello, World!"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)