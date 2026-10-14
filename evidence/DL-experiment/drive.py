import subprocess, sys, time, re
S = sys.argv[0].rsplit('/',1)[0]
enc = sys.argv[1]; budget = float(sys.argv[2])
bound_rule = '&diff{totalcost-0} <= b.\n'
open(f'{S}/bound.lp','w').write('#const b=100000.\n' + bound_rule)
t0 = time.time()
lo, hi = 0, 15245   # known trivial upper bound (chronological tour)
best = None
while lo < hi and time.time()-t0 < budget:
    mid = (lo+hi)//2
    left = budget - (time.time()-t0)
    r = subprocess.run(['python3','-m','clingodl',f'{S}/instance.lp',f'{S}/{enc}',
                        f'{S}/bound.lp','-c',f'b={mid}','--time-limit',str(max(1,int(left)))],
                       capture_output=True, text=True)
    out = r.stdout
    if 'UNSATISFIABLE' in out: lo = mid+1; res='UNSAT'
    elif 'SATISFIABLE' in out:
        hi = mid; best = out; res='SAT'
    else: print(f'  b<={mid}: TIMEOUT after {time.time()-t0:.0f}s'); break
    print(f'  b<={mid}: {res}  ({time.time()-t0:.1f}s)')
print(f'elapsed {time.time()-t0:.1f}s  interval [{lo},{hi}]' + (' PROVEN OPTIMAL' if lo==hi else ' (not closed)'))
if best:
    cyc = dict(tuple(map(int,m)) for m in re.findall(r'cycle\((\d+),(\d+)\)', best))
    n, order = 35, []
    for _ in range(35): n = cyc[n]; order.append(n)
    print('best tour found (from dummy 35):', ' '.join(map(str,order)))
