import os
from typing import Sequence
import uuid
from pgvector.sqlalchemy import VECTOR
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import DateTime, ForeignKey, create_engine, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

load_dotenv()

db_url = os.getenv("DATABASE_URL")

engine = create_engine(db_url)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    filename: Mapped[str]
    contents: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(tz=timezone.utc))


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(VECTOR(1024))

Base.metadata.create_all(engine)


def insert_document(filename: str, contents: str):
    document = Document(
        id=uuid.uuid4(),
        filename=filename, 
        contents=contents
    )

    with Session(engine) as session:
        session.add(document)
        session.commit()
        session.refresh(document)
        return document.id


def insert_chunks(document_id: uuid.UUID, chunks: list[str], embeddings: list):
    with Session(engine) as session:
        for index, content in enumerate(chunks):
            chunk = Chunk(
                    id=uuid.uuid4(),
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    embedding=embeddings[index]
                )
            session.add(chunk)
        session.commit()


def find_similar(q_embedding: str, k=3) -> list[Chunk]:
    statement = (
        select(Chunk)
        .order_by(Chunk.embedding.cosine_distance(q_embedding))
        .limit(k)
    )
    with Session(engine) as session:
        similar_chunks = session.scalars(statement).all()

        return similar_chunks