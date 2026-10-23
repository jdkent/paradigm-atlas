"""Derive a JSON Schema from a NuExtract template (for vLLM structured_outputs constrained decoding)."""

def to_schema(t):
    if isinstance(t, dict):
        return {"type": "object", "properties": {k: to_schema(v) for k, v in t.items()},
                "required": list(t), "additionalProperties": False}
    if isinstance(t, list):
        if t and isinstance(t[0], list):
            return {"anyOf": [{"type": "array", "items": {"enum": t[0]}}, {"type": "null"}]}
        if len(t) == 1 and isinstance(t[0], dict):
            return {"type": "array", "items": to_schema(t[0])}
        if len(t) == 1 and t[0] in ("verbatim-string", "string"):
            return {"anyOf": [{"type": "array", "items": {"type": "string"}}, {"type": "null"}]}
        if len(t) == 1 and t[0] in ("integer", "number"):
            return {"type": "array", "items": {"type": t[0]}}
        return {"anyOf": [{"enum": t}, {"type": "null"}]}
    if t in ("verbatim-string", "string"):
        return {"anyOf": [{"type": "string"}, {"type": "null"}]}
    if t == "integer":
        return {"anyOf": [{"type": "integer"}, {"type": "null"}]}
    if t == "number":
        return {"anyOf": [{"type": "number"}, {"type": "null"}]}
    return {}
