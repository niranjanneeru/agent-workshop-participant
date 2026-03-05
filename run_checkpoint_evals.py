#!/usr/bin/env python3
"""Run evaluation for each checkpoint tag.

Usage: python run_checkpoint_evals.py [--start N] [--end N]
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request


EVAL_URL = "http://localhost:3000"
PLATFORM_URL = "http://localhost:8081"
WEAVIATE_URL = "http://localhost:8090"

AGENT_CONFIG = {
    "endpoint_url": "http://agent-platform:8081/api/chat/sync",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body_template": {"message": "$message", "history": "$messages", "user_id": 1},
    "response_path": "response",
}

PRESET_IDS = [
    "step-0-simple-agent",
    "step-1-db-tools",
    "step-2-rag-tools",
    "step-3-web-search",
    "step-4-intent-routing",
    "step-5-memory-streaming",
    "step-6-mcp",
    "step-7-guardrails",
]


def run(cmd, **kw):
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def wait_healthy(url, label, timeout=120):
    print(f"  Waiting for {label} ({url}) ...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen(url, timeout=5)
            if r.status == 200:
                print(" ✓")
                return True
        except Exception:
            pass
        time.sleep(3)
        print(".", end="", flush=True)
    print(" TIMEOUT")
    return False


def check_weaviate_ingested():
    """Warn if Weaviate Documents collection is empty (RAG won't work)."""
    try:
        r = urllib.request.urlopen(
            f"{WEAVIATE_URL}/v1/objects?class=Documents&limit=1", timeout=5
        )
        data = json.loads(r.read())
        if not data.get("objects"):
            print(
                "\n  ⚠️  WARNING: Weaviate 'Documents' collection is empty — RAG tools will not work."
            )
            print(
                "  Run: docker compose run --rm --workdir /app platform python -m scripts.ingest\n"
            )
    except Exception:
        pass


def fetch_presets():
    r = urllib.request.urlopen(f"{EVAL_URL}/api/eval/presets")
    return json.loads(r.read())


def run_eval(preset: dict):
    """POST to eval/run, read SSE stream, return result dict."""
    goal_config = {
        "goal": preset["goal"],
        "success_criteria": preset["success_criteria"],
        "initial_context": preset.get("initial_context", ""),
        "evaluator_persona": preset.get("evaluator_persona", ""),
        "max_turns": preset.get("max_turns", 6),
    }
    body = json.dumps({
        "name": preset.get("name", preset["id"]),
        "agent_config": AGENT_CONFIG,
        "goal_config": goal_config,
        "evaluator_model": "gpt-4.1-mini",
        "judge_model": "gpt-4.1-mini",
    }).encode()

    req = urllib.request.Request(
        f"{EVAL_URL}/api/eval/run",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    resp = urllib.request.urlopen(req, timeout=300)

    result = None
    buffer = ""
    for raw_line in resp:
        line = raw_line.decode("utf-8", errors="replace")
        buffer += line
        if "\n" in buffer:
            parts = buffer.split("\n")
            buffer = parts[-1]
            for part in parts[:-1]:
                part = part.strip()
                if part.startswith("data:"):
                    data_str = part[5:].strip()
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    if data.get("type") == "turn":
                        speaker = data.get("speaker", "?")
                        msg = (data.get("message") or "")[:120]
                        print(f"    [{speaker}] {msg}")
                    elif data.get("type") == "result":
                        result = data.get("result", {})
                    elif data.get("type") == "error":
                        print(f"    ERROR: {data.get('error')}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=7)
    args = parser.parse_args()

    # Check Weaviate is populated
    check_weaviate_ingested()

    # Fetch presets
    print("\n=== Fetching eval presets ===")
    presets_list = fetch_presets()
    presets_by_id = {p["id"]: p for p in presets_list}
    print(f"  Found {len(presets_list)} presets: {[p['id'] for p in presets_list]}")

    results = {}

    for ckpt in range(args.start, args.end + 1):
        tag = f"checkpoint-{ckpt}"
        preset_id = PRESET_IDS[ckpt]

        print(f"\n{'='*60}")
        print(f"=== Checkpoint {ckpt}: {preset_id} ===")
        print(f"{'='*60}")

        # Checkout the tag
        print(f"\n  Checking out {tag} ...")
        r = run(f"git checkout {tag}")
        if r.returncode != 0:
            print(f"  FAILED to checkout {tag}: {r.stderr}")
            results[ckpt] = "CHECKOUT_FAILED"
            continue

        # Rebuild and restart platform
        print(f"\n  Rebuilding platform ...")
        r = run("docker compose up -d --build platform")
        if r.returncode != 0:
            print(f"  FAILED to rebuild platform: {r.stderr}")
            results[ckpt] = "BUILD_FAILED"
            continue

        # Wait for platform to be healthy
        if not wait_healthy(f"{PLATFORM_URL}/api/health", "platform"):
            results[ckpt] = "PLATFORM_UNHEALTHY"
            continue

        # Run eval
        preset = presets_by_id.get(preset_id)
        if not preset:
            print(f"  Preset {preset_id} not found!")
            results[ckpt] = "PRESET_NOT_FOUND"
            continue

        print(f"\n  Running evaluation: {preset.get('name', preset_id)} ...")
        try:
            result = run_eval(preset)
            if result:
                passed = result.get("passed", result.get("goal_reached", False))
                scores = result.get("scores", {})
                score = result.get("score", round(sum(scores.values()) / len(scores), 2) if scores else "?")
                summary = result.get("summary", result.get("assessment", ""))[:200]
                status = "PASS ✅" if passed else "FAIL ❌"
                print(f"\n  Result: {status} (score: {score})")
                print(f"  Summary: {summary}")
                results[ckpt] = status
            else:
                print(f"\n  No result received")
                results[ckpt] = "NO_RESULT"
        except Exception as e:
            print(f"\n  Eval error: {e}")
            results[ckpt] = f"ERROR: {e}"

    # Summary
    print(f"\n{'='*60}")
    print("=== SUMMARY ===")
    print(f"{'='*60}")
    for ckpt in range(args.start, args.end + 1):
        print(f"  checkpoint-{ckpt}: {results.get(ckpt, 'SKIPPED')}")

    # Return to the last checkpoint
    run(f"git checkout checkpoint-{args.end}")


if __name__ == "__main__":
    main()
