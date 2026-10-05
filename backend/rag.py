from langchain_text_splitters import RecursiveCharacterTextSplitter

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