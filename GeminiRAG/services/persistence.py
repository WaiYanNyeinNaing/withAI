import os
import json


def load_persisted_documents(store):
    """
    Load all .json docs from ./documents/ into the in-memory store.
    """
    root = "documents"
    if not os.path.exists(root):
        return

    for fname in os.listdir(root):
        if fname.endswith(".json"):
            path = os.path.join(root, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                store.add_document(
                    doc_id=data["id"],
                    name=data["name"],
                    content=data["content"],
                    description=data.get("description", ""),
                    persist=False,
                )
                # Build BM25 index for the loaded document
                store._build_bm25_index(data["id"])
            except Exception as exc:
                print(f"[persistence] Failed loading {fname}: {exc}")
