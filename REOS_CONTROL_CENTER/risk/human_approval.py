HIGH_RISK = {'architecture_freeze','financial','legal','security','privacy','production'}
def requires_human(action):
    return action in HIGH_RISK
