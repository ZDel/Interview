from pathlib import Path
import csv
import os, time
from flask import (
    Flask, url_for, send_from_directory,
    render_template_string, abort, request, flash, redirect
)
from werkzeug.utils import secure_filename
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "Documents.csv"
DOCS_ROOT = BASE_DIR / "Docs"  

print(f"CSV_PATH: {CSV_PATH}")

app = Flask(__name__)
app.secret_key = "test"
def append_document(csv_path: Path, name: str, rel_path: str, category: str):
    new_file = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Path", "Category"])
        if new_file:
            writer.writeheader()
        writer.writerow({
            "Name": name,
            "Path": rel_path.replace("/", "\\"),
            "Category": category
        })

def read_documents(csv_path: Path):

    docs = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f) 
        for row in reader:
            name = (row.get("Name") or "").strip()
            rel_path = (row.get("Path") or "").replace("\\", "/").strip()
            category = (row.get("Category") or "").strip()
            if not name or not rel_path:
                continue
            docs.append({
                "name": name,
                "rel_path": rel_path,
                "category": category
            })
    return docs
def write_documents(csv_path: Path, docs: list[dict]):
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Path", "Category"])
        writer.writeheader()
        for d in docs:
            writer.writerow({
                "Name": d["name"],
                "Path": d["rel_path"].replace("/", "\\"),
                "Category": d["category"]
            })

@app.route("/", methods=["GET"])
def index():
    docs = read_documents(CSV_PATH)
    for idx, d in enumerate(docs):
        d["idx"] = idx
        d["url"] = url_for("serve_file", subpath=d["rel_path"])
    return render_template_string(INDEX_HTML, docs=docs)

@app.route("/files/<path:subpath>")
def serve_file(subpath: str):
    safe_path = subpath.replace("\\", "/")

    inside_docs = safe_path.split("/", 1)[1] if "/" in safe_path else ""

    return send_from_directory(DOCS_ROOT, inside_docs, as_attachment=False)
@app.route("/delete", methods=["POST"])
def delete_doc():

    try:
        idx = int(request.form.get("idx", "-1"))
    except ValueError:
        flash("Invalid delete request.", "error")
        return redirect(url_for("index"))

    docs = read_documents(CSV_PATH)
    if idx < 0 or idx >= len(docs):
        flash("Document not found.", "error")
        return redirect(url_for("index"))

    doc = docs.pop(idx)
    # Rewrite CSV without this entry
    write_documents(CSV_PATH, docs)


    flash("Document deleted.", "success")
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload_doc():
    """Handle real file upload, save to Docs/, and append to CSV."""
    name = (request.form.get("name") or "").strip()
    category = (request.form.get("category") or "").strip()
    file = request.files.get("file")

    if not name or not file or not file.filename:
        flash("Name and file are required.", "error")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)


    # Ensure unique filename to avoid collisions
    base, ext = os.path.splitext(filename)
    unique = f"{base}_{int(time.time())}{ext}"
    save_path = DOCS_ROOT / unique
    file.save(save_path)

    # Path stored in CSV should start with Docs/ for serving
    rel_path = f"Docs/{unique}"
    append_document(CSV_PATH, name=name, rel_path=rel_path, category=category)

    flash("Document uploaded.", "success")
    return redirect(url_for("index"))

# ---------- Inline template ----------
INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Documents</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    h1 { margin-bottom: 1rem; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.6rem; border-bottom: 1px solid #eee; text-align: left; }
    tr:hover { background: #fafafa; }
    .muted { color: #666; font-size: 0.9rem; }
    .cat { white-space: nowrap; }
  </style>
</head>
<body>
  <h1>Documents</h1>
  {% if docs %}
  <table>
    <thead>
      <tr><th>Name</th><th>Path</th><th class="cat">Category</th></tr>
    </thead>
    <tbody>
      {% for d in docs %}
      <tr>
        <td><a href="{{ d.url }}" target="_blank" rel="noopener">{{ d.name }}</a></td>
        <td class="muted">{{ d.rel_path }}</td>
        <td class="cat">{{ d.category }}</td>
        <td class="actions">
          <form method="post" action="{{ url_for('delete_doc') }}" onsubmit="return confirm('Delete this document?');" style="display:inline;">
            <input type="hidden" name="idx" value="{{ d.idx }}">
            <button type="submit" title="Delete">Delete</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p class="muted">No documents found.</p>
  {% endif %}
  <h2>Upload a new document</h2>
  <form class="upload" method="post" action="{{ url_for('upload_doc') }}" enctype="multipart/form-data">
    <label>Name</label>
    <input type="text" name="name" required>

    <label>Category</label>
    <input type="text" name="category" placeholder="e.g., Supporting Documents">

    <label>Choose file</label>
    <input type="file" name="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.png,.jpg,.jpeg" required>

    <button type="submit" class="add-btn">Upload & Add</button>
  </form>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
