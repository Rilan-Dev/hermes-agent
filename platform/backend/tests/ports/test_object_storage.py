import pytest

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.ports.object_storage import ObjectMetadata, ObjectReference


DIGEST = "a" * 64


def test_object_reference_is_opaque_and_metadata_is_validated() -> None:
    reference = ObjectReference.parse("obj_01JY123")
    metadata = ObjectMetadata(
        filename="invoice.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        sha256=DIGEST,
    )

    assert str(reference) == "obj_01JY123"
    assert metadata.sha256 == DIGEST

    with pytest.raises(DomainValidationError, match="content type"):
        ObjectMetadata("invoice.pdf", " ", 1, DIGEST)
    with pytest.raises(DomainValidationError, match="size"):
        ObjectMetadata("invoice.pdf", "application/pdf", -1, DIGEST)
    with pytest.raises(DomainValidationError, match="SHA-256"):
        ObjectMetadata("invoice.pdf", "application/pdf", 1, "not-a-digest")
