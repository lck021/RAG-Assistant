# RAG Assistant Project

## Docker Commands

To copy docker image of postgresql server with pgvector extension installed: 
```powershell
docker run --name rag-postgres -e POSTGRES_USER=raguser -e POSTGRES_PASSWORD='choose-a-strong-local-password' -e POSTGRES_DB=ragdb -p 5432:5432 -v rag_postgres_data:/var/lib/postgresql/data -d pgvector/pgvector:pg17
```

A superuser account is initiated and a docker volume is mounted to the container so that the postgresql data is persistent. 

## Setting up Virtual Environment (.venv)

```terminal
py -3.11 -m venv .venv

.venv\Scripts\Activate.ps1
```

## Running pytests
```terminal
python -m pytest tests/test_*.py
```