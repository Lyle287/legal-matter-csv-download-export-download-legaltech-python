from fastapi import FastAPI, HTTPException

from .matter_report import ExportRequest, ExportResult

app = FastAPI(title="Legal matter export")


@app.post("/exports", response_model=ExportResult)
def export_matter(request: ExportRequest) -> ExportResult:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "STORAGE_CLEANUP_UNAVAILABLE",
            "message": (
                "Export storage is disabled because the available capabilities "
                "cannot delete the bucket and object created by this workflow"
            ),
        },
    )
