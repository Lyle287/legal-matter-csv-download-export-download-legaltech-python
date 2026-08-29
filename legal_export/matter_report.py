from __future__ import annotations

import csv
import io
from datetime import date

from pydantic import BaseModel, Field


class MatterIntake(BaseModel):
    matter_id: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    matter_type: str = Field(min_length=1)


class SignedDelivery(BaseModel):
    document_name: str = Field(min_length=1)
    signed_on: date
    delivered_on: date | None = None


class DeadlineFollowUp(BaseModel):
    deadline: date
    owner_email: str = Field(min_length=3)


class ExportRequest(BaseModel):
    intake: MatterIntake
    signed_document: SignedDelivery
    follow_up: DeadlineFollowUp
    as_of: date


class ExportResult(BaseModel):
    matter_id: str
    follow_up_required: bool
    download_url: str
    expires_seconds: int


def follow_up_required(request: ExportRequest) -> bool:
    days_left = (request.follow_up.deadline - request.as_of).days
    return request.signed_document.delivered_on is None and days_left <= 7


def build_csv(request: ExportRequest) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "matter_id",
            "client_name",
            "matter_type",
            "document_name",
            "signed_on",
            "delivered_on",
            "deadline",
            "owner_email",
            "follow_up_required",
        ],
    )
    writer.writeheader()
    writer.writerow(
        {
            "matter_id": request.intake.matter_id,
            "client_name": request.intake.client_name,
            "matter_type": request.intake.matter_type,
            "document_name": request.signed_document.document_name,
            "signed_on": request.signed_document.signed_on.isoformat(),
            "delivered_on": (
                request.signed_document.delivered_on.isoformat()
                if request.signed_document.delivered_on
                else "pending"
            ),
            "deadline": request.follow_up.deadline.isoformat(),
            "owner_email": request.follow_up.owner_email,
            "follow_up_required": str(follow_up_required(request)).lower(),
        }
    )
    return output.getvalue().encode("utf-8")

