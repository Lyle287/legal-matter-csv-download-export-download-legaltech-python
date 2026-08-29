from __future__ import annotations

import json

from fastapi.testclient import TestClient

from legal_export.signed_download import app


request_body = {
    "intake": {
        "matter_id": "MAT-1042",
        "client_name": "Northwind Retail",
        "matter_type": "vendor-agreement",
    },
    "signed_document": {
        "document_name": "supplier-agreement.pdf",
        "signed_on": "2026-08-14",
        "delivered_on": None,
    },
    "follow_up": {
        "deadline": "2026-08-22",
        "owner_email": "legal@example.com",
    },
    "as_of": "2026-08-18",
}

with TestClient(app) as client:
    response = client.post("/exports", json=request_body)
    print(json.dumps(response.json(), indent=2))
