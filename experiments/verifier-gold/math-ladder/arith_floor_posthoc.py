"""Post-hoc (2026-10-09, the Publisher's question): on the ladder's false accepts, does the verdict's `reasoning` hold the
true value? Sizes an "arithmetic floor": on a supported verdict, compare the claim's number with the last number in
the reasoning, and a mismatch becomes cannot_tell. Caveat: `reasoning` is the structured summary written with the
verdict, not the thinking trace, which offrig does not record.

  python arith_floor_posthoc.py qwen3_8b qwen3_14b ...   (run dirs under E:/AI/rnd-ladder/ladder-<name>)
"""
import json, os, re, sys
from collections import Counter
g={}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ladder.jsonl'), encoding='utf-8'):
    r=json.loads(l); g[r['id']]=r
NUM=re.compile(r'(?<![\w.])-?\d[\d,]*(?:\.\d+)?')
def nums(s): 
    out=[]
    for t in NUM.findall(s or ''):
        try: out.append(float(t.replace(',','')))
        except: pass
    return out
def fmt(x): return int(x) if float(x).is_integer() else x
for m in sys.argv[1:]:
    v=[json.loads(l) for l in open(f'E:/AI/rnd-ladder/ladder-{m}/verdicts.jsonl', encoding='utf-8')]
    fa=Counter(); l6=Counter(); floor=Counter()
    for x in v:
        if x['status']!='ok': continue
        r=g[x['claim_id']]; true=float(r['ladder']['true']); claimed=nums(r['claim'])[-1]
        rs=nums(x.get('reasoning'))
        last=rs[-1] if rs else None
        # floor: on a 'supported' model verdict, compare the claim's number with the reasoning's final number
        if x['model_verdict']=='supported':
            # final computed number: last number in reasoning that isn't just the claim restated at the end? use last number
            mism = last is not None and last!=claimed
            if r['label']=='unsupported':
                k = 'true value in reasoning' if true in rs else 'true value absent'
                k2 = 'floor catches' if mism else 'floor misses'
                fa[(k,k2)]+=1
                if r['ladder']['cell']=='L6': l6[(k,k2)]+=1
            else:
                floor['supported gold, floor would flip (false reject)' if mism else 'supported gold, floor agrees']+=1
    print(f"== {m}\n  false accepts (model said supported, gold unsupported): {sum(fa.values())}")
    for k,c in fa.most_common(): print('   ',c,k)
    print('  of which L6:',dict(l6))
    print('  cost on gold-supported:',dict(floor))
