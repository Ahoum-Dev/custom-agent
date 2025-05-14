# RAG-Enabled Voice Agent

This project adds Retrieval-Augmented Generation (RAG) capabilities to the Ahoum Voice Agent, allowing it to leverage a knowledge base stored in MongoDB Atlas Vector Search to provide context-aware responses.

## Setup

### Prerequisites

1. MongoDB Atlas account with Vector Search enabled
2. Python 3.8+
3. LiveKit account (for voice agent functionality)

### Environment Variables

Create a `.env` file in the `agent` directory with the following variables:

```
# MongoDB Connection
MONGODB_CONNECTION_STRING=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority

# LiveKit Connection (already configured in your existing setup)
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

### Installation

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up MongoDB Atlas Vector Search:
   - Create a new MongoDB Atlas cluster
   - Enable Vector Search capability
   - Create a database called `ahoum_db`
   - Create a collection called `knowledge_base`
   - Create a vector search index on the `embedding` field

3. Populate the vector database with initial data:

```bash
python populate_vector_db.py
```

4. Verify the setup by running the agent:

```bash
python main.py
```

## How It Works

1. The agent uses RAG (Retrieval-Augmented Generation) to enhance its responses:
   - When a user asks a question, the agent first creates an embedding of the question
   - It searches the MongoDB Atlas Vector Search for relevant information
   - The retrieved context is provided to the LLM to generate a more informed response

2. The knowledge base contains information relevant to spiritual and meditation topics:
   - Basic meditation concepts
   - Mindfulness practices
   - Breathing techniques
   - Spiritual growth
   - And more...

3. You can add more knowledge to the database by:
   - Adding entries to the `SAMPLE_DOCUMENTS` in `populate_vector_db.py`
   - Creating a custom script to import knowledge from other sources

## Customization

### Adding Custom Knowledge

To add custom knowledge to the vector database:

1. Modify the `SAMPLE_DOCUMENTS` list in `populate_vector_db.py` or create a new list
2. Run the script to add the new documents to the database:

```bash
python populate_vector_db.py
```

### Adjusting RAG Parameters

You can tune the RAG behavior by modifying these parameters:

- In `rag_utils.py` - `RAGContextProvider.get_context`:
  - Adjust `limit` parameter to control how many documents to retrieve
  - Modify how conversation history is used for context

- In `main.py` - `Assistant.on_message`:
  - Change how the retrieved context is incorporated into the prompt

## Troubleshooting

### MongoDB Connection Issues

- Ensure your IP address is whitelisted in MongoDB Atlas
- Verify your connection string is correct
- Check that the database and collection names match your configuration

### Vector Search Not Working

- Ensure the vector search index is properly created in MongoDB Atlas
- Verify the dimension of your embeddings matches the index configuration
- Check the MongoDB logs for any errors related to vector search

### Model Loading Issues

- Ensure you have enough RAM to load the embedding model
- Consider using a smaller model if memory is limited 