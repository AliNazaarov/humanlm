import json, re, collections, os
ev=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dev=[json.loads(l) for l in open(f'{ev}/dev_set.jsonl')]
tr=[json.loads(l) for l in open(f'{ev}/trick_set.jsonl')]
base={json.loads(l)['id']:json.loads(l)['output'] for l in open(f'{ev}/baseline_frontier.jsonl')}
wc=lambda s: len(s.split())
print(collections.Counter(d['type'] for d in dev))
print(collections.Counter(d['trick_kind'] for d in tr))
emoji=re.compile('[\U0001F300-\U0001FAFF☀-➿]')
slop=re.compile(r"\b(unlock|seamless(ly)?|elevate|empower|game-changer|revolutioni[sz]e|effortless(ly)?|delve|tapestry)\b",re.I)
num=re.compile(r"\d[\d,.]*")
probs=[]
for d in dev+tr:
    o=base[d['id']]; src=json.dumps(d['brief'],ensure_ascii=False)+d['ai_draft']
    if d in dev and not (60<=wc(d['ai_draft'])<=250): probs.append((d['id'],'draft words',wc(d['ai_draft'])))
    if '—' in o or '–' in o: probs.append((d['id'],'dash in baseline'))
    if emoji.search(o): probs.append((d['id'],'emoji in baseline'))
    m=slop.search(o)
    if m: probs.append((d['id'],'slop',m.group()))
    for n in num.findall(o):
        n=n.rstrip('.,')
        if n and n not in src: probs.append((d['id'],'new number',n))
    for v in d.get('verbatim',[]):
        if v not in o: probs.append((d['id'],'verbatim missing',v[:30]))
    if d['type']=='cold_email':
        body=o.split('\n',1)[1]
        if wc(body)>90: probs.append((d['id'],'cold >90',wc(body)))
    if d['type']=='landing_hero' and o.startswith('Headline'):
        h=re.search(r'Headline: (.*)',o).group(1); sub=re.search(r'Subhead: (.*)',o)
        if wc(h)>12: probs.append((d['id'],'headline',wc(h)))
        if sub and wc(sub.group(1))>30: probs.append((d['id'],'subhead',wc(sub.group(1))))
    if d['type']=='landing_section' and wc(o)>80: probs.append((d['id'],'section>80',wc(o)))
    if d['type']=='launch_email' and wc(o)>200: probs.append((d['id'],'email>200',wc(o)))
for p in probs: print(p)
r=[wc(base[d['id']])/wc(d['ai_draft']) for d in dev]
print('dev baseline/draft length ratio median', sorted(r)[len(r)//2], 'min',min(r),'max',max(r))
print('draft words median', sorted(wc(d['ai_draft']) for d in dev)[50])
