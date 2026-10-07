"""Tiny Gemini helper: send a prompt (+ optional screenshots), get parsed JSON back.
Set GEMINI_API_KEY in your environment. Tries several models in turn if one is slow/overloaded.
Force one model with GEMINI_MODEL. Quick self-test:  python llm.py"""
import os, json, re, time
from google import genai
from google.genai import types

MODELS = ([os.environ["GEMINI_MODEL"]] if os.environ.get("GEMINI_MODEL") else
          ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.7-flash"])
TIMEOUT_S = 40
_client = None

def _make_client():
    try:  # newer SDKs: switch off the library's own silent retries
        opts = types.HttpOptions(timeout=TIMEOUT_S * 1000,
                                 retry_options=types.HttpRetryOptions(attempts=1))
    except Exception:
        opts = types.HttpOptions(timeout=TIMEOUT_S * 1000)
    return genai.Client(http_options=opts)  # reads GEMINI_API_KEY from the environment

def ask_json(prompt, images=(), retries=8):
    global _client
    if _client is None:
        _client = _make_client()
    parts = [types.Part.from_bytes(data=open(p, "rb").read(), mime_type="image/png")
             for p in images] + [prompt]
    cfg = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2)
    for n in range(retries):
        model = MODELS[n % len(MODELS)]
        start = time.time()
        print(f"  -> {model} (attempt {n+1}/{retries}, timeout {TIMEOUT_S}s)...", flush=True)
        try:
            r = _client.models.generate_content(model=model, contents=parts, config=cfg)
            print(f"  <- answered in {time.time()-start:.1f}s", flush=True)
            return json.loads(re.sub(r"^```(?:json)?|```$", "", r.text.strip()).strip())
        except json.JSONDecodeError:
            print("  (invalid JSON, trying again)", flush=True)
        except Exception as e:
            msg = str(e)
            print(f"  !! after {time.time()-start:.1f}s: {msg[:200]}", flush=True)
            low = msg.lower()
            if "api key" in low or "permission" in low or "401" in low or "403" in low:
                raise  # a key problem won't be fixed by switching models
            time.sleep(3)  # otherwise just move on to the next model
    raise RuntimeError("Every model failed. Check your connection / try again in a few minutes.")

if __name__ == "__main__":
    print(ask_json('Reply only with JSON: {"ok": true}'))