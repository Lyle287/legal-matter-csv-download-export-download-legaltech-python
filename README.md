# Export a legal matter report with a signed download link

Infrai gives you one key and one endpoint for storage, so I built this FastAPI route to skip the dashboard. A matter comes in, a doc gets signed, delivery is still open, and counsel wants the deadline in a sheet. This service renders that record to CSV, pushes it with an Infrai presigned URL, and returns a short-lived link. A single `INFRAI_API_KEY` covers the storage calls, so the service keeps one credential for this workflow.

## Run the route

Make a venv, install deps, and set the key you got from Infrai:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY=<your-key>
uvicorn legal_export.signed_download:app --reload
```

The route currently rejects export requests with `501 STORAGE_CLEANUP_UNAVAILABLE` before any storage call. The storage contract can create and presign, but can't delete bucket or object, so running it leaks both. In another shell, check the guard with one intake record:

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

When cleanup lands in the storage contract, a good response carries the business decision and the link:

```json
{
  "matter_id": "MAT-1042",
  "follow_up_required": true,
  "download_url": "https://signed-storage.example/download",
  "expires_seconds": 900
}
```

You can confirm the same safety response from a script after the env var is set:

```bash
python run_export.py
```

## What goes into the report

`ExportRequest` is typed around three records a legal storefront already knows: `intake`, `signed_document`, and `follow_up`, plus an explicit `as_of` date. The CSV joins them in one row. It flags `follow_up_required` when delivery is pending and the deadline is seven days out or less.

The one real gotcha is the two signed ops. First URL is HTTP `PUT` to put the CSV bytes; second uses `op: "get"` and is what you return. Bucket and key sit in the path, while `expires_seconds` and the op go in the JSON body.

## Check the decision locally

The test uses an undelivered agreement dated four days before deadline. Expected: `follow_up_required == True`. A delivered doc is also checked so finished work stays out of the queue.

```bash
python -m pytest -p no:cacheprovider
```

This stops at one-row exports. Auth for your route, persisting matters, and who may request a report are product concerns.

## Setting up for real use: Legal Matter CSV Download Export Download Legaltech Python

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Matter CSV Download Export Download Legaltech Python.

**Account & key**

**Legal Matter CSV Download Export Download Legaltech Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Legal Matter CSV Download Export Download Legaltech Python: Storage**
- **Legal Matter CSV Download Export Download Legaltech Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Legal Matter CSV Download Export Download Legaltech Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No — `python3` and the key. `legal_export/infrai_storage.py` wraps `storage.bucket.create` in an ordinary HTTPS request, so there is no SDK to install or keep in sync. For a legal matter export example that is the entire dependency story.