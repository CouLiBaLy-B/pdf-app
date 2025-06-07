"""
Fonctions utilitaires diverses
"""


def parse_page_ranges(page_input):
    """Parse une chaîne comme '1,3,5-7' en liste de numéros de pages"""
    pages = []
    parts = page_input.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))

    return sorted(set(pages))


def validate_page_numbers(pages, max_pages):
    """Valide une liste de numéros de pages"""
    invalid_pages = [p for p in pages if p < 1 or p > max_pages]
    return len(invalid_pages) == 0, invalid_pages


def format_file_size(size_bytes):
    """Formate une taille de fichier en unités lisibles"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"
