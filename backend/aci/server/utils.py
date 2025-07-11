def truncate_if_too_large(data: str, max_size: int) -> str:
    data_size = len(data.encode("utf-8"))
    if data_size > max_size:
        return (
            data.encode("utf-8")[: max_size - 100].decode("utf-8", errors="replace")
            + f"... [truncated, size={data_size}]"
        )
    return data
