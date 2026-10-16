#!/usr/bin/env python3
"""Regression tests for the two Prolog checkers: does each one bite?

Run from anywhere:   python3 evidence/certificate/tests/run_tests.py
                     python3 evidence/certificate/tests/run_tests.py --original
The second form runs the same tamperings against the ORIGINAL checkers (kept in
original-2026-08-04/ and Claude-artifacts/original-2026-08-01/) and only reports
what they do, without judging it.

Every test copies evidence/ to a temporary directory, tampers with the copy, runs
the checkers there, and compares the outcome with the expected one.  The real
files are never modified.  Needs SWI-Prolog (swipl) and the Python standard library.

Added 2026-10-16.  Tests F1 and F2 are the two false accepts found by an
independent review (OpenAI Codex): the 2026-08-04 checkers ACCEPTED both.  T1-T6
are the six tamperings reported on the page since 2026-08-04; N1 is the one
tampering that should be accepted (a different, still valid proof).
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2]


def leaf_sub(text, fn, count=None):
    """Apply fn(leaf_id, path, ys, zs) -> (path, ys, zs) to leaf facts."""
    pat = re.compile(r"leaf\((\d+),\s*(\[[^\]]*\]),\s*(\[[^\]]*\]),\s*(\[[^\]]*\])\)")
    done = 0

    def rep(m):
        nonlocal done
        if count is not None and done >= count:
            return m[0]
        done += 1
        p, y, z = fn(int(m[1]), m[2], m[3], m[4])
        return f"leaf({m[1]}, {p}, {y}, {z})"

    out = pat.sub(rep, text)
    assert done > 0
    return out


def chronological_visits(route):
    return re.sub(r"visit\(\s*(\d+),\s*\d+\)", lambda m: f"visit({m[1]}, {m[1]})", route)


def forge_extra_potential(c, r):
    """F1 (Codex): a 36th potential for a nonexistent node, no cuts, claim the
    chronological length, and make the route chronological."""
    c = leaf_sub(c, lambda i, p, y, z: (p, "[" + ",".join(["0"] * 35 + ["1000000000"]) + "]", "[]"))
    c = c.replace("claim(3527).", "claim(15209).")
    return c, chronological_visits(r)


def forge_visits_only(c, r):
    """F2 (Codex): reorder visit/2, leave the stored legs and total unchanged."""
    return c, chronological_visits(r)


def forge_fake_nodes(c, r):
    """F3: declare 37 nodes and add a cut made only of nodes that do not exist,
    with a huge multiplier -- no real edge crosses it, so it inflates the bound."""
    c = c.replace("node_count(35).", "node_count(37).")
    c = c.replace("counts(edges(563), cuts(34), leaves(226)).",
                  "counts(edges(563), cuts(35), leaves(226)).\ncut(35, [36, 37]).")
    c = leaf_sub(c, lambda i, p, y, z: (p, y, z[:-1] + (", " if z != "[]" else "") + "35-1000000000]"))
    return c, r


def forge_duplicate_leaf(c, r):
    """F4: a second leaf 1 that closes trivially, next to the real one."""
    m = re.search(r"leaf\(1,\s*(\[[^\]]*\]),", c)
    extra = f"leaf(1, {m[1]}, [" + ",".join(["0"] * 34 + ["99999999999"]) + "], [])."
    return c + "\n" + extra + "\n", r


def forge_redefine_dist(c, r):
    """F5: the certificate tries to define a predicate (all distances zero)."""
    return c + "\ndist(_, _, 0).\n", r


def t_delete_leaf(c, r):
    return re.sub(r"\nleaf\(226,[^\n]*", "", c, count=1), r


def t_zero_potentials(c, r):
    return leaf_sub(c, lambda i, p, y, z: (p, "[" + ",".join(["0"] * 35) + "]", z), count=1), r


def t_negative_multiplier(c, r):
    def neg(i, p, y, z):
        if z == "[]":
            return p, y, z
        return p, y, re.sub(r"-(\d+)", r"- -\1", z, count=1)
    return leaf_sub(c, neg), r


def t_claim_3528(c, r):
    return c.replace("claim(3527).", "claim(3528)."), r


def t_falsify_edge(c, r):
    return c.replace("edge(1, 1, 2, 645).", "edge(1, 1, 2, 545)."), r


def t_enlarge_cut(c, r):
    return c.replace("cut(1, [15, 24, 26]).", "cut(1, [" + ", ".join(map(str, range(1, 36))) + "]).", 1), r


def t_nudge_potential(c, r):
    """N1: lower one potential of leaf 1 slightly -- a different, still valid proof."""
    def nudge(i, p, y, z):
        ys = y[1:-1].split(",")
        ys[0] = str(int(ys[0]) - 5)
        return p, "[" + ",".join(ys) + "]", z
    return leaf_sub(c, nudge, count=1), r


TESTS = [
    # name, tamper, expected (check_certificate passes?, verify.pl passes?)
    ("original files", lambda c, r: (c, r), (True, True)),
    ("F1 extra potential for a nonexistent node (Codex)", forge_extra_potential, (False, False)),
    ("F2 visits reordered, stored legs unchanged (Codex)", forge_visits_only, (False, False)),
    ("F3 cut made of nonexistent nodes", forge_fake_nodes, (False, True)),
    ("F4 duplicate leaf id", forge_duplicate_leaf, (False, True)),
    ("F5 certificate redefines dist/3", forge_redefine_dist, (False, True)),
    ("T1 delete one leaf", t_delete_leaf, (False, True)),
    ("T2 zero out one leaf's potentials", t_zero_potentials, (False, True)),
    ("T3 negative cut multiplier", t_negative_multiplier, (False, True)),
    ("T4 claim 3,528 km", t_claim_3528, (False, True)),
    ("T5 falsify one edge cost (645 -> 545)", t_falsify_edge, (False, True)),
    ("T6 enlarge a cut to all nodes", t_enlarge_cut, (False, True)),
    ("N1 nudge one potential (still a valid proof)", t_nudge_potential, (True, True)),
]


def run_checker(cwd, prog):
    p = subprocess.run(["swipl", "-q", "-g", "run", "-t", "halt", prog],
                       cwd=cwd, capture_output=True, text=True, timeout=120)
    lines = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()]
    fails = [l for l in lines if l.startswith("FAIL")]
    return p.returncode == 0, (fails[0] if fails else lines[-1] if lines else "")


def main():
    original = "--original" in sys.argv[1:]
    cert0 = (EVIDENCE / "certificate/certificate.pl").read_text(encoding="utf-8")
    route0 = (EVIDENCE / "Claude-artifacts/route_optimized.pl").read_text(encoding="utf-8")
    failures = 0
    for name, tamper, (want_cert, want_verify) in TESTS:
        with tempfile.TemporaryDirectory() as tmp:
            ev = Path(tmp) / "evidence"
            shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns(
                "original-*", "__pycache__", "tests", "GPT-artifacts", "DL-experiment"))
            c, r = tamper(cert0, route0)
            (ev / "certificate/certificate.pl").write_text(c, encoding="utf-8")
            (ev / "Claude-artifacts/route_optimized.pl").write_text(r, encoding="utf-8")
            if original:
                shutil.copy(EVIDENCE / "certificate/original-2026-08-04/check_certificate.pl",
                            ev / "certificate/check_certificate.pl")
                shutil.copy(EVIDENCE / "Claude-artifacts/original-2026-08-01/verify.pl",
                            ev / "Claude-artifacts/verify.pl")
            got_cert, msg_c = run_checker(ev / "certificate", "check_certificate.pl")
            got_ver, msg_v = run_checker(ev / "Claude-artifacts", "verify.pl")
        ok = (got_cert, got_ver) == (want_cert, want_verify)
        failures += not ok
        fmt = lambda b: "PASS" if b else "FAIL"
        if original:
            print(f"    {name}")
            print(f"      check_certificate.pl (2026-08-04): {fmt(got_cert)}  {msg_c}")
            print(f"      verify.pl (2026-08-01):            {fmt(got_ver)}  {msg_v}")
            continue
        print(f"{'ok ' if ok else 'BAD'} {name}")
        print(f"      check_certificate.pl: {fmt(got_cert)} (expected {fmt(want_cert)})  {msg_c}")
        print(f"      verify.pl:            {fmt(got_ver)} (expected {fmt(want_verify)})  {msg_v}")
    if original:
        print("\n(original checkers: outcomes reported, not judged)")
        return
    print(f"\n{len(TESTS) - failures} of {len(TESTS)} tests behave as expected.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
