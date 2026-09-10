from xml.etree import ElementTree as ET
from canonical import Person, Address, TaxProfile

def map_identity(raw: dict) -> Person:
    return Person(
        id=raw["citizenId"],
        name=raw["name"],
        date_of_birth=raw["dateOfBirth"]
    )

def map_tax(raw_xml: str) -> TaxProfile:
    root = ET.fromstring(raw_xml.strip())
    pan_elem = root.find("PAN")
    status_elem = root.find("Status")
    pan = pan_elem.text if pan_elem is not None else ""
    status = status_elem.text if status_elem is not None else ""
    return TaxProfile(pan=pan, status=status)

def map_municipality(raw: dict) -> Address:
    return Address(
        house_number=raw["HOUSE_NO"],
        locality=raw["LOCALITY"],
        city="Kottayam"
    )
