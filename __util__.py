def ordinal(n):
    return str(n) + ('th' if 10 <= n % 100 < 20 else {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th'))

def cap_words(word):
  parts = []
  for part in word.split():
    parts.append(part.capitalize())
  return ' '.join(parts).strip()

def to_utf8(item):
    ''''''
    if item: return item.encode('utf-8', 'replace'); return None
