"""Post-hoc (2026-10-09, after the chain result): how much of each run's abstain is offrig's quote check rejecting a
quote that is really in the evidence? Rescores the chain's verdicts under looser quote matching, descriptively.
The pre-registered result stands as scored; this sizes a possible offrig change, never a rescore.

  mode 0  as scored (offrig 0f8b1c4: normalised substring, at least 12 characters)
  mode 1  + a short quote equal to a whole trimmed line; comment and diff markers (///, //, #, *, +/-) stripped from
          each evidence line before matching; a literal \n in the quote read as a line break
  mode 2  + a quote with ... matched as its >=12-character segments, in order

  python quote_match_posthoc.py results/2026-10-09-chain
"""
import glob, json, math, os, re, sys
G=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
gold={}
for f in [f"{G}/grounded.jsonl", f"{G}/prs/grounded-prs.jsonl", f"{G}/diffs/reasoning-diffs.jsonl"]:
    for l in open(f, encoding='utf-8'):
        r=json.loads(l); gold[r['id']]=r
Z=1.959963984540054
def wub(k,n):
    if n==0: return 1.0
    if k==n: return 1.0
    p=k/n; z2=Z*Z; c=(p+z2/(2*n))/(1+z2/n); m=Z*math.sqrt(p*(1-p)/n+z2/(4*n*n))/(1+z2/n); return min(1,c+m)
def norm(s):
    s=s.translate({0x2018:"'",0x2019:"'",0x201a:"'",0x201b:"'",0x201c:'"',0x201d:'"',0x201e:'"',0x201f:'"'}); return " ".join(s.split())
MARK=re.compile(r'^\s*(///?|//!|#+|\*|/\*\*?|--|[+-](?!\+|-))\s?')
def strip_lines(t): return "\n".join(MARK.sub('',ln) for ln in t.splitlines())
def found(q,ev,mode):
    q=norm(q)
    if mode>=1: q=norm(q.replace('\n',' '))
    if len(q)<12: 
        return mode>=1 and any(q==norm(ln) for e in ev for ln in e.splitlines() if ln.strip())
    E=[norm(e) for e in ev]
    if mode>=1: E+= [norm(strip_lines(e)) for e in ev]
    if any(q in e for e in E): return True
    if mode>=2 and ('...' in q or '…' in q):
        segs=[s.strip() for s in re.split(r'\.\.\.|…',q) if s.strip()]
        if segs and all(len(s)>=12 for s in segs):
            for e in E:
                pos=0; ok=True
                for s in segs:
                    i=e.find(s,pos)
                    if i<0: ok=False;break
                    pos=i+len(s)
                if ok: return True
    return False
modes={0:'as scored',1:'+whole-line short, comment/diff markers, escaped \n',2:'+ ellipsis segments in order'}
print("run | mode | abstain | FA primary (ub) | rule abstain/FA")
for d in sorted(glob.glob(f"{sys.argv[1]}/cal-*-tune")):
    v=[json.loads(l) for l in open(f"{d}/verdicts.jsonl", encoding='utf-8')]
    name=os.path.basename(d)[4:-5]
    for mode in (0,1,2):
        ab=den=fa=fan=0
        for x in v:
            if x['status']!='ok': continue
            g=gold[x['claim_id']]; ev=[c['text'] for c in g['context']]
            mv=x['model_verdict']
            if mode==0: fv=x['final_verdict']
            else:
                fv=x['final_verdict']
                if fv=='cannot_tell' and mv!='cannot_tell' and x.get('reason')=='quote_not_found' and found(x.get('evidence_quote') or '',ev,mode): fv=mv
            gl=x['gold_label']
            if gl in('supported','unsupported'): den+=1; ab+=fv=='cannot_tell'
            if gl in('unsupported','cannot_tell'): fan+=1; fa+=fv=='supported'
        print(f"{name} | {mode} | {ab}/{den} {ab/den:.3f} | {fa}/{fan} ub {wub(fa,fan):.3f} | {'ok' if ab/den<=0.2 else 'X'}/{'ok' if wub(fa,fan)<0.1 else 'X'}")
