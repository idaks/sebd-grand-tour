#!/usr/bin/env python3
"""independent_check.py -- a second, independent check of the lower bound.

Written by OpenAI Codex during an independent review on 2026-10-16 (see the page's
"A second opinion" section); copied here verbatim except for this docstring, the
path line below, and the final print lines.  Different author, different language
(Python, standard library only, integer arithmetic) than check_certificate.pl.

It checks, from the unchanged certificate.pl and distance.pl: 563 edges equal to the
561 published distances plus two zero-cost dummy edges; 34 proper cuts; leaf ids
exactly 1..226; exactly 35 integer potentials per leaf; nonnegative multipliers on
existing cuts; decisions on existing edges; a complete binary case analysis; and
every leaf's bound > 3526 km.  It does not check the tour (verify.pl does that).

Run:   python3 independent_check.py        (from this directory or anywhere)
"""
from pathlib import Path
import re, ast
p=Path(__file__).resolve().parent.parent
s=(p/"certificate/certificate.pl").read_text()
edges=[tuple(map(int,m)) for m in re.findall(r"edge\((\d+),\s*(\d+),\s*(\d+),\s*(-?\d+)\)",s)]
cuts={int(i):set(ast.literal_eval(v)) for i,v in re.findall(r"cut\((\d+),\s*(\[[^\]]*\])\)",s)}
leaves=[]
for i,path,ys,zs in re.findall(r"leaf\((\d+),\s*(\[[^\]]*\]),\s*(\[[^\]]*\]),\s*(\[[^\]]*\])\)",s):
 pairs=lambda x:[tuple(map(int,m)) for m in re.findall(r"(\d+)-(-?\d+)",x)]
 leaves.append((int(i),pairs(path),ast.literal_eval(ys),dict(pairs(zs))))
assert len(edges)==563 and len({e[0] for e in edges})==563
assert len(cuts)==34 and all(2<=len(v)<=33 and v<=set(range(1,36)) for v in cuts.values())
assert len(leaves)==226 and {x[0] for x in leaves}==set(range(1,227))
scale=int(re.search(r"scale\((\d+)\)",s)[1]);assert scale>0
bounds=[]
for i,path,ys,zs in leaves:
 assert len(ys)==35 and all(type(y)==int for y in ys)
 assert all(k in cuts and z>=0 for k,z in zs.items())
 assert len(dict(path))==len(path) and all(e in range(1,564) and v in (0,1) for e,v in path)
 decisions=dict(path);b=2*sum(ys)+2*sum(zs.values())
 for e,u,v,c in edges:
  d=scale*c-ys[u-1]-ys[v-1]-sum(z for k,z in zs.items() if (u in cuts[k])!=(v in cuts[k]))
  b+=0 if decisions.get(e)==0 else d if decisions.get(e)==1 else min(0,d)
 assert b>scale*3526
 bounds.append(b)
def complete(paths):
 if paths==[[]]:return True
 assert paths and all(paths)
 e=paths[0][0][0]
 assert all(p[0][0]==e for p in paths)
 return complete([p[1:] for p in paths if p[0][1]==0]) and complete([p[1:] for p in paths if p[0][1]==1])
assert complete([p for _,p,_,_ in leaves])
dist={(int(a),int(b)):int(c) for a,b,c in re.findall(r"distance\(\s*(\d+),\s*(\d+),\s*(\d+)\)",(p/"Claude-artifacts/distance.pl").read_text())}
assert {(u,v):c for _,u,v,c in edges if v!=35}==dist
assert [(u,v,c) for _,u,v,c in edges if v==35]==[(1,35,0),(34,35,0)]
print("Independent Python check: 563 edges, 34 proper cuts, 226 leaves, 35 potentials per leaf; complete tree; all exact integer bounds > 3526.")
print("Minimum scaled bound:",min(bounds),"scale:",scale,"maximum tree depth:",max(len(p) for _,p,_,_ in leaves))
