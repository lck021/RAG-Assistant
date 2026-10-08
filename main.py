from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Annotated

from backend.database import *
from backend.rag import *

app = FastAPI()

@app.post("/upload", status_code=201)
async def processFile(file: Annotated[UploadFile, File()]):

    # checks if file type is valid
    if Path(file.filename).suffix.lower() != ".txt":
        raise HTTPException(
            status_code=422,
            detail="Incorrect file type"
        )

    raw = await file.read()

    # checks encoding
    try: 
        contents = raw.decode(encoding="utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        raise HTTPException(
                    status_code=422,
                    detail="Incorrect file encoding"
                )

    chunks = text_into_chunks(contents)
    chunk_count = len(chunks)
    embeddings = embed_chunks(chunks)

    # adds document and individual chunks into database
    document_id = insert_document(filename=file.filename, 
                               contents=contents)

    insert_chunks(
        document_id=document_id,
        chunks=chunks,
        embeddings=embeddings
    )

    return {
        "id": document_id,
        "filename": file.filename,
        "chunk_count": chunk_count,
        "message": "Document uploaded successfully"
    }