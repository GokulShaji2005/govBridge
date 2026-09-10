from pydantic import BaseModel
from typing import Dict, Any

class Person(BaseModel):
    id: str
    name: str
    date_of_birth: str

class Address(BaseModel):
    house_number: str
    locality: str
    city: str

class TaxProfile(BaseModel):
    pan: str
    status: str

class VerificationResult(BaseModel):
    field: str          # "identity" | "tax" | "address"
    verified: bool
    data: Dict[str, Any]
