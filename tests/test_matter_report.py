from datetime import date

from fastapi.testclient import TestClient

from legal_export.matter_report import ExportRequest, follow_up_required
from legal_export.signed_download import app


def test_flags_undelivered_signed_document_inside_deadline_window() -> None:
    request = ExportRequest.model_validate(
        {
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
            "as_of": date(2026, 8, 18),
        }
    )

    assert follow_up_required(request) is True


def test_delivered_document_needs_no_follow_up() -> None:
    request = ExportRequest.model_validate(
        {
            "intake": {
                "matter_id": "MAT-1043",
                "client_name": "Contoso Shop",
                "matter_type": "lease-review",
            },
            "signed_document": {
                "document_name": "lease.pdf",
                "signed_on": "2026-08-12",
                "delivered_on": "2026-08-15",
            },
            "follow_up": {
                "deadline": "2026-08-20",
                "owner_email": "legal@example.com",
            },
            "as_of": "2026-08-18",
        }
    )

    assert follow_up_required(request) is False


def test_export_refuses_to_create_resources_without_cleanup() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/exports",
            json={
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
            },
        )

    assert response.status_code == 501
    assert response.json()["detail"]["code"] == "STORAGE_CLEANUP_UNAVAILABLE"
