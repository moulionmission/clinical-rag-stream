from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ClinicalNoteInput(BaseModel):
    patient_id: str = Field(..., description="Unique Patient Identifier (MRN)")
    patient_name: str = Field(..., description="Full Name of the Patient")
    ssn: Optional[str] = Field(None, description="Patient SSN")
    dob: Optional[str] = Field(None, description="Date of Birth")
    phone: Optional[str] = Field(None, description="Contact Phone")
    clinical_notes: str = Field(..., description="Unstructured clinical physician notes")
    department: str = Field(..., description="Clinical department or specialty")

class AnonymizedClinicalRecord(BaseModel):
    record_hash: str
    department: str
    masked_text: str
    redacted_entities: List[str]
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    vector_id: Optional[str] = None

class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="Clinical inquiry or diagnostic query")
    top_k: int = Field(default=3, description="Number of context records to retrieve")

class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    retrieved_contexts: List[Dict[str, Any]]
    confidence_score: float
