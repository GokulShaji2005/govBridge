import httpx
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000/mock"

async def call_identity(citizen_id: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/identity/verify", json={"citizen_id": citizen_id}, timeout=10.0)
        res.raise_for_status()
        return res.json()

async def call_tax(pan: str) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/tax/verify", json={"pan": pan}, timeout=10.0)
        res.raise_for_status()
        return res.text  # returns raw XML text

async def call_municipality(owner_code: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/municipality/verify", json={"owner_code": owner_code}, timeout=10.0)
        res.raise_for_status()
        return res.json()  # returns legacy dict

async def call_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        res = await client.post(f"{BASE_URL}/business/register", json=payload, timeout=10.0)
        res.raise_for_status()
        return res.json()
