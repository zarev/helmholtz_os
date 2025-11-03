"""Utilities for persisting downloaded papers into a pgvector-enabled database."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import psycopg
from pgvector.psycopg import register_vector
from pypdf import PdfReader


@dataclass
class PgVectorConfig:
    """Configuration required to connect to Postgres."""

    host: str
    port: int
    user: str
    password: str
    dbname: str
    table: str = "open_access_papers"

    @classmethod
    def from_env(cls) -> Optional["PgVectorConfig"]:
        """Create a configuration object from the current environment.

        Returns ``None`` when the expected environment variables are missing so
        callers can gracefully skip database ingestion.
        """

        host = os.getenv("PGVECTOR_HOST")
        dbname = os.getenv("PGVECTOR_DB")
        user = os.getenv("PGVECTOR_USER")
        password = os.getenv("PGVECTOR_PASSWORD")
        port = os.getenv("PGVECTOR_PORT", "5432")
        table = os.getenv("PGVECTOR_TABLE", "open_access_papers")

        if not all([host, dbname, user, password]):
            return None

        try:
            port_num = int(port)
        except ValueError:
            raise ValueError("PGVECTOR_PORT must be an integer") from None

        return cls(
            host=host,
            port=port_num,
            user=user,
            password=password,
            dbname=dbname,
            table=table,
        )


def _ensure_table(conn: psycopg.Connection, table: str) -> None:
    """Create the destination table when it does not already exist."""

    create_sql = f"
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            pdf_url TEXT UNIQUE NOT NULL,
            local_path TEXT NOT NULL,
            content TEXT,
            embedding vector(3) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    ""
    with conn.cursor() as cur:
        cur.execute(create_sql)
        conn.commit()


def _generate_embedding(text: str) -> Iterable[float]:
    """Generate a deterministic embedding for ``text``.

    The implementation intentionally avoids heavyweight ML dependencies so the
    ingestion step works in lightweight environments. It hashes the text with
    SHA-256 and normalises the digest into three floating point numbers, which
    are suitable for storing in a ``vector(3)`` column via pgvector.
    """

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    chunks = [digest[i : i + 21] for i in range(0, 63, 21)]
    return [int(chunk, 16) / float(16 ** len(chunk)) for chunk in chunks]


def _read_pdf_text(pdf_path: Path) -> str:
    """Extract a basic text representation from ``pdf_path``."""

    reader = PdfReader(str(pdf_path))
    texts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
        except Exception:  # pragma: no cover - defensive against parser quirks
            page_text = ""
        texts.append(page_text)
    return "\n".join(texts)


def store_paper(paper_path: str | Path, title: str, pdf_url: str) -> None:
    """Persist metadata and embeddings for the downloaded paper.

    When the pgvector configuration is absent the function simply logs the
    situation and returns without raising an exception. This keeps the scraper
    usable in environments where Postgres is not yet configured.
    """

    config = PgVectorConfig.from_env()
    if config is None:
        print("ℹ️  Skipping pgvector ingestion (environment variables not set).")
        return

    path_obj = Path(paper_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Paper path does not exist: {path_obj}")

    content = _read_pdf_text(path_obj)
    embedding = _generate_embedding(content)

    conn = psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
    )
    try:
        register_vector(conn)
        _ensure_table(conn, config.table)

        insert_sql = (
            f"INSERT INTO {config.table} (title, pdf_url, local_path, content, embedding) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (pdf_url) DO UPDATE SET "
            "title = EXCLUDED.title, local_path = EXCLUDED.local_path, "
            "content = EXCLUDED.content, embedding = EXCLUDED.embedding"
        )
        with conn.cursor() as cur:
            cur.execute(
                insert_sql,
                (
                    title,
                    pdf_url,
                    str(path_obj.resolve()),
                    content,
                    list(embedding),
                ),
            )
        conn.commit()
        print(f"💾 Stored '{title}' in pgvector table '{config.table}'.")
    finally:
        conn.close()


__all__ = ["store_paper", "PgVectorConfig"]
