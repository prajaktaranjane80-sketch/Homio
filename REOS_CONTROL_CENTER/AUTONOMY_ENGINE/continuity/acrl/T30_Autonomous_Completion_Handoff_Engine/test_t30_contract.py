import json
from pathlib import Path

def test_contract():
    data=json.loads((Path(__file__).with_name('t30.contract.json')).read_text())
    assert data['layer']=='T30'
    assert 'HANDOFF_READY' in data['terminal_states']
    assert len(data['proof_dimensions'])==8
