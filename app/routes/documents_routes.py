from fastapi import APIRouter, File, UploadFile , Depends,HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from uuid import uuid4
import os
from datetime import datetime,timedelta
from app.models import doc_models
from sqlalchemy.orm import Session
from app.core.config import FILE_DIR,fernet
from app.database import get_db
from app.dependencies import get_current_user



documents_router=APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@documents_router.post("/upload")
async def upload_docs(file: UploadFile = File(...),db: Session = Depends(get_db),current_user: doc_models.User = Depends(get_current_user)):

    content = await file.read()
    encryted=fernet.encrypt(content)

    filepath = f"{FILE_DIR}/{uuid4()}_{file.filename}"
    with open(filepath, "wb") as f:
        f.write(encryted)

    
    doc = doc_models.Document(
        filename=file.filename,
        content_type=file.content_type,
        file_path=filepath,
        owner_id=current_user.id 
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@documents_router.get("/{id}")
async def get_doc_metadata(
    id: int,
    db: Session = Depends(get_db),
    current_user: doc_models.User = Depends(get_current_user)
):
    doc = db.query(doc_models.Document).filter(doc_models.Document.id == id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return doc

    


@documents_router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current_user: doc_models.User = Depends(get_current_user)):
    doc = db.query(doc_models.Document).get(doc_id)
    with open(doc.file_path, "rb") as f :
            encrypted=f.read()

    decrypted=fernet.decrypt(encrypted)
    temp_path=f"/tmp/{uuid4().hex}_{doc.filename}"
    with open(temp_path, "wb") as f:
        f.write(decrypted)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=temp_path,
        filename=doc.filename,
        media_type=doc.content_type
    )


@documents_router.post("/documents/{doc_id}/share/")
def generate_share_link(
    doc_id: int,
    expire_minutes: int = 60,
    one_time: bool = False,
    db: Session = Depends(get_db),
    current_user: doc_models.User = Depends(get_current_user)
):
    doc = db.query(doc_models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    token = uuid4().hex
    expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)

    share = doc_models.ShareToken(
        document_id=doc_id,
        token=token,
        expires_at=expires_at,
        one_time=one_time,
        used=False
    )
    db.add(share)
    db.commit()

    share_url = f"/public/{token}/download/"

    return {
        "share_url": share_url,
        "expires_at": expires_at,
        "one_time": one_time
    }



@documents_router.get("/public/{token}/download/")
def public_download(token: str, db: Session = Depends(get_db)):
    try:
        share = db.query(doc_models.ShareToken).filter(doc_models.ShareToken.token == token).first()
        if not share:
            raise HTTPException(status_code=404, detail="Invalid or expired token")

        if datetime.utcnow() > share.expires_at:
            raise HTTPException(status_code=403, detail="Link expired")

        if share.one_time and share.used:
            raise HTTPException(status_code=403, detail="One-time link already used")

        doc = db.query(doc_models.Document).get(share.document_id)
        if not doc or not os.path.exists(doc.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(doc.file_path, "rb") as f :
            encrypted=f.read()

        decrypted=fernet.decrypt(encrypted)
        temp_path=f"/tmp/{uuid4().hex}_{doc.filename}"
        with open(temp_path, "wb") as f:
            f.write(decrypted)


        if share.one_time:
            share.used = True
            db.commit()

        # background_tasks.add_task(remove_file, temp_path)

        return FileResponse(
            path=temp_path,
            filename=doc.filename,
            media_type=doc.content_type
        )

    except HTTPException as http_exc:
        raise http_exc

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(exc)}")
