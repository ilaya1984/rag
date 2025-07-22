from flask import Flask, request, session, redirect, url_for, render_template, jsonify
import os
from rag_utils import ingest_and_embed, ask_question,extract_suggested_questions_from_answer
from werkzeug.utils import secure_filename
import json


app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = "uploaded_docs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
AGENTS_DIR = "agents"

def resolve_active_agent(request, session,id) -> str | None:
    
    # 1. Check query string (?id=...)
    agent_id = request.args.get("id")
    if agent_id:
        session["active_agent"] = agent_id
        return agent_id

    # 2. Check existing session
    agent_id = session.get("active_agent")
    if agent_id:
        return agent_id

    # 3. Default to first available agent from agents directory
    try:
        
        session["active_agent"] = id
        return agent_id
    except Exception as e:
        print("Failed to resolve fallback agent:", e)
        return None
    
@app.route("/")
def index():
    session.setdefault("chat_history", [])
    session.setdefault("active_agent", None)

    agents = []
    agent_images = {}
    suggestions_dict = {}
    angent_id=None
    agent_names={}
    for filename in os.listdir("agents"):
        if filename.endswith(".json"):
            with open(os.path.join("agents", filename), "r", encoding="utf-8") as f:
                agent_data = json.load(f)
                agents.append(agent_data["id"])
               
                if angent_id==None:angent_id=agent_data["id"]
                agent_images[agent_data["id"]] = agent_data.get("image", "default_agent.png")
                agent_names[agent_data["id"]] = agent_data["name"]
                suggestions_dict[agent_data["id"]] = agent_data.get("suggested_questions", [])

    active_agent = resolve_active_agent(request, session,angent_id)
    
    suggestions = suggestions_dict.get(active_agent, [])
    # print("aid",angent_id,active_agent,suggestions)
    return render_template(
        "chat.html",
        chat_history=session["chat_history"],
        agents=agents,
        agent_images=agent_images,
        active_agent=active_agent,
        suggestions=suggestions,agent_names=agent_names
    )

@app.route("/switch", methods=["POST"])
def switch_agent():
    agent = request.form.get("agent")
    if agent and agent in session.get("agents", []):
        session["active_agent"] = agent
        session["chat_history"] = []  # Clear chat when switching
    return redirect(url_for("index"))
@app.route("/create_agent", methods=["POST"])
def create_agent():
    from werkzeug.utils import secure_filename

    agent_name = request.form.get("agent_name")
    pdf = request.files.get("file")
    img = request.files.get("agent_image")

    if not agent_name or not pdf:
        return "Agent name and PDF are required", 400

    agent_id = secure_filename(agent_name)  # Normalize filename/ID

    # Save PDF
    pdf_path = os.path.join(UPLOAD_FOLDER, f"{agent_id}.pdf")
    pdf.save(pdf_path)

    # Save agent image (optional)
    if img and img.filename:
        ext = os.path.splitext(img.filename)[-1]
        image_filename = f"{agent_id}{ext}"
        img.save(os.path.join("static", image_filename))
    else:
        image_filename = "default_agent.png"

    # Embed + generate suggestions
    ingest_and_embed(agent_id, pdf_path)  # This already generates suggestions into session

    # Get suggestions from session
    suggestions = session.get("suggestions", {}).get(agent_id, [])

    # Save agent metadata to JSON
    agent_metadata = {
        "id": agent_id,
        "name": agent_name,
        "pdf_path": pdf_path,
        "image": image_filename,
        "suggested_questions": suggestions
    }

    with open(os.path.join("agents", f"{agent_id}.json"), "w", encoding="utf-8") as f:
        json.dump(agent_metadata, f, indent=2)

    # Set active agent in session
    session["active_agent"] = agent_id
    session["chat_history"] = []

    return "OK"


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(path)

    agent_name = f.filename
    ingest_and_embed(agent_name, path)

    session.setdefault("agents", [])
    if agent_name not in session["agents"]:
        session["agents"].append(agent_name)
    session["active_agent"] = agent_name
    session["chat_history"] = []  # Clear chat for new agent

    return redirect(url_for("index"))

@app.route("/ask", methods=["POST"])
def ask():
    if request.is_json:
        data = request.get_json()
        query = data.get("query", "")
    else:
        query = request.form.get("query", "")

    active_agent = session.get("active_agent")
    if not active_agent:
        return jsonify({"answer": "<span style='color:red;'>No agent selected</span>"})

    result = ask_question(active_agent, query)
    if isinstance(result, dict) and "error" in result:
        answer = f"<span style='color:red;'><b>Error:</b> {result['error']}</span>"
    else:
        answer = result
        suggestions = extract_suggested_questions_from_answer(answer)
    
    session.setdefault("chat_history", [])
    session["chat_history"].append({"question": query, "answer": answer})
    session.modified = True

    return jsonify({
        "answer": answer,
        "suggestions": suggestions
    })



if __name__ == "__main__":
    app.run(debug=True)
