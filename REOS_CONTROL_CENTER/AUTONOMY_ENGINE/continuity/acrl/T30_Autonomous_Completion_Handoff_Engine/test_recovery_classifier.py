from .recovery_classifier import classify_recovery
def test_recovery():
    assert classify_recovery(checkpoint_valid=True,execution_interrupted=True,evidence_consistent=True,human_rejected=False)=='RESUME'
