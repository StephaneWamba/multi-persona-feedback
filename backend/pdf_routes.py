from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_current_user
import os
from typing import Optional
import PyPDF2
import io

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a PDF file
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed")

    # Check file size (limit to 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="File size too large. Maximum 10MB allowed")

    try:
        # Read PDF content
        content = await file.read()

        # Extract text from PDF
        pdf_text = extract_text_from_pdf(content)

        if not pdf_text.strip():
            raise HTTPException(
                status_code=400, detail="Could not extract text from PDF")

        # For now, we'll return the extracted text
        # In a full implementation, this would be stored in the database
        return {
            "filename": file.filename,
            "size": len(content),
            "extracted_text": pdf_text[:1000] + "..." if len(pdf_text) > 1000 else pdf_text,
            "text_length": len(pdf_text),
            "message": "PDF processed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing PDF: {str(e)}")


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF content using PyPDF2
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


@router.get("/status")
async def pdf_status():
    """
    Check PDF processing service status
    """
    return {
        "status": "operational",
        "message": "PDF processing service is ready",
        "supported_formats": ["PDF"],
        "max_file_size": "10MB"
    }
