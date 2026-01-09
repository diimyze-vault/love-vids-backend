from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from app.core.security import get_current_user_id
from app.core.storage import storage_service
from app.schemas.responses import UnifiedResponse

router = APIRouter()

@router.get("/upload-url")
async def get_upload_url(
    filename: str,
    content_type: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL to upload a file directly to Backblaze B2
    """
    try:
        # Create a unique path for the user's file
        object_name = f"users/{current_user_id}/uploads/{filename}"
        
        result = storage_service.generate_upload_url(
            object_name=object_name,
            content_type=content_type
        )
        
        return UnifiedResponse(
            status="success",
            message="Upload URL generated",
            data={
                "upload_url": result["url"],
                "file_url": result["file_url"],
                "object_name": object_name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Proxy upload to B2 to avoid CORS issues
    """
    try:
        object_name = f"users/{current_user_id}/uploads/{file.filename}"
        file_url = storage_service.upload_file(
            file.file,
            object_name=object_name,
            content_type=file.content_type
        )
        
        return UnifiedResponse(
            status="success",
            message="File uploaded successfully",
            data={
                "file_url": file_url,
                "object_name": object_name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
