import os
import pickle
import numpy as np
from PyPDF2 import PdfReader
from huggingface_hub import InferenceClient
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import markdown

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

def ingest_and_embed(pdf_path: str):
    clean_text = extract_clean_text(pdf_path)

    # Chunk smartly
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(clean_text)
    chunks = [c.strip() for c in chunks if len(c.strip()) > 100]

    # Save text chunks
    with open("docs.pkl", "wb") as f:
        pickle.dump(chunks, f)

    # Embed and save vector index
    vectorstore = FAISS.from_texts(chunks, embedder)
    vectorstore.save_local("index")

def ask_question(query: str) -> str:
    # Load FAISS index + docs
    vectorstore = FAISS.load_local("index", embedder, allow_dangerous_deserialization=True)
    with open("docs.pkl", "rb") as f:
        docs = pickle.load(f)

    # Vector search
    q_vector = embedder.embed_query(query)
    D, I = vectorstore.index.search(np.array([q_vector]), k=5)

    # Select top context chunks (limit length)
    context = []
    total_char_limit = 12000
    for i in I[0]:
        if 0 <= i < len(docs):
            chunk = docs[i].strip()
            if chunk and len("".join(context)) + len(chunk) < total_char_limit:
                context.append(chunk)
    context_text = "\n".join(context)

    # 💡 Add a system role to guide tone
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful and articulate assistant. "
                "When answering questions, use **Markdown formatting**:\n"
                "- Use **bold** for important terms\n"
                "- Use numbered or bullet lists for steps or points\n"
                "- Use headings (### or **) when appropriate\n"
                "- Use a table if comparing multiple things\n\n"
                "Keep answers concise and reader-friendly."
            )
        },
        {
            "role": "user",
            "content": (
                f"Using the context below, answer the question in Markdown format.\n\n"
                f"### Context:\n{context_text}\n\n"
                f"### Question:\n{query}\n"
            )
        }
    ]

    # Query the LLM (Together.ai)
    response = client.chat_completion(
        messages,
        max_tokens=300,
        temperature=0.8,
        top_p=0.9,
    )
    markdown_answer = response.choices[0].message.content.strip()
    html_answer = markdown.markdown(markdown_answer, unsafe_allow_html=True)
    print(html_answer )

    return html_answer

