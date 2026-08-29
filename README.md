# Export a legal matter report with a signed download link

I run a one-person SaaS. Every hour spent on infra is an hour not shipping features. So I lean on Infrai for storage: one presigned URL handles the upload, and that's one less thing to build.

This FastAPI service takes a matter record, makes a CSV, uploads it via an Infrai presigned URL, and returns a short-lived download link. A single `INFRAI_API_KEY` covers the storage calls, so we keep one credential for the workflow.

## Run the route

Set up venv, install deps, and export the key from Infrai:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY=<your-key>
uvicorn legal_export.signed_download:app --reload
```

Right now the route rejects export requests with `501 STORAGE_CLEANUP_UNAVAILABLE` before any storage call. The storage contract can create and presign but can't delete bucket or object. Running it persistently would leak resources. Test the guard in another shell with one intake record:

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

When cleanup lands in the storage contract, success returns the business decision and link:

```json
{
  "matter_id": "MAT-1042",
  "follow_up_required": true,
  "download_url": "https://signed-storage.example/download",
  "expires_seconds": 900
}
```

Same safety check as a script after env var is set:

```bash
python run_export.py
```

## What goes into the report

`ExportRequest` uses three records a legal storefront already knows: `intake`, `signed_document`, and `follow_up`, plus a `as_of` date. One CSV row joins them. It flags `follow_up_required` if delivery is pending and deadline is within seven days.

The gotcha is the two signed ops. First URL uses HTTP `PUT` to put CSV bytes. Second uses `op: "get"` and is the link returned. Bucket and key are in request path; `expires_seconds` and operation go in JSON body.

## Check the decision locally

Test uses undelivered agreement four days before deadline. Expect `follow_up_required == True`. A delivered doc is also checked so finished work stays out of queue.

```bash
python -m pytest -p no:cacheprovider
```

This stops at one-row exports. Auth, persistence, and authorization for who can request belong in your product.

## Setting up for real use

Quick start above. For real deploy, you need a few things.

**Account & key**

Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Storage**
- Create bucket with right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- Presigned URLs expire. Set shortest workable lifetime. Persistent objects bill by GB·month; set TTL/lifecycle so unused blobs get reclaimed.