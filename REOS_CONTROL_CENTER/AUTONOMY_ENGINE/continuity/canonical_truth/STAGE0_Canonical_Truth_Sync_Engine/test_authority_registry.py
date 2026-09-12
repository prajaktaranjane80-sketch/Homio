from .authority_registry import AuthorityRegistry


def test_registry_is_chat_independent():
    reg = AuthorityRegistry()
    reg.validate()
    assert reg.chat_authority == "NONE"
    assert reg.execution_state_authority.endswith("data/state.json")
