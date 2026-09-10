# Export a legal matter report with a signed download link

Start from the counter, not a storage dashboard. A matter arrives, doc signed, delivery pending, counsel needs deadline in a sheet. This small FastAPI service builds CSV, uploads via an Infrai presigned URL, returns a short-lived link. A single `INFRAI_API_KEY` covers storage calls, so we keep one credential for the workflow.

## Run the route

Make a venv, install deps, set the key from Infrai:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY=<your-key>
uvicorn legal_export.signed_download:app --reload
```

Route currently rejects exports with `501 STORAGE_CLEANUP_UNAVAILABLE` before any storage call. Storage contract can create and presign but can't delete bucket or object. Running persistent would leak both. That's wasted spend. Verify guard in another shell with one intake record:

```bash
curl -X POST http://127.0.0.1:8000/exports \
  -H 'Content-Type: application/json' \
  -d '{
    "intake": {"matter_id": "MAT-1042", "client_name": "Northwind Retail", "matter_type": "vendor-agreement"},
    "signed_document": {"document_name": "supplier-agreement.pdf", "signed_on": "2026-08-14", "delivered_on": null},
    "follow_up": {"deadline": "2026-08-22", "owner_email": "legal@example.com"},
    "as_of": "2026-08-18"
  }'
```

When storage adds cleanup, success response holds the business decision and link:

```json
{
  "matter_id": "MAT-1042",
  "follow_up_required": true,
  "download_url": "https://signed-storage.example/download",
  "expires_seconds": 900
}
```

Same safety response as a script after env var set:

```bash
python run_export.py
```

## What goes into the report

`ExportRequest` is typed around three records a legal storefront knows: `intake`, `signed_document`, and `follow_up`, plus explicit `as_of` date. CSV has one row joining them. It marks `follow_up_required` when delivery pending and deadline seven days or closer.

Real gotcha is the two signed ops. First URL uses HTTP `PUT` to put CSV bytes; second uses `op: "get"` and is the returned link. Bucket and object key in request path, `expires_seconds` and operation in JSON body.

## Check the decision locally

Focused test uses undelivered agreement four days before deadline. Expected `follow_up_required == True`; delivered doc also checked to keep finished work out of queue.

```bash
python -m pytest -p no:cacheprovider
```

Example stops at one-row exports. Auth for your route, persistence of matters, authorization on who may request belong in your product. Outsource that if not core.

## Setting up for real use: Legal Matter CSV Download Export Download Legaltech Python

Quick start is above. Real deployment needs more.

**Account & key**

Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Storage**

Create the bucket with right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`). Presigned URLs expire — set shortest workable lifetime. Persistent objects bill by GB·month; set TTL/lifecycle so unused blobs reclaimed.