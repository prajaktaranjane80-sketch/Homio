def compact(text, limit=800):
    text = ' '.join(str(text).split())
    return text if len(text) <= limit else text[:limit-3] + '...'
