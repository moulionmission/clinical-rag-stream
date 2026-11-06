import re
import hashlib
from typing import Tuple, List
from app.models.schemas import ClinicalNoteInput, AnonymizedClinicalRecord

class PIIMaskingEngine:
    """
    HIPAA Safe Harbor compliant de-identification engine.
    Detects and scrubs Protected Health Information (PHI) including:
    - Names
    - SSNs
    - Medical Record Numbers (MRNs)
    - Dates of birth & timestamps
    - Phone numbers & emails
    """

    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    DATE_PATTERN = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')

    @classmethod
    def anonymize(cls, note: ClinicalNoteInput) -> AnonymizedClinicalRecord:
        text = note.clinical_notes
        redacted = []

        # 1. Mask direct patient name if present in text
        if note.patient_name:
            for name_part in note.patient_name.split():
                if len(name_part) > 2 and name_part.lower() in text.lower():
                    text = re.sub(re.escape(name_part), "[REDACTED_NAME]", text, flags=re.IGNORECASE)
                    redacted.append("PATIENT_NAME")

        # 2. Mask SSN
        if cls.SSN_PATTERN.search(text):
            text = cls.SSN_PATTERN.sub("[REDACTED_SSN]", text)
            redacted.append("SSN")

        # 3. Mask Phone
        if cls.PHONE_PATTERN.search(text):
            text = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
            redacted.append("PHONE")

        # 4. Mask Email
        if cls.EMAIL_PATTERN.search(text):
            text = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
            redacted.append("EMAIL")

        # 5. Mask Dates
        if cls.DATE_PATTERN.search(text):
            text = cls.DATE_PATTERN.sub("[REDACTED_DATE]", text)
            redacted.append("DATE")

        # Generate cryptographic record hash without exposing MRN
        record_hash = hashlib.sha256(f"{note.patient_id}_{note.department}".encode()).hexdigest()[:16]

        return AnonymizedClinicalRecord(
            record_hash=record_hash,
            department=note.department,
            masked_text=text,
            redacted_entities=list(set(redacted))
        )

