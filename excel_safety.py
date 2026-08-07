FORMULA_PREFIXES = ("=", "+", "-", "@")


def sanitize_excel_value(value):
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value
