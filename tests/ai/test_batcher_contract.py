from src.ai.batcher import chunk_records


def test_chunk_records_respects_batch_size() -> None:
    records = list(range(250))
    chunks = list(chunk_records(records, batch_size=100))
    assert [len(chunk) for chunk in chunks] == [100, 100, 50]
