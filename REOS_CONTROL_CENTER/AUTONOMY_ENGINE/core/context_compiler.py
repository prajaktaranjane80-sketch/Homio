from __future__ import annotations
from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class ContextItem:
    kind: str; key: str; value: Any; priority: int
class ContextCompiler:
    def compile(self, items:list[ContextItem], max_items:int=80): return sorted(items,key=lambda x:(-x.priority,x.kind,x.key))[:max_items]
    @staticmethod
    def redact(value:Any)->Any:
        if isinstance(value,dict):
            s={"password","token","secret","api_key","private_key","cookie"}
            return {k:("[REDACTED]" if k.lower() in s else ContextCompiler.redact(v)) for k,v in value.items()}
        if isinstance(value,list): return [ContextCompiler.redact(v) for v in value]
        return value
