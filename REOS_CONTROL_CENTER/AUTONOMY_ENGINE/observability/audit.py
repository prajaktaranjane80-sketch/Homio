from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
class AutonomyAudit:
    def __init__(self,path:Path): self.path=path; self.path.parent.mkdir(parents=True,exist_ok=True)
    def record(self,event_type:str,payload:dict[str,Any]):
        row={"event_type":event_type,"recorded_at":datetime.now(timezone.utc).isoformat(),"payload":payload}
        with self.path.open("a",encoding="utf-8") as f: f.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")
