from .completion_models import ProofDimension

DEFAULT_QUORUM = tuple(d.value for d in ProofDimension)

class CompletionPolicy:
    def __init__(self, required_dimensions=DEFAULT_QUORUM, minimum_quorum_ratio=1.0):
        self.required_dimensions = tuple(required_dimensions)
        self.minimum_quorum_ratio = float(minimum_quorum_ratio)
        if not 0 < self.minimum_quorum_ratio <= 1:
            raise ValueError("minimum_quorum_ratio must be > 0 and <= 1")

    def quorum(self, passed: set[str]) -> bool:
        required = set(self.required_dimensions)
        if not required:
            return False
        return len(required & passed) / len(required) >= self.minimum_quorum_ratio
