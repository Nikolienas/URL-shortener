def extract_url_from_cell(url_cell):
    """
    Извлекает URL из ячейки Excel, обрабатывая гиперссылки и обычные значения
    """
    # Приоритет 1: Гиперссылка в ячейке (если это внешняя ссылка)
    if url_cell.hyperlink:
        url = url_cell.hyperlink.target
        # Игнорирование внутренние ссылки Excel (начинающиеся с '#')
        if url and not url.startswith('#'):
            return url
    
    # Приоритет 2: Значение ячейки (если это строка с URL)
    cell_value = url_cell.value
    if cell_value and isinstance(cell_value, str) and cell_value.startswith('http'):
        return cell_value
    
    # Приоритет 3: Любое другое значение (преобразуется в строку)
    return str(cell_value) if cell_value else None