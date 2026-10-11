from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from huggingface_hub import InferenceClient

# cache the embedding model
@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("BAAI/bge-large-en-v1.5")


def text_into_chunks(text: str) -> list[str]:
    # checks if text is empty or only contains whitespace
    if not text.strip():
        return []

    # initialize the splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,       # maximum number of characters per chunk
        chunk_overlap=80,     # number of overlapping characters to preserve context
    )

    chunks = text_splitter.split_text(text)

    return chunks


def embed_chunks(chunks: list[str]): 
    # initialise the model
    model = get_embedding_model()

    embeddings = model.encode(chunks, truncate_dim=1024, normalize_embeddings=True)

    return embeddings


def embed_question(question: str):
    # initialise the model
    model = get_embedding_model()

    embedding = model.encode(question, truncate_dim=1024, normalize_embeddings=True)

    return embedding


def generate_answer(question: str, context: list):
    client = InferenceClient()

    context = "\n\n".join(chunk.content for chunk in context)
    prompt = f"""
    Answer the question below using only the provided context.

    Context:
    {context}

    Question:
    {question}
    """

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer concisely.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ]
    )

    return completion.choices[0].message