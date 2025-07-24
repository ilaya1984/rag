import os
import pickle
import numpy as np
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import markdown
from flask import session

# ✅ LangChain Tools & Agents
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain_core.messages import AIMessage, HumanMessage


def extract_suggested_questions_from_answer(answer: str, max_questions: int = 5) -> list[str]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Based on the following answer, generate "
                f"{max_questions} interesting, relevant, and diverse follow-up questions a user might ask. "
                "Return only the questions in a clean numbered or bulleted list."
            )
        },
        {
            "role": "user",
            "content": f"{answer}\n\nGenerate {max_questions} follow-up questions:"
        }
    ]

    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
        )
        raw_output = response.choices[0].message.content.strip()
        return [q.strip("•- 1234567890.").strip() for q in raw_output.split("\n") if q.strip()]
    except Exception as e:
        print("Follow-up suggestion error:", e)
        return []



# Add globally or in function scope


def extract_suggested_questions(chunks: list[str], max_questions: int = 5) -> list:
    if not chunks:
        return []

    # ✅ Sample chunks: beginning, middle, end
    N = len(chunks)
    selected = []

    if N >= 6:
        selected += chunks[:2]
        selected += chunks[N // 2:N // 2 + 2]
        selected += chunks[-2:]
    else:
        selected = chunks[:min(6, N)]

    context = "\n".join(selected)
    context = context[:2000]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Based on the following document content, generate "
                f"{max_questions} interesting, relevant, and diverse questions a user might ask. "
                "Return only the questions in a clean numbered or bulleted list."
            )
        },
        {
            "role": "user",
            "content": f"{context}\n\nGenerate {max_questions} questions:"
        }
    ]

    try:
        response = client.chat_completion(
            messages=messages,
            max_tokens=300,
            temperature=0.7,
            top_p=0.9,
        )
        raw_output = response.choices[0].message.content.strip()
        questions = [
            line.strip("•-*0123456789. ").strip()
            for line in raw_output.splitlines()
            if len(line.strip()) > 5
        ]
        return questions[:max_questions]

    except Exception as e:
        print(f"[ERROR] Failed to generate suggested questions: {e}")
        return []



# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# Together Inference
client = InferenceClient(
    provider="together",
    model="mistralai/Mistral-7B-Instruct-v0.3",
    api_key="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"  # Replace with your Together.ai HF key
)

def extract_clean_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text and "table of contents" not in page_text.lower():
            text += page_text.strip() + "\n"
    return text

def ingest_and_embed(agent_id: str, pdf_path: str):
    os.makedirs("data", exist_ok=True)
    os.makedirs("index", exist_ok=True)

    clean_text = extract_clean_text(pdf_path)
   
     # 🔥 Generate suggestions from PDF text
    

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(clean_text)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 100]

    # Save docs to data/
    with open(os.path.join("data", f"{agent_id}.pkl"), "wb") as f:
        pickle.dump(chunks, f)

    # ✅ Save FAISS index to index/agent_id.faiss + .pkl
    vectorstore = FAISS.from_texts(chunks, embedder)
    vectorstore.save_local("index", index_name=agent_id)

    # ✅ Now generate suggested questions using chunks
    suggested_questions = extract_suggested_questions(chunks)

    # Save suggestions in session
    session.setdefault("suggestions", {})
    session["suggestions"][agent_id] = suggested_questions

# def ask_question(query: str) -> str:
#     # Load FAISS index + docs
#     vectorstore = FAISS.load_local("index", embedder, allow_dangerous_deserialization=True)
#     with open("docs.pkl", "rb") as f:
#         docs = pickle.load(f)

#     # Vector search
#     q_vector = embedder.embed_query(query)
#     D, I = vectorstore.index.search(np.array([q_vector]), k=5)

#     # Select top context chunks (limit length)
#     context = []
#     total_char_limit = 12000
#     for i in I[0]:
#         if 0 <= i < len(docs):
#             chunk = docs[i].strip()
#             if chunk and len("".join(context)) + len(chunk) < total_char_limit:
#                 context.append(chunk)
#     context_text = "\n".join(context)

#     # 💡 Add a system role to guide tone
#     messages = [
#         {
#             "role": "system",
#             "content": (
#                 "You are a helpful and articulate assistant. "
#                 "When answering questions, use **Markdown formatting**:\n"
#                 "- Use **bold** for important terms\n"
#                 "- Use numbered or bullet lists for steps or points\n"
#                 "- Use headings (### or **) when appropriate\n"
#                 "- Use a table if comparing multiple things\n\n"
#                 "Keep answers concise and reader-friendly."
#             )
#         },
#         {
#             "role": "user",
#             "content": (
#                 f"Using the context below, answer the question in Markdown format.\n\n"
#                 f"### Context:\n{context_text}\n\n"
#                 f"### Question:\n{query}\n"
#             )
#         }
#     ]

#     # Query the LLM (Together.ai)
#     response = client.chat_completion(
#         messages,
#         max_tokens=300,
#         temperature=0.8,
#         top_p=0.9,
#     )
#     markdown_answer = response.choices[0].message.content.strip()
#     html_answer = markdown.markdown(markdown_answer, unsafe_allow_html=True)
#     print(html_answer )
def ask_question(agent_id: str, query: str) -> dict:
    # Paths
    data_path = os.path.join("data", f"{agent_id}.pkl")
    index_path = os.path.join("index", agent_id)
    
    if not os.path.exists(data_path):
        return {"error": f"No document found for agent '{agent_id}'"}
    if not os.path.exists(index_path + ".faiss") or not os.path.exists(index_path + ".pkl"):
        return {"error": f"No index found for agent '{agent_id}' path:"+data_path}

    with open(data_path, "rb") as f:
        docs = pickle.load(f)

    vectorstore = FAISS.load_local("index", embedder, index_name=agent_id, allow_dangerous_deserialization=True)

    q_vector = embedder.embed_query(query)
    D, I = vectorstore.index.search(np.array([q_vector]), k=5)

    total_char_limit = 12000
    context = []
    for i in I[0]:
        if 0 <= i < len(docs):
            chunk = docs[i].strip()
            if chunk and len("".join(context)) + len(chunk) <= total_char_limit:
                context.append(chunk)

    if not context:
        return {"error": "No relevant chunks found"}

    context_text = "\n".join(context)

    # LLM prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use **Markdown formatting**:\n"
                "- Headings (###)\n"
                "- **Bold** for important words\n"
                "- Bullet points or numbers for structure\n"
                "- Use tables if needed\n"
                "Keep the tone friendly and clear."
            )
        },
        {
            "role": "user",
            "content": (
                f"Answer the following question using only the context below. Format the response in Markdown.\n\n"
                f"### Context:\n{context_text}\n\n"
                f"### Question:\n{query}"
            )
        }
    ]

    # Call model
    response = client.chat_completion(
        messages,
        max_tokens=500,
        temperature=0.8,
        top_p=0.9,
    )

    markdown_answer = response.choices[0].message.content.strip()
    html_answer = markdown.markdown(markdown_answer, extensions=["extra"], output_format="html5")

    return html_answer

def load_retriever_tool(agent_id: str) -> Tool | None:
    try:
        vectorstore = FAISS.load_local("index", embedder, index_name=agent_id, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        return create_retriever_tool(
            retriever,
            name="document_qa",
            description=f"Use this to answer document-based questions for agent {agent_id}."
        )
    except Exception as e:
        print(f"[TOOL ERROR] Retriever tool load failed for {agent_id}: {e}")
        return None

class TogetherChat(SimpleChatModel):
    def _call(self, messages, stop=None):
        hf_messages = [{"role": m.type, "content": m.content} for m in messages]
        try:
            response = client.chat_completion(messages=hf_messages, max_tokens=512, temperature=0.7)
            return response.choices[0].message.content
        except Exception as e:
            return f"[Together AI Error] {e}"

def run_agent_with_tools(agent_id: str, query: str) -> str:
    try:
        vectorstore = FAISS.load_local("index", embedder, index_name=agent_id, allow_dangerous_deserialization=True)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        retriever_tool = create_retriever_tool(
            retriever,
            name="document_qa",
            description=f"Use this to answer document-based questions for agent {agent_id}."
        )

        tools = [
            retriever_tool,
            DuckDuckGoSearchRun(name="Search")
        ]

        llm = TogetherChat()
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True
        )

        return agent.run(query)

    except Exception as e:
        print("[AGENT ERROR]:", e)
        return f"<span style='color:red;'>Agent failed: {e}</span>"