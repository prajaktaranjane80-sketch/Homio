from .change_impact_analysis import ImpactLevel, ImpactReason, T17Decision
IMPACT_LEVELS = tuple(x.value for x in ImpactLevel)
IMPACT_REASONS = tuple(x.value for x in ImpactReason)
DECISIONS = tuple(x.value for x in T17Decision)
