from flask import Flask, request, jsonify, render_template_string
import os
from rag_utils import ingest_and_embed, ask_question


app = Flask(__name__)
UPLOAD_FOLDER = "uploaded_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = """
<!doctype html>
<title>RAG with Phi-2</title>
<h2>Upload PDF</h2>
<form method=post enctype=multipart/form-data action="/upload">
  <input type=file name=file><input type=submit value=Upload>
</form>
<hr>
<h2>Ask a question</h2>
<form method=post action="/ask">
  <input type=text name=query style="width:300px;">
  <input type=submit value=Ask>
</form>
{% if response %}
  <h3>Response:</h3>
  <p>{{ response }}</p>
{% endif %}
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(path)
    ingest_and_embed(path)
    return "PDF uploaded and embedded! 000000000000000000000000000000000"

@app.route("/ask", methods=["POST"])
def ask():
    query = request.form["query"]
    answer = ask_question(query)
    return answer

if __name__ == "__main__":
    app.run(debug=True)
