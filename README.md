# Tomo: Your Digital Pet with a Memory

## Overview

Tomo is a proof-of-concept for a digital pet with a persistent, searchable memory. It's an exploration of creating a conversational agent that can remember and recall past interactions, powered by a Retrieval-Augmented Generation (RAG) architecture.

The core idea is to give the digital pet a "memory" by converting conversations into storable, searchable vector embeddings. When you talk to Tomo, it searches its past memories for contextually relevant information and uses that to form a more informed and personal response.

## Features

*   **Persistent Memory:** Tomo stores all interactions in a PostgreSQL database, ensuring that no memory is lost.
*   **Contextual Conversations:** Tomo uses vector similarity search (`pgvector`) to find relevant memories and provide context-aware replies.
*   **Extensible Knowledge:** The system includes scrapers to pre-populate Tomo's memory with knowledge from external documents, such as scientific papers.
*   **LLM Integration:** Tomo leverages a Large Language Model (specifically, a local Llama C++ server) to generate high-quality text embeddings and conversational completions.

## Architecture

Tomo is built with the following components:

*   **Frontend:** A simple HTML and JavaScript interface for interacting with the pet.
*   **Backend:** A Python backend built with **FastAPI** that serves the API for the frontend.
*   **Database:** **PostgreSQL** with the `pgvector` extension for efficient vector similarity search.
*   **AI/ML:**
    *   **Llama C++ Server:** Used for generating vector embeddings and completing text.
    *   **Fallback Embedder:** A deterministic embedder is used as a fallback if the Llama server is not available.

All services are containerized and can be orchestrated using `docker-compose`.

## How It Works

The application follows a Retrieval-Augmented Generation (RAG) pipeline:

1.  **Input:** The user sends a message to Tomo through the web interface.
2.  **Embedding:** The FastAPI backend receives the message and uses the `llama_client` to convert the text into a vector embedding.
3.  **Storage:** This embedding, along with the original text, is stored as a "memory" in the PostgreSQL database.
4.  **Retrieval:** When generating a response, the system first creates an embedding of the user's latest message and searches the database for the most similar/relevant memories.
5.  **Generation:** The retrieved memories are passed to the Llama model as context, along with a prompt to generate a conversational reply.
6.  **Response:** The generated text is sent back to the user.

## Getting Started

To run Tomo, you will need to have Docker and Docker Compose installed.

1.  **Set up the Environment:**
    *   Copy the example environment files:
        ```bash
        cp .env.example .env
        cp backend/.env.example backend/.env
        ```
    *   Review and update the `.env` files with your specific configuration, such as database credentials.

2.  **Build and Run the Services:**
    ```bash
    docker-compose up --build
    ```

3.  **Access the Frontend:**
    *   Open your web browser and navigate to `http://localhost:8080` (or the port you have configured for the frontend).

4.  **(Optional) Run the Scrapers:**
    *   To pre-populate Tomo's memory, you can run the included scraper scripts. You will need to install the Python dependencies first:
        ```bash
        pip install -r requirements.txt
        ```
    *   Then, run the desired scraper:
        ```bash
        python open_access_scraper.py
        ```
