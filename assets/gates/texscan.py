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
        # 인라인 MathJax(tex-svg)에는 한글 글리프가 없어 \text{월} 같은 수식이 통째로
        # "Math input error"가 된다. 렌더 게이트가 mjx 오류 수로 잡아 주지만 어느 수식인지는
        # 말해 주지 않으므로 여기서 이름으로 잡는다. 한글은 수식 밖 본문에 쓴다.
        if re.search(r'[가-힣]', t):
            issues.append('수식 안의 한글 — 인라인 MathJax가 렌더하지 못한다')
        # 셸 헤어독으로 조각을 쓰면 \frac \b \v 의 백슬래시가 먹히면서 제어문자만 남는다.
        # 실측: "EX=12\cdot\frac{5}{20}=3"이 \x0crac{5}{20}이 되어 수식 하나가 통째로
        # "Math input error"가 됐다. 눈으로는 보이지 않고 렌더해야 드러난다.
        for ch, name in ((chr(7), 'a'), (chr(8), 'b'), (chr(11), 'v'), (chr(12), 'f')):
            if ch in t:
                issues.append(f'제어문자 — 백슬래시가 먹혀 \\{name} 가 뭉개졌다')
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
