import os
from typing import List, Dict, Any, Optional
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

class MongoDBVectorStore:
    """A class to handle interactions with MongoDB Atlas Vector Search"""
    
    def __init__(self, connection_string: Optional[str] = None, db_name: str = "ahoum_db", collection_name: str = "knowledge_base"):
        """Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string with credentials
            db_name: Database name
            collection_name: Collection name for the vector store
        """
        # Use provided connection string or get from environment variable
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("MongoDB connection string not found. Please provide it or set MONGODB_CONNECTION_STRING environment variable.")
        
        # Connect to MongoDB
        self.client = MongoClient(self.connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        
        # Ensure vector search index exists
        self._ensure_vector_index()
    
    def _ensure_vector_index(self):
        """Ensure the vector search index exists in MongoDB Atlas"""
        # Check if the vector index exists, if not, create it
        index_info = self.collection.index_information()
        vector_index_name = "vector_index"
        
        if vector_index_name not in index_info:
            try:
                # Try to create a standard index on the embedding field
                # This won't enable vector search but will at least index the field
                self.collection.create_index(
                    [("embedding", 1)],  # Regular index, not TEXT or vector
                    name=vector_index_name
                )
                print(f"Created standard index '{vector_index_name}' (not a vector index)")
                print("Note: Vector search will be performed using in-memory similarity calculation")
            except Exception as e:
                print(f"Warning: Could not create index: {e}")
                print("Vector search will use in-memory computation")
    
    def add_document(self, text: str, metadata: Dict[str, Any], embedding: List[float]):
        """Add a document to the vector store
        
        Args:
            text: The text of the document
            metadata: Additional metadata for the document
            embedding: Vector embedding of the document
        
        Returns:
            The ID of the inserted document
        """
        document = {
            "text": text,
            "metadata": metadata,
            "embedding": embedding
        }
        
        result = self.collection.insert_one(document)
        return result.inserted_id
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add multiple documents to the vector store
        
        Args:
            documents: List of documents, each with text, metadata, and embedding
        
        Returns:
            The IDs of the inserted documents
        """
        if not documents:
            return []
        
        # Ensure each document has the required fields
        for doc in documents:
            if not all(key in doc for key in ["text", "metadata", "embedding"]):
                raise ValueError("Each document must contain 'text', 'metadata', and 'embedding' fields")
        
        result = self.collection.insert_many(documents)
        return result.inserted_ids
    
    def search(self, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using vector search
        
        Args:
            query_embedding: The vector embedding of the search query
            limit: Maximum number of results to return
        
        Returns:
            List of documents sorted by similarity
        """
        try:
            # Check if we're using MongoDB Atlas
            try:
                # Try Atlas vector search first
                query_vector = np.array(query_embedding, dtype=np.float32)
                pipeline = [
                    {
                        "$search": {
                            "index": "vector_index",
                            "vectorSearch": {
                                "queryVector": query_vector.tolist(),
                                "path": "embedding",
                                "numCandidates": limit * 10,
                                "limit": limit
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "text": 1,
                            "metadata": 1,
                            "score": {"$meta": "searchScore"}
                        }
                    }
                ]
                
                results = list(self.collection.aggregate(pipeline))
                if results:
                    return results
                
            except Exception as e:
                # If not Atlas or Atlas search fails, log the error
                print(f"Atlas vector search not available: {e}")
                print("Falling back to manual vector similarity search")
            
            # Manual vector similarity search for non-Atlas MongoDB
            # Fetch all documents (with a reasonable limit)
            all_docs = list(self.collection.find({}, {"_id": 0, "text": 1, "metadata": 1, "embedding": 1}).limit(1000))
            if not all_docs:
                return []
                
            # Calculate cosine similarity for each document
            query_vector = np.array(query_embedding, dtype=np.float32)
            results_with_scores = []
            
            for doc in all_docs:
                if "embedding" not in doc:
                    continue
                
                doc_vector = np.array(doc["embedding"], dtype=np.float32)
                
                # Calculate cosine similarity
                similarity = np.dot(query_vector, doc_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                )
                
                results_with_scores.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": float(similarity)
                })
            
            # Sort by similarity score (highest first)
            results_with_scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top results
            return results_with_scores[:limit]
            
        except Exception as e:
            print(f"Error during vector search: {e}")
            return []

class RAGContextProvider:
    """Provides context for the agent using RAG"""
    
    def __init__(self, embedding_model_name: str = "groq/embedding"):
        """Initialize the RAG context provider
        
        Args:
            embedding_model_name: The name of the embedding model to use
        """
        self.vector_store = MongoDBVectorStore()
        self.embedding_model_name = embedding_model_name
        
        # Lazy load the embedding model when needed
        self._embedding_model = None
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model"""
        if self._embedding_model is None:
            # Here we would typically load a model like sentence-transformers
            # For simplicity, we'll just use a dummy function
            # In a real implementation, you'd use a proper embedding model
            print(f"Loading embedding model: {self.embedding_model_name}")
            
            # This is a placeholder - in a real implementation, use:
            # from sentence_transformers import SentenceTransformer
            # self._embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Dummy function for demo purposes
            self._embedding_model = lambda text: np.random.rand(384).astype(np.float32)
        
        return self._embedding_model
    
    def get_embedding(self, text: str) -> List[float]:
        """Get the embedding for a text
        
        Args:
            text: The text to embed
        
        Returns:
            Vector embedding of the text
        """
        # In a real implementation, use the model to get embeddings
        embedding = self.embedding_model(text)
        return embedding.tolist()
    
    def get_context(self, query: str, conversation_history: List[str], limit: int = 3) -> str:
        """Get relevant context for a query using RAG
        
        Args:
            query: The current query
            conversation_history: List of previous conversation turns
            limit: Maximum number of context documents to retrieve
        
        Returns:
            Concatenated context string
        """
        # Combine query with recent conversation history for better context
        context_query = query
        if conversation_history:
            # Use the last 3 turns of conversation for context
            recent_history = conversation_history[-3:]
            context_query = " ".join(recent_history + [query])
        
        # Get embedding for the query
        query_embedding = self.get_embedding(context_query)
        
        # Search for relevant documents
        results = self.vector_store.search(query_embedding, limit=limit)
        
        if not results:
            return ""
        
        # Format the results into a context string
        context_parts = []
        for i, doc in enumerate(results):
            context_parts.append(f"[{i+1}] {doc['text']}")
        
        return "\n\n".join(context_parts) 