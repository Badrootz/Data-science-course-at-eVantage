import os
import time
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE_FILE = os.path.join(BASE_DIR, "chunks_with_embeddings.pkl")
DEFAULT_SCRAPED_DIR = os.path.join(BASE_DIR, "scraped_pages")

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

from scraper import scrape_pages
from chunker import chunk_all_documents


class RAGSystem:
    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        overlap: int = 100,
        cache_file: str = None,
        scraped_pages_dir: str = None,
        force_reindex: bool = False
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.cache_file = cache_file if cache_file else DEFAULT_CACHE_FILE
        self.scraped_pages_dir = scraped_pages_dir if scraped_pages_dir else DEFAULT_SCRAPED_DIR
        
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.chunks = []
        self.embeddings = None
        
        self._load_or_create_index(force_reindex=force_reindex)
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def _load_or_create_index(self, force_reindex: bool = False):
        if not force_reindex and os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                cached_data = pickle.load(f)
                self.chunks = cached_data["chunks"]
                self.embeddings = cached_data["embeddings"]
            return

        if not os.path.exists(self.scraped_pages_dir) or not os.listdir(self.scraped_pages_dir):
            scrape_pages(output_dir=self.scraped_pages_dir)

        scraped_pages_dict = {}
        for fname in os.listdir(self.scraped_pages_dir):
            if fname.endswith(".txt"):
                fpath = os.path.join(self.scraped_pages_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    scraped_pages_dict[fname] = f.read()

        self.chunks = chunk_all_documents(scraped_pages_dict, chunk_size=self.chunk_size, overlap=self.overlap)
        texts = [c["chunk_text"] for c in self.chunks]
        self.embeddings = np.array(
            self.embedding_model.encode(texts, show_progress_bar=False, normalize_embeddings=True),
            dtype=np.float32
        )

        with open(self.cache_file, "wb") as f:
            pickle.dump({
                "chunks": self.chunks,
                "embeddings": self.embeddings,
                "chunk_size": self.chunk_size,
                "overlap": self.overlap
            }, f)

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        """Embeds query and computes top-k cosine similarity search."""
        query_vec = np.array(
            self.embedding_model.encode([query], normalize_embeddings=True)[0],
            dtype=np.float32
        )
        similarities = np.dot(self.embeddings, query_vec)
        top_k_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx, sim_idx in enumerate(top_k_indices):
            chunk_copy = self.chunks[sim_idx].copy()
            chunk_copy["similarity_score"] = float(similarities[sim_idx])
            results.append(chunk_copy)
        return results

    def generate_response(
        self,
        query: str,
        retrieved_chunks: list[dict],
        enforce_grounding: bool = True,
        model_name: str = "gemma-4-31b-it"
    ) -> str:
        """Generates response using Google GenAI API with strict context grounding option."""
        if not self.client:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
            else:
                return "Error: GEMINI_API_KEY is not set."

        if enforce_grounding:
            formatted_context = ""
            for idx, c in enumerate(retrieved_chunks, 1):
                formatted_context += f"{idx}. [Source: {c['source_page']}]\n{c['chunk_text']}\n\n"

            prompt = (
                "You are a Formula 1 expert assistant. Answer the question using ONLY "
                "the context provided below. If the answer is not in the context, say "
                "'I don't have enough information in my knowledge base to answer this.' "
                "Do not use your own training knowledge beyond what is in the context.\n\n"
                f"Context:\n{formatted_context}\n"
                f"Question: {query}\n\n"
                "Answer:"
            )
        else:
            prompt = (
                "You are a Formula 1 expert assistant. Answer the following question:\n\n"
                f"Question: {query}\n\n"
                "Answer:"
            )

        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            answer = response.text
        except Exception as e:
            answer = f"Gemini API Error: {str(e)}"

        # Pacing sleep to keep TPM usage smoothly under rate limits
        time.sleep(4.0)
        return answer
