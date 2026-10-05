-- creates pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- creates documents table with id as a primary key
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  filename TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- creates chunks table, referencing document_id as a foreign key
  CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024) NOT NULL
  );

-- creates an embedding index using the HNSW algorithm based on cosine similarity
CREATE INDEX chunks_embedding_idx
ON chunks USING hnsw (embedding vector_cosine_ops);