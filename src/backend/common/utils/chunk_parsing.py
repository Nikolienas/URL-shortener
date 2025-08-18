def get_chunks(queryset, chunk_size=1000):
    '''Генератор, для итерирования данных чанков'''
    chunk = []
    for item in queryset.iterator():
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk