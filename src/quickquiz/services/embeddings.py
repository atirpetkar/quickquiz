"""Embedding service for generating text embeddings."""


from openai import AsyncOpenAI

from ..core.config import settings
from ..core.exceptions import QuickQuizException


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-ada-002"
        self.embedding_dimension = 1536

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for a single text."""

        try:
            if not text.strip():
                return None

            response = await self.client.embeddings.create(model=self.model, input=text)

            return response.data[0].embedding

        except Exception as e:
            raise QuickQuizException(f"Failed to generate embedding: {str(e)}")

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float] | None]:
        """Generate embeddings for multiple texts in batch."""

        try:
            # Filter out empty texts
            non_empty_texts = [text for text in texts if text.strip()]

            if not non_empty_texts:
                return [None] * len(texts)

            response = await self.client.embeddings.create(
                model=self.model, input=non_empty_texts
            )

            embeddings = [data.embedding for data in response.data]

            # Map back to original positions
            result = []
            embedding_idx = 0

            for text in texts:
                if text.strip():
                    result.append(embeddings[embedding_idx])
                    embedding_idx += 1
                else:
                    result.append(None)

            return result

        except Exception as e:
            raise QuickQuizException(f"Failed to generate batch embeddings: {str(e)}")

    async def similarity_search(
        self,
        query_embedding: list[float],
        candidate_embeddings: list[list[float]],
        top_k: int = 5,
    ) -> list[tuple]:
        """Find most similar embeddings using cosine similarity."""

        try:
            import numpy as np

            # Convert to numpy arrays
            query_vec = np.array(query_embedding)
            candidate_vecs = np.array(candidate_embeddings)

            # Compute cosine similarities
            similarities = np.dot(candidate_vecs, query_vec) / (
                np.linalg.norm(candidate_vecs, axis=1) * np.linalg.norm(query_vec)
            )

            # Get top-k similar items
            top_indices = np.argsort(similarities)[::-1][:top_k]

            return [(idx, similarities[idx]) for idx in top_indices]

        except Exception as e:
            raise QuickQuizException(f"Failed to perform similarity search: {str(e)}")

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.embedding_dimension
