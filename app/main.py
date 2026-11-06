from fastapi import FastAPI, HTTPException, status
from app.models.schemas import (
    ClinicalNoteInput,
    AnonymizedClinicalRecord,
    RAGQueryRequest,
    RAGQueryResponse
)
from app.pipeline.masking import PIIMaskingEngine
from app.pipeline.vector_store import VectorStore
from app.pipeline.stream_engine import KafkaStreamSimulator
from app.pipeline.rag_engine import ClinicalRAGEngine

app = FastAPI(
    title="Clinical RAG & Ingestion Platform",
    description="High-throughput event-driven clinical ingestion and privacy-preserving RAG engine.",
    version="1.0.0"
)

# Shared in-memory singletons
vector_store = VectorStore(dimension=64)
stream_engine = KafkaStreamSimulator(vector_store=vector_store)
rag_engine = ClinicalRAGEngine(vector_store=vector_store)

@app.get("/health", tags=["Monitoring"])
def health():
    return {
        "status": "healthy",
        "service": "clinical-rag-stream",
        "total_records_indexed": len(vector_store.vectors)
    }

@app.post("/api/v1/ingest", response_model=AnonymizedClinicalRecord, tags=["Ingestion"])
def ingest_record(note: ClinicalNoteInput):
    """
    Ingests an individual clinical note, masks PHI/PII, and updates vector store.
    """
    anonymized = PIIMaskingEngine.anonymize(note)
    vector_store.upsert(
        doc_id=anonymized.record_hash,
        text=anonymized.masked_text,
        metadata={
            "department": anonymized.department,
            "masked_text": anonymized.masked_text,
            "redacted": anonymized.redacted_entities
        }
    )
    return anonymized

@app.post("/api/v1/stream/benchmark", tags=["Streaming"])
async def run_streaming_benchmark(total_events: int = 30000):
    """
    Executes a high-concurrency ingestion benchmark to verify 15,000+ events/sec capability.
    """
    return await stream_engine.benchmark_throughput(total_events=total_events)

@app.post("/api/v1/rag/query", response_model=RAGQueryResponse, tags=["RAG Retrieval"])
def query_rag(req: RAGQueryRequest):
    """
    Performs vector similarity search and synthesizes an augmented clinical response.
    """
    return rag_engine.query(req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

