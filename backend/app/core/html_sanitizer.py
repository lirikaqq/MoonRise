"""
Модуль для безопасной очистки HTML-контента.
Используется bleach для удаления опасных тегов и атрибутов (XSS-защита).
"""
import bleach


# Разрешённые теги — только те, что доступны в нашем Tiptap-редакторе
ALLOWED_TAGS = [
    "p", "br",
    "strong", "em", "u", "s",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "a",
    "span",
]

# Разрешённые атрибуты по тегам
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "span": ["style"],
}

# Разрешённые протоколы для ссылок
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(html_content: str | None) -> str | None:
    """
    Очищает HTML от опасных тегов/атрибутов.
    Возвращает None если на входе None или пустая строка.
    """
    if not html_content:
        return None

    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,  # Удаляем неразрешённые теги (а не экранируем)
        strip_comments=True,
    )

    return cleaned if cleaned.strip() else None
