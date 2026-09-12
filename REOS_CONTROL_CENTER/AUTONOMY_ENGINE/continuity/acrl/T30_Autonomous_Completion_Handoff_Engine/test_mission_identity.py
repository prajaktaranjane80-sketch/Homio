from .mission_identity import mission_fingerprint
def test_fingerprint_deterministic():
    a={'b':2,'a':1}; assert mission_fingerprint(a)==mission_fingerprint({'a':1,'b':2})
