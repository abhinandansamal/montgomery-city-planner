"""City policy search engine using ChromaDB RAG pipeline.

Performs similarity search on the local 'Rulebook' ChromaDB collection
to retrieve relevant Montgomery zoning and planning policy excerpts.
"""

import os
from typing import Any, Dict, List, Optional
import chromadb

# Configuration: Point to the chroma_db directory at the project root
# Assuming this file is at src/rag/engine.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "Rulebook"


def _get_collection() -> Optional[chromadb.Collection]:
    """Retrieve the Rulebook collection from ChromaDB.

    Returns:
        The ChromaDB collection if found, otherwise None.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        return None


async def search_city_policy(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Search the Rulebook policy database for relevant documents.

    Args:
        query: Natural-language query about city policy or zoning.
        n_results: Number of results to return. Defaults to 5.

    Returns:
        A list of dictionaries containing:
            - text (str): The document excerpt.
            - source (str): Source document name (e.g., 'zoning.pdf').
            - page (int/str): Page number.
            - relevance_score (float): Calculated relevance (1 - distance).
        If an error occurs or no collection is found, returns a diagnostic error.
    """
    collection = _get_collection()
    if collection is None:
        return [{"error": "Rulebook collection not found. Please ensure indexer has been run."}]

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    output: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        output.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "page": meta.get("page", "?"),
            "relevance_score": round(1 - dist, 4) if dist else None,
        })

    return output
