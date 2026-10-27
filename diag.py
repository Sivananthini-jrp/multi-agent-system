"""
Diagnostic script: isolates where LLM calls are failing or hanging.
Run: venv\\Scripts\\python -u diag.py
Each step prints BEFORE and AFTER so you can see which one hangs.
"""
import os
import sys
import json
import time
import socket
import urllib.request
import urllib.error

SEP = "=" * 60


def step(n, name):
    print(f"\n{SEP}\nSTEP {n}: {name}\n{SEP}")


def safe(name, fn, timeout_note=""):
    """Run fn, print result or error. Never let it block silently."""
    print(f"  running...{timeout_note}")
    t0 = time.time()
    try:
        result = fn()
        elapsed = time.time() - t0
        print(f"  ✅ OK in {elapsed:.1f}s")
        print(f"  result: {result}")
        return True, result
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  ❌ FAILED in {elapsed:.1f}s")
        print(f"  {type(e).__name__}: {e}")
        return False, e


# ---------- Step 0: environment ----------
step(0, "Environment")
print(f"  python: {sys.executable}")
print(f"  version: {sys.version.split()[0]}")
print(f"  cwd: {os.getcwd()}")

try:
    from dotenv import load_dotenv, find_dotenv
    found = find_dotenv()
    print(f"  .env found at: {found or '(none)'}")
    load_dotenv(override=True)
except Exception as e:
    print(f"  dotenv error: {e}")

provider = (os.getenv("LLM_PROVIDER") or "").strip()
key = os.getenv("GOOGLE_API_KEY") or ""
print(f"  LLM_PROVIDER: {provider!r}")
print(f"  GOOGLE_API_KEY length: {len(key)}")
print(f"  GOOGLE_API_KEY prefix: {key[:6]!r}")


# ---------- Step 1: raw network to Google ----------
step(1, "Raw TCP to generativelanguage.googleapis.com:443 (5s timeout)")
def tcp_test():
    s = socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=5)
    s.close()
    return "connected"
safe("tcp", tcp_test, " (if this hangs → network/DNS/VPN is the problem)")


# ---------- Step 2: raw HTTPS to Google root ----------
step(2, "HTTPS GET to Google API root (10s timeout)")
def https_test():
    resp = urllib.request.urlopen("https://generativelanguage.googleapis.com", timeout=10)
    return f"HTTP {resp.status}"
safe("https", https_test, " (if this hangs → proxy/firewall blocking HTTPS)")


# ---------- Step 3: list models with key ----------
step(3, "List models using your API key (15s timeout)")
def list_models():
    if not key:
        raise ValueError("GOOGLE_API_KEY is empty — .env not loaded")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read())
    names = [m["name"] for m in data.get("models", [])
             if "generateContent" in m.get("supportedGenerationMethods", [])]
    return f"{len(names)} models support generateContent:\n    " + "\n    ".join(names)
ok_models, models_result = safe("list_models", list_models,
                                " (if this hangs/403 → key is invalid or restricted)")


# ---------- Step 4: raw REST generateContent call ----------
step(4, "Raw REST call to gemini-2.5-flash (20s timeout)")
def raw_call():
    if not key:
        raise ValueError("GOOGLE_API_KEY is empty")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={key}"
    )
    body = json.dumps({"contents": [{"parts": [{"text": "say ok"}]}]}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=20)
    data = json.loads(resp.read())
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return f"model replied: {text[:80]!r}"
safe("raw_call", raw_call,
     " (if 404 → wrong model name; if 429 → rate-limited; if hangs → blocked)")


# ---------- Step 5: LangChain model construction ----------
step(5, "LangChain get_model() construction")
def construct():
    from config import get_model
    m = get_model()
    return f"{type(m).__name__} with model={getattr(m, 'model', '?')}"
ok_lc, _ = safe("construct", construct)


# ---------- Step 6: LangChain invoke (this is where it usually hangs) ----------
step(6, "LangChain invoke 'say ok' (30s timeout)")
def lc_invoke():
    from config import get_model
    m = get_model()
    r = m.invoke("say ok")
    return f"replied: {r.content[:80]!r}"
safe("lc_invoke", lc_invoke,
     " (if this hangs but step 4 worked → LangChain/SDK issue)")


# ---------- Step 7: bind_tools (needed by researcher/analyst) ----------
step(7, "LangChain bind_tools + invoke (30s timeout)")
def lc_tools():
    from config import get_model
    from tools import calculate
    m = get_model().bind_tools([calculate])
    r = m.invoke("what is 2+2? use the tool")
    return f"tool_calls={getattr(r, 'tool_calls', None)} content={r.content[:60]!r}"
safe("lc_tools", lc_tools,
     " (if this hangs → tool calling unsupported on your model/tier)")


# ---------- Step 8: with_structured_output (needed by supervisor) ----------
step(8, "LangChain with_structured_output (30s timeout)")
def lc_structured():
    from config import get_model
    from pydantic import BaseModel
    from typing import Literal

    class R(BaseModel):
        next_agent: Literal["researcher", "analyst", "writer", "finish"]

    m = get_model(temperature=0).with_structured_output(R)
    out = m.invoke("research_findings missing, analysis missing, draft missing. Next?")
    return f"structured output: {out}"
safe("lc_structured", lc_structured,
     " (if this hangs → model doesn't support structured output)")


print(f"\n{SEP}\nDIAGNOSTIC COMPLETE\n{SEP}")
print("""
Interpretation guide:

- Step 1 hangs  → network/DNS. Try mobile hotspot or disable VPN.
- Step 2 hangs  → HTTPS blocked. Check corporate proxy / antivirus.
- Step 3 fails  → API key invalid or no Gemini access on the project.
- Step 4 fails  → Wrong model name, or rate-limited (429), or key revoked.
- Step 5 fails  → config.py broken; recheck the file.
- Step 6 hangs  → langchain-google-genai SDK issue. Try:
                    venv\\Scripts\\pip install --upgrade langchain-google-genai
- Step 7 hangs  → tool calling unsupported. Fall back to no-tools researcher.
- Step 8 hangs  → structured output unsupported. Use plain-text supervisor.
- All pass      → The LLM works fine. The graph has a logic bug, not LLM.

Use the first failing step to decide the fix.
""")