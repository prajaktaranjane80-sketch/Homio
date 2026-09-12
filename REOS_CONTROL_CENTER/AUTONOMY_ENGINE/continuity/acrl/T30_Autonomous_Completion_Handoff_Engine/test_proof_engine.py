from .proof_engine import evaluate_proof
def test_proof():
    r=evaluate_proof({'CODE':True,'TEST':False},('CODE','TEST','CONTRACT')); assert r.passed==('CODE',) and 'CONTRACT' in r.missing
