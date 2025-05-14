"""
Script to populate the MongoDB vector database with initial data.
This script will create embeddings for a set of documents and add them to the database.
"""

import os
import sys
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_utils import MongoDBVectorStore

# Load environment variables
load_dotenv()

# Sample spiritual and meditation knowledge
SAMPLE_DOCUMENTS = [
    {
        "text": "Meditation is a practice where an individual uses a technique – such as mindfulness, or focusing the mind on a particular object, thought, or activity – to train attention and awareness, and achieve a mentally clear and emotionally calm and stable state.",
        "metadata": {
            "category": "meditation",
            "source": "general knowledge",
            "importance": "high"
        }
    },
    {
        "text": "Mindfulness meditation involves paying attention to the present moment, deliberately and non-judgmentally. This practice has been shown to reduce stress, improve concentration, and increase self-awareness.",
        "metadata": {
            "category": "meditation",
            "source": "mindfulness practice",
            "importance": "high"
        }
    },
    {
        "text": "Breathing techniques are fundamental to many spiritual and meditation practices. Deep, conscious breathing can activate the parasympathetic nervous system, reducing stress and anxiety.",
        "metadata": {
            "category": "breathing",
            "source": "meditation techniques",
            "importance": "medium"
        }
    },
    {
        "text": "Spiritual growth often involves self-reflection and introspection. Taking time to examine your thoughts, feelings, and behaviors can lead to greater self-awareness and personal development.",
        "metadata": {
            "category": "spiritual growth",
            "source": "personal development",
            "importance": "high"
        }
    },
    {
        "text": "Gratitude practices have been shown to increase happiness and well-being. Taking time each day to acknowledge what you're grateful for can shift your perspective and improve your mood.",
        "metadata": {
            "category": "gratitude",
            "source": "positive psychology",
            "importance": "medium"
        }
    },
    {
        "text": "Journaling is a powerful tool for self-discovery and emotional processing. Writing down your thoughts and feelings can help you gain clarity and insight into your inner world.",
        "metadata": {
            "category": "journaling",
            "source": "self-reflection",
            "importance": "medium"
        }
    },
    {
        "text": "Setting intentions helps guide your actions and decisions toward your values and goals. Unlike goals, intentions focus on how you want to be, rather than what you want to achieve.",
        "metadata": {
            "category": "intentions",
            "source": "mindful living",
            "importance": "medium"
        }
    },
    {
        "text": "Compassion meditation involves cultivating feelings of goodwill, kindness, and warmth toward others. This practice can increase empathy and reduce negative emotions like anger and fear.",
        "metadata": {
            "category": "meditation",
            "source": "compassion practices",
            "importance": "high"
        }
    },
    {
        "text": "The concept of impermanence is central to many spiritual traditions. Recognizing that all things are transient can help you let go of attachments and accept change more gracefully.",
        "metadata": {
            "category": "impermanence",
            "source": "Buddhist philosophy",
            "importance": "high"
        }
    },
    {
        "text": "Self-compassion involves treating yourself with the same kindness and understanding that you would offer to a good friend. This practice can reduce self-criticism and increase emotional resilience.",
        "metadata": {
            "category": "self-compassion",
            "source": "positive psychology",
            "importance": "high"
        }
    }
]

def main():
    print("Starting to populate vector database...")
    
    # Load the sentence transformer model
    print("Loading embedding model...")
    model_name = "all-MiniLM-L6-v2"  # A good general-purpose embedding model
    model = SentenceTransformer(model_name)
    print(f"Model loaded: {model_name}")
    
    # Connect to MongoDB Vector Store
    vector_store = MongoDBVectorStore()
    
    # Create embeddings and insert documents
    print("Creating embeddings and inserting documents...")
    
    documents_with_embeddings = []
    for doc in SAMPLE_DOCUMENTS:
        # Generate embedding for the document text
        text = doc["text"]
        embedding = model.encode(text, convert_to_tensor=False).tolist()
        
        # Create document with embedding
        document = {
            "text": text,
            "metadata": doc["metadata"],
            "embedding": embedding
        }
        
        documents_with_embeddings.append(document)
    
    # Insert all documents at once
    inserted_ids = vector_store.add_documents(documents_with_embeddings)
    
    print(f"Successfully inserted {len(inserted_ids)} documents into the vector database")
    
    # Test a query
    print("\nTesting a query...")
    query = "How can meditation help me with stress?"
    query_embedding = model.encode(query, convert_to_tensor=False).tolist()
    
    results = vector_store.search(query_embedding, limit=2)
    
    print(f"Query: {query}")
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        print(f"Result {i+1}: {result['text'][:100]}...")
    
    print("\nPopulation complete!")

if __name__ == "__main__":
    main() 