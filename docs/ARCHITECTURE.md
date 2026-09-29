# Scheme Setu AI V2 — build notes

## Core architecture

Responsive React frontend → FastAPI → domain services → AI orchestrator → RAG retriever + tools → optional Gemini.

## Local RAG

The supplied 52 scheme records are indexed with a TF-IDF sparse vectorizer. This provides a local retrieval layer with no external vector database requirement. A future production deployment can swap the retriever for a managed embedding/vector service without changing the copilot contract.

## Voice

Browser Web Speech API is used for speech recognition where Chrome/Edge support it. Browser Speech Synthesis is used for read-aloud responses. This keeps the prototype install-light and avoids storing voice data on the server.

## Demo-data boundary

The supplied 52 schemes and 277 partner rows are retained as seed/demo data. The supplied partner URLs contain demo-style example values, so they must not be represented as live verified institutions.

## Application tracking

The roadmap UI is implemented. Live application-status tracking is intentionally left as an integration point requiring an authorized partner/department interface.
