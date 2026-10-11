from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from functools import lru_cache
from google import genai

client = genai.Client()

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
    context = "\n\n".join(chunk.content for chunk in context)
    instructions = "Answer using only the context below. If the answer is not in the context, reply exactly: NOT_FOUND"
    prompt = f"""
    Context:
    {context}

    Question:
    {question}
    """

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        system_instruction=instructions,
        input=prompt,
        generation_config={
            "temperature": 0,
            "max_output_tokens": 300,
            "thinking_level": "low"
        },
        store=False
    )

    return interaction.output_text