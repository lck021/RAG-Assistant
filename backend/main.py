from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Annotated

from rag import *

app = FastAPI()

@app.post("/uploadfile")
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
        text = raw.decode(encoding="utf-8-sig", errors="strict")
    except UnicodeDecodeError:
        raise HTTPException(
                    status_code=422,
                    detail="Incorrect file encoding"
                )

    chunks = text_into_chunks(text)

    