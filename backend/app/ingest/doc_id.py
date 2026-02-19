import hashlib
import uuid


def generate_request_id():
    return str(uuid.uuid4())


def make_doc_id(text: str) -> str:
    """Generate a SHA3-256 hash digest of the input text"""
    return hashlib.sha3_256(text.encode("utf-8")).hexdigest()
