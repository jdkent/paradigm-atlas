"""Minimal OpenAI-compatible chat client for the portkey gateway (credentials from /home/james/pondie/.env)."""
import json, os, re, time
import requests

def load_env(path="/home/james/pondie/.env"):
    for line in open(path):
        m = re.match(r"\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=\s*(.*)\s*$", line)
        if m:
            os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))

DEFAULT_MODEL = "@psyc-aid338-ope-333f18/gpt-6-luna"   # latest Luna on the portkey gateway (2026-10-09)


def chat(messages, model=DEFAULT_MODEL, max_tokens=16000, temperature=None, json_mode=True, timeout=300, schema=None,
         schema_name="extraction", reasoning_effort=None, service_tier=None):
    """schema: a JSON Schema dict -> OpenAI strict structured output (response_format json_schema, strict=True),
    so enum/list/null formatting is enforced by the API rather than by prompt instructions."""
    base = os.environ["OPENAI_API_GATEWAY"].rstrip("/"); key = os.environ["OPENAI_API_KEY"]
    body = {"model": model, "messages": messages}
    body["max_tokens" if "claude" in model else "max_completion_tokens"] = max_tokens
    if temperature is not None:
        body["temperature"] = temperature
    # OpenAI Flex processing: ~half price, slower, may answer 429 "resource unavailable" -> long timeout + retries
    if service_tier and "/gpt" in model:
        body["service_tier"] = service_tier
        timeout = max(timeout, 900)
    if reasoning_effort and "/gpt" in model:
        body["reasoning_effort"] = reasoning_effort
    if schema is not None:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": schema_name, "schema": schema, "strict": True}}
    elif json_mode and "/gpt" in model:
        body["response_format"] = {"type": "json_object"}
    last = None
    tries = 8 if service_tier == "flex" else 5
    for attempt in range(tries):
        try:
            r = requests.post(f"{base}/chat/completions", json=body, timeout=timeout,
                              headers={"Authorization": f"Bearer {key}"})
            if r.status_code == 200:
                j = r.json()
                return j["choices"][0]["message"]["content"], j.get("usage", {})
            last = f"{r.status_code} {r.text[:300]}"
            if r.status_code in (400, 401, 403, 404):
                break
            if r.status_code == 429 and service_tier == "flex":
                time.sleep(min(600, 30 * 2 ** attempt)); continue
        except Exception as e:  # noqa
            last = repr(e)
        time.sleep(3 * 2 ** attempt)
    raise RuntimeError(last)

def parse_json(s):
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)
        return json.loads(m.group(0)) if m else None
