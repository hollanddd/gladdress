def ordinal(n):
    return str(n) + ('th' if 10 <= n % 100 < 20 else {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th'))
