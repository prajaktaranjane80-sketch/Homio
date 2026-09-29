from pathlib import Path
class WorkspaceGuard:
    def __init__(self, allowed_roots:list[Path]): self.allowed_roots=[p.resolve() for p in allowed_roots]
    def check(self,target:Path)->bool:
        r=target.resolve(); return any(r==root or root in r.parents for root in self.allowed_roots)
    def require(self,target:Path)->None:
        if not self.check(target): raise PermissionError(f"Workspace boundary violation: {target}")
