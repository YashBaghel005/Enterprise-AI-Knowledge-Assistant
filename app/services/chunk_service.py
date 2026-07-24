from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkService:
    """
    Splits extracted pages into overlapping chunks.
    """

    def __init__(
        self,
        chunk_size: int = 700,
        chunk_overlap: int = 150,
    ):

        self.splitter = RecursiveCharacterTextSplitter(

            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,

            separators=[
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
                " ",
                "",
            ],
        )

    def create_chunks(
        self,
        pages,
        document_id,
    ):

        chunks = []

        chunk_id = 1

        for page in pages:

            splits = self.splitter.split_text(
                page["text"]
            )

            for split in splits:

                chunks.append({

                    "id": document_id * 100000 + chunk_id,

                    "document_id": document_id,

                    "chunk_id": chunk_id,

                    "page_number": page["page_number"],

                    "text": split,

                })

                chunk_id += 1

        return chunks