# RAG-Enabled Voice Agent

This project adds Retrieval-Augmented Generation (RAG) capabilities to the Ahoum Voice Agent, allowing it to leverage a knowledge base stored in MongoDB Atlas Vector Search to provide context-aware responses.

## Setup

### Prerequisites

1. MongoDB database (can be MongoDB Atlas or self-hosted)
2. Python 3.8+
3. LiveKit account (for voice agent functionality)

### Environment Variables

Create a `.env` file in the `agent` directory with the following variables:

```
# MongoDB Connection
MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/ahoum_db?directConnection=true

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

2. Set up MongoDB:
   - If using MongoDB Atlas:
     - Create a new MongoDB Atlas cluster
     - Enable Vector Search capability
     - Create a database called `ahoum_db`
     - Create a collection called `knowledge_base`
     - Create a vector search index on the `embedding` field
   - If using self-hosted MongoDB:
     - Ensure MongoDB is running and accessible
     - The code will automatically use an in-memory vector similarity search

3. Populate the vector database with initial data:

```bash
python populate_vector_db.py
```

4. Verify the setup by running the agent:

```bash
python main.py
```

## Docker Deployment

This project can be easily deployed using Docker and Docker Compose.

### Docker Environment Variables

Create a `.env` file at the root of the project with the following variables:

```
# LiveKit
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
NEXT_PUBLIC_LIVEKIT_URL=your_livekit_url

# Groq API Key
GROQ_API_KEY=your_groq_api_key

# MongoDB (optional - only if using external MongoDB)
# MONGODB_CONNECTION_STRING=mongodb://username:password@host:port/dbname
```

### Running with Docker Compose

To start all services (frontend, agent, and MongoDB):

```bash
docker-compose up -d
```

This will:
1. Start a MongoDB container
2. Start the agent connected to MongoDB
3. Initialize the vector database with sample data
4. Start the frontend application

### Accessing the Application

- Frontend: http://localhost:3000
- Agent: http://localhost:8000

### Using an External MongoDB

If you want to use an external MongoDB instance (self-hosted or Atlas) instead of the Docker container:

1. Uncomment and set the `MONGODB_CONNECTION_STRING` in your `.env` file
2. For MongoDB Atlas, make sure Vector Search is enabled
3. For self-hosted MongoDB, the agent will use in-memory vector similarity

## How It Works

1. The agent uses RAG (Retrieval-Augmented Generation) to enhance its responses:
   - When a user asks a question, the agent first creates an embedding of the question
   - It searches the MongoDB for relevant information
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