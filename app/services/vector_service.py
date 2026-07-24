from pathlib import Path

import lancedb
import pyarrow as pa

from app.core.config import settings
from app.core.logger import logger


class VectorService:
    """
    Responsible only for interacting with LanceDB.
    """

    _instance = None
    _db = None
    _table = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.db_path = Path(settings.VECTOR_DB_PATH)
        self.table_name = settings.VECTOR_TABLE_NAME

    def connect(self):

        if self._db is None:
            self.db_path.mkdir(parents=True, exist_ok=True)

            VectorService._db = lancedb.connect(
                str(self.db_path)
            )

            logger.info("Connected to LanceDB")
        return self._db

    def get_table(self):

        if self._table is None:
            db = self.connect()

            if self.table_name in db.table_names():

                VectorService._table = db.open_table(
                    self.table_name
                )

            else:

                schema = pa.schema([
                    pa.field("id", pa.int64()),
                    pa.field("document_id", pa.int64()),
                    pa.field("chunk_id", pa.int64()),
                    pa.field("page_number", pa.int32()),
                    pa.field("text", pa.string()),
                    pa.field("embedding", pa.list_(pa.float32(), 384)),
                ])

                VectorService._table = db.create_table(
                    self.table_name,
                    schema=schema
                )

                logger.info("Vector Table Created")

        return self._table

    def insert_chunks(
        self,
        chunks,
        embeddings,
    ):
        """
        Store chunks and embeddings.
        """

        records = []

        for chunk, embedding in zip(chunks, embeddings):

            records.append({

                "id": chunk["id"],
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "page_number": chunk["page_number"],
                "text": chunk["text"],
                "embedding": embedding,

            })

        self.get_table().add(records)

        logger.info(
            f"Inserted {len(records)} vectors."
        )

    def search(
        self,
        embedding,
        limit=5,
    ):
        """
        Search using an embedding vector.
        """

        logger.info("Searching LanceDB...")

        results = (

            self.get_table()

            .search(
                embedding,
                vector_column_name="embedding"
            )

            .metric("cosine")

            .limit(limit)

            .to_list()

        )

        logger.info(
            f"Retrieved {len(results)} chunks."
        )

        return results

    def delete_document(
        self,
        document_id,
    ):

        table = self.get_table()

        table.delete(
            f"document_id={document_id}"
        )

        logger.info(
            f"Deleted document {document_id}"
        )


vector_service = VectorService()