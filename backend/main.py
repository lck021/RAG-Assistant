from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Annotated

from backend.database import *
from rag import *

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
    document = insert_document(filename=file.filename, 
                               contents=contents)

    for index, chunk in enumerate(chunks):
        insert_chunk(document_id=document.id, 
                     chunk_index=index, 
                     content=chunk, 
                     embedding=embeddings[index])

    return {
        "id": document.id,
        "filename": file.filename,
        "chunk_count": chunk_count,
        "message": "Document uploaded successfully"
    }