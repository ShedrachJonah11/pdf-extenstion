from pathlib import Path

from app.services.storage_paths import (
    INDEX_FILE,
    METADATA_FILE,
    doc_dir,
    index_path,
    metadata_path,
)


def test_doc_dir_combines_root_and_id() -> None:
    assert doc_dir(Path("/tmp/store"), "abc") == Path("/tmp/store/abc")


def test_metadata_path_uses_metadata_filename() -> None:
    p = metadata_path(Path("/tmp/store"), "abc")
    assert p.name == METADATA_FILE
    assert p.parent.name == "abc"


def test_index_path_uses_faiss_filename() -> None:
    p = index_path(Path("/tmp/store"), "abc")
    assert p.name == INDEX_FILE
    assert p.parent.name == "abc"


def test_filenames_are_constants() -> None:
    assert METADATA_FILE.endswith(".json")
    assert INDEX_FILE.endswith(".faiss")
