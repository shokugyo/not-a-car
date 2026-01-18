"""地点知識ベース（RAG）モジュール"""

from .search import KnowledgeSearch, get_knowledge_search

# ベクトルストアはchromadbがインストールされている場合のみ利用可能
try:
    from .vector_store import LocationVectorStore, get_vector_store, CHROMADB_AVAILABLE
except ImportError:
    LocationVectorStore = None  # type: ignore
    get_vector_store = None  # type: ignore
    CHROMADB_AVAILABLE = False

__all__ = [
    "LocationVectorStore",
    "get_vector_store",
    "KnowledgeSearch",
    "get_knowledge_search",
    "CHROMADB_AVAILABLE",
]
