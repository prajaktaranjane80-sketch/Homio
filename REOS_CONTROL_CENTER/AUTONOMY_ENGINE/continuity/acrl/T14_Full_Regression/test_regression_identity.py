from .regression_identity import canonicalize, fingerprint

def test_canonicalization_is_stable():
    assert canonicalize({'b':1,'a':2}) == '{"a":2,"b":1}'

def test_fingerprint_is_stable():
    assert fingerprint({'a':1}) == fingerprint({'a':1})
    assert fingerprint({'a':1}) != fingerprint({'a':2})

def test_fingerprint_length():
    assert len(fingerprint({'a':1})) == 64
