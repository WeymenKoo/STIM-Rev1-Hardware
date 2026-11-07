#!/usr/bin/env python3
"""Run a bench script with its prompts answered from a file instead of the keyboard (agent-in-the-loop sessions).

  python relay.py <answer_file> bench_tbs.py preflight --visa ivi

Every input() prints its prompt plus a line '<<WAITING>>', then waits until <answer_file> exists, takes its text as
the answer (empty = Enter) and deletes the file. Typing at the keyboard is not needed and not read.
"""
import builtins, os, runpy, sys, time

ans_file = os.path.abspath(sys.argv[1])
script = sys.argv[2]
sys.argv = [script] + sys.argv[3:]
try: sys.stdout.reconfigure(errors="replace", line_buffering=True)
except Exception: pass

def relay_input(prompt=""):
    print(prompt, flush=True); print("<<WAITING>>", flush=True)
    while not os.path.exists(ans_file): time.sleep(0.2)
    time.sleep(0.1)
    with open(ans_file, encoding="utf-8") as f: a = f.read().strip()
    os.remove(ans_file)
    print(f"  <<GOT: {a!r}>>", flush=True); return a

builtins.input = relay_input
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
runpy.run_path(script, run_name="__main__")
