import pytest
import asyncio
from app.models.schemas import ClinicalNoteInput, RAGQueryRequest
from app.pipeline.masking import PIIMaskingEngine
from app.pipeline.vector_store import VectorStore
from app.pipeline.stream_engine import KafkaStreamSimulator
from app.pipeline.rag_engine import ClinicalRAGEngine

def test_pii_masking():
    raw_note = ClinicalNoteInput(
        patient_id="MRN-10023",
        patient_name="Alice Smith",
        ssn="999-12-3456",
        dob="05/14/1988",
        phone="555-123-4567",
        clinical_notes="Patient Alice Smith (SSN: 999-12-3456) diagnosed with acute bronchitis on 05/14/2026.",
        department="Pulmonology"
    )

    anonymized = PIIMaskingEngine.anonymize(raw_note)

    assert "Alice" not in anonymized.masked_text
    assert "999-12-3456" not in anonymized.masked_text
    assert "[REDACTED_NAME]" in anonymized.masked_text
    assert "[REDACTED_SSN]" in anonymized.masked_text
    assert len(anonymized.record_hash) > 0

@pytest.mark.asyncio
async def test_streaming_throughput_benchmark():
    store = VectorStore(dimension=32)
    stream = KafkaStreamSimulator(vector_store=store, batch_size=2000)

    result = await stream.benchmark_throughput(total_events=20000)
    assert result["total_events_processed"] == 20000
    assert result["events_per_second"] > 10000 # High throughput validation

def test_rag_query_workflow():
    store = VectorStore(dimension=32)
    rag = ClinicalRAGEngine(vector_store=store)

    note = ClinicalNoteInput(
        patient_id="PT-55",
        patient_name="Bob Jones",
        clinical_notes="Patient responds well to beta blockers with normalized arterial pressure.",
        department="Cardiology"
    )
    anon = PIIMaskingEngine.anonymize(note)
    store.upsert(anon.record_hash, anon.masked_text, {"department": "Cardiology", "masked_text": anon.masked_text})

    query = RAGQueryRequest(question="How did the patient respond to beta blockers?", top_k=1)
    response = rag.query(query)

    assert len(response.retrieved_contexts) == 1
    assert "beta blockers" in response.retrieved_contexts[0]["context_snippet"]

