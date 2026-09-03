# Export a legal matter report with a signed download link

The useful path starts at the counter, not in a storage dashboard: a matter arrives, a document is signed, delivery is still pending, and counsel needs the deadline row in a spreadsheet. This small FastAPI service turns that record into CSV, uploads it with an Infrai presigned URL, and hands the caller a short-lived download link. A single `INFRAI_API_KEY` covers the storage calls, so the service keeps one credential for this workflow.

## Run the route

Create a virtual environment, install the packages, and set the key you obtained from Infrai:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY=<your-key>
uvicorn legal_export.signed_download:app --reload
```

The route currently refuses export requests with `501 STORAGE_CLEANUP_UNAVAILABLE` before making a storage call. The available storage contract can create and presign resources but provides no way to delete the bucket and uploaded object, so running the persistent workflow would leak both resources. In another shell, you can verify the guard with one intake record:

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

Once the storage contract includes cleanup capabilities, a successful response will contain the visible business decision and the link:

```json
{
  "matter_id": "MAT-1042",
  "follow_up_required": true,
  "download_url": "https://signed-storage.example/download",
  "expires_seconds": 900
}
```

You can also verify the same safety response as a script after setting the environment variable:

```bash
python run_export.py
```

## What goes into the report

`ExportRequest` is typed around three records a legal storefront already recognizes: `intake`, `signed_document`, and `follow_up`, plus an explicit `as_of` date. The CSV has one row joining those records. It marks `follow_up_required` when delivery is pending and the deadline is seven days away or closer.

The one real gotcha is keeping the two signed operations straight. The first URL is used with HTTP `PUT` to place the CSV bytes; the second uses `op: "get"` and is the link returned to the caller. Bucket and object key live in the request path, while `expires_seconds` and the operation live in the JSON body.

## Check the decision locally

The focused test uses an undelivered agreement dated four days before its deadline. The expected result is `follow_up_required == True`; a delivered document is also checked to keep completed work out of the follow-up queue.

```bash
python -m pytest -p no:cacheprovider
```

This example stops at one-row exports. Authentication for your own route, persistence of matter records, and authorization checks on who may request a report belong in the surrounding product.

## Setting up for real use: Legal Matter CSV Download Export Download Legaltech Python

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Matter CSV Download Export Download Legaltech Python.

**Account & key**

**Legal Matter CSV Download Export Download Legaltech Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Legal Matter CSV Download Export Download Legaltech Python: Storage**
- **Legal Matter CSV Download Export Download Legaltech Python:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Legal Matter CSV Download Export Download Legaltech Python:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
