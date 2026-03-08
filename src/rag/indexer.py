"""Policy document ingestion script for ChromaDB RAG pipeline.

Reads PDF files from the data directory, chunks the text,
embeds using a HuggingFace sentence-transformer, and stores
in a local ChromaDB collection named 'Rulebook'.
"""

import os
import sys
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

# Configuration: Point to root-level directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data_files")  # Using the renamed data directory
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "Rulebook"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def ingest_pdfs() -> None:
    """Ingest all PDFs from the data directory into the ChromaDB 'Rulebook' collection.

    Reads each PDF found in DATA_DIR, splits the text into overlapping chunks,
    and stores them with metadata (source filename, page number) in ChromaDB
    using the default embedding function.
    """
    if not os.path.isdir(DATA_DIR):
        print(f"[ERROR] Data directory '{DATA_DIR}' not found.")
        print("  Please ensure 'data_files' exists and contains zoning.pdf / comp_plan.pdf.")
        return

    pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"[ERROR] No PDF files found in '{DATA_DIR}'.")
        return

    print(f"[INFO] Found {len(pdf_files)} PDF(s): {pdf_files}")

    # Text splitter configuration
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    # ChromaDB persistent client
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if it exists (fresh ingest)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[INFO] Deleted existing '{COLLECTION_NAME}' collection.")
    except Exception:
        # Ignore if collection doesn't exist
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Montgomery city policy documents"},
    )

    total_chunks = 0
    for pdf_name in pdf_files:
        pdf_path = os.path.join(DATA_DIR, pdf_name)
        print(f"[INFO] Loading {pdf_name}...")

        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
        except Exception as e:
            print(f"[ERROR] Failed to load {pdf_name}: {e}")
            continue

        for page in pages:
            chunks = splitter.split_text(page.page_content)
            for j, chunk in enumerate(chunks):
                doc_id = f"{pdf_name}_p{page.metadata.get('page', 0)}_c{j}"
                collection.add(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{
                        "source": pdf_name,
                        "page": page.metadata.get("page", 0),
                        "chunk_index": j,
                    }],
                )
                total_chunks += 1

    print(f"[SUCCESS] Ingested {total_chunks} chunks into '{COLLECTION_NAME}' collection.")
    print(f"[INFO] ChromaDB persisted at: {CHROMA_DIR}")


if __name__ == "__main__":
    ingest_pdfs()
