from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Annotated
from pydantic import BaseModel, Field
import uuid

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


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


@app.post("/ask", status_code=200)
def generateAnswer(request: AskRequest):
    request.question = request.question.strip()

    q_embedding = embed_question(request.question)
    similar_chunks = find_similar(q_embedding)
    response = generate_answer(request.question, context=similar_chunks)

    return {
        "response": response,
        "context": [
            {
                "id": chunk.id,
                "content": chunk.content,
                "document_id": chunk.document_id
            }
            for chunk in similar_chunks
        ]
    }


# TODO: add a delete endpoint and delete the test doc after the tests have ran
@app.delete("/delete/{document_id}")
def deleteDocument(document_id: uuid.UUID):
    if not is_doc_present(document_id):
        raise HTTPException(
            status_code=404,
            detail=f"Item with ID {document_id} not found"
        )

    if not delete_document(document_id):
        raise HTTPException(
                    status_code=400,
                    detail=f"Delete unsuccessful"
                )

    return {
        "deleted_id": document_id
    }