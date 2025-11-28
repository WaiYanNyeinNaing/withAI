from __future__ import annotations

"""
Local document helpers.

These utilities allow you to treat a local folder full of documents as
a simple "corpus" that your agents can read from. This is useful for:

- Prototyping / offline testing
- Simple demos without an external document service
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LocalDoc:
    """
    A simple representation of a local text document.
    """

    doc_id: str
    path: str
    title: str
    content: str


def _read_file(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding, errors="ignore") as f:
        return f.read()


def load_local_documents(
    root_dir: str,
    exts: Optional[List[str]] = None,
    max_files: Optional[int] = None,
) -> List[LocalDoc]:
    """
    Load local text documents from a directory.

    Parameters
    ----------
    root_dir:
        Root directory to scan.
    exts:
        Optional list of file extensions to include (e.g. [".txt", ".md"]).
        If None, all files are included.
    max_files:
        Optional limit on the number of files to read.

    Returns
    -------
    List[LocalDoc]
        LocalDoc objects with ID, path, title, and content.
    """
    docs: List[LocalDoc] = []
    counter = 0

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if exts and not any(filename.lower().endswith(ext) for ext in exts):
                continue

            full_path = os.path.join(dirpath, filename)
            try:
                text = _read_file(full_path)
            except Exception as exc:  # pragma: no cover
                print(f"[local_docs] Error reading {full_path}: {exc}")
                continue

            doc_id = f"local-{counter}"
            title = filename
            docs.append(
                LocalDoc(
                    doc_id=doc_id,
                    path=full_path,
                    title=title,
                    content=text,
                )
            )
            counter += 1

            if max_files is not None and counter >= max_files:
                return docs

    return docs


def make_doc_index(docs: List[LocalDoc]) -> Dict[str, LocalDoc]:
    """
    Build a dictionary index of docs by doc_id for quick lookup.
    """
    return {doc.doc_id: doc for doc in docs}
