"""Post-hoc (2026-10-09, asked by ASPIRE for its stage-3b judge choice): each chain model's error lean on the gold.
False rejects (gold supported -> unsupported) vs false accepts (gold unsupported -> supported), on the final verdict
and on the model's own verdict before the quote check. Descriptive; it decides nothing here.

  python error_lean_posthoc.py
"""
import glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
def rate(files,field):
    out={}
    for f in sorted(glob.glob(files)):
        name=os.path.basename(os.path.dirname(f))
        sup=[0,0,0]; uns=[0,0,0]   # n, said unsupported, said supported
        for l in open(f,encoding='utf-8'):
            x=json.loads(l)
            if x['status']!='ok': continue
            g=x.get('gold_label'); v=x.get(field)
            if g=='supported': sup[0]+=1; sup[1]+=v=='unsupported'
            if g=='unsupported': uns[0]+=1; uns[2]+=v=='supported'
        out[name]=(sup,uns)
    return out
print("chain (final verdict): false-reject on gold supported | false-accept on gold unsupported")
for k,(s,u) in rate(os.path.join(HERE,'results','2026-10-09-chain','cal-*','verdicts.jsonl'),'final_verdict').items():
    print(f"  {k:38} FR {s[1]}/{s[0]} {s[1]/s[0]:.2f}   FA {u[2]}/{u[0]} {u[2]/u[0]:.2f}")
print("chain (model verdict, before the quote check):")
for k,(s,u) in rate(os.path.join(HERE,'results','2026-10-09-chain','cal-*','verdicts.jsonl'),'model_verdict').items():
    print(f"  {k:38} FR {s[1]}/{s[0]} {s[1]/s[0]:.2f}   FA {u[2]}/{u[0]} {u[2]/u[0]:.2f}")
