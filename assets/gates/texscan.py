# -*- coding: utf-8 -*-
# usage: python texscan.py <file1.html> [file2.html ...]
# merror로 안 잡히는 조용한 TeX 파손 후보를 찾는다. \to\ 2 같은 의도적 간격은 오탐이니 눈으로 거를 것.
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')
BS = chr(92)
for fn in sys.argv[1:]:
    body = re.sub(r'<script[\s\S]*?</script>', '', io.open(fn, encoding='utf-8').read())
    body = body.replace(BS+'$', '')   # 수식 안 달러 이스케이프(\$)는 짝 계산에서 제외
    segs = [('$$', m.start(), m.group(1)) for m in re.finditer(r'\$\$([\s\S]*?)\$\$', body)]
    tmp2 = re.sub(r'\$\$[\s\S]*?\$\$', lambda m: ' '*len(m.group(0)), body)
    segs += [('$', m.start(), m.group(1)) for m in re.finditer(r'\$([^$]+)\$', tmp2)]
    print('==', fn)
    hits = 0
    for kind, pos, t in sorted(segs, key=lambda x: x[1]):
        issues = []
        if '\t' in t: issues.append('TAB')
        if kind == '$' and '\n' in t: issues.append('인라인 수식 내 줄바꿈')
        if re.search(r'(?<!' + re.escape(BS) + r')' + re.escape(BS) + r' [0-9\-]', t): issues.append('역슬래시+공백+숫자(행구분 파손 의심)')
        if re.search(re.escape(BS) + r'[bcfv](?![a-zA-Z])', t): issues.append('수상한 제어열 \\b\\c\\f\\v')
        if kind == '$$' and re.search(r'pmatrix|bmatrix|cases|aligned', t) and (BS+BS) not in t and '&' in t:
            issues.append('행렬/케이스인데 행구분자 \\\\ 없음')
        if issues:
            hits += 1
            print(' 줄', body[:pos].count('\n')+1, '['+kind+']', ' | '.join(issues))
            print('   ', repr(t[:140]))
    if hits == 0:
        print('  (이상 없음)')
