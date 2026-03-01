"""Batch helpers for AI classification."""

from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


def chunk_records(records: Iterable[T], batch_size: int) -> Iterator[list[T]]:
    """Yield records in fixed-size chunks."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    bucket: list[T] = []
    for record in records:
        bucket.append(record)
        if len(bucket) >= batch_size:
            yield bucket
            bucket = []

    if bucket:
        yield bucket
