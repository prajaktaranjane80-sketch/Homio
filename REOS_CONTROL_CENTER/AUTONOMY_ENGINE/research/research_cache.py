from __future__ import annotations
import json
from pathlib import Path
from typing import Any
class ResearchCache:
    def __init__(self,path:Path): self.path=path; self.path.parent.mkdir(parents=True,exist_ok=True)
    def _load(self):
        if not self.path.exists(): return {}
        try:
            x=json.loads(self.path.read_text(encoding="utf-8")); return x if isinstance(x,dict) else {}
        except json.JSONDecodeError: return {}
    def put(self,key:str,value:dict[str,Any]):
        d=self._load(); d[key]=value; self.path.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    def get(self,key:str): return self._load().get(key)
