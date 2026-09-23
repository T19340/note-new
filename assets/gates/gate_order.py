# -*- coding: utf-8 -*-
"""읽는 순서 게이트 — 아직 주지 않은 것으로 설명하고 있지 않은지 본다.

usage: python gate_order.py <조립된.html>

노트는 위에서 아래로 한 번 읽힌다. 그런데 뒤에 나올 문제나 상황을 앞에서 예로 들면, 읽는
사람은 그 자리에서 이해할 수 없고 한참 뒤에 가서야 "아까 그게 이거였구나" 하게 된다. 그
되돌아감이 곧 혼란이고, 만들 이유가 없는 비용이다.

무엇을 보나. 문제 블록(.pset)마다 그 문제에만 나오는 낱말을 뽑아, 그 낱말이 문제보다 **앞에**
쓰였는지 찾는다. 앞에 있으면 독자가 모르는 것으로 설명한 자리다.

빠뜨리는 곳. 목차·배치표·패널은 일부러 앞에 두는 지도이므로 검사에서 뺀다. 문제의 제목
자체(예: "추가 5번")를 앞에서 가리키는 것도 지도의 일부라 허용한다. 걸리는 것은 **문제의
내용**을 미리 풀어 쓴 자리다.
"""
import io, os, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

STOP = set('''것 수 때 곳 중 등 및 또 그 이 저 두 세 네 한 개 명 번 장 절 문제 경우 확률 평균
구하 구하십시오 하면 해서 되는 있는 없는 같은 다른 모든 어떤 이때 그때 이것 그것 무엇 얼마
사람 사이 대해 대한 위해 통해 가운데 각각 서로 다시 먼저 나중 지금 여기 거기'''.split())


def prose_blocks(html):
    """문서에 나오는 순서대로 (종류, 글) 목록. 지도 성격의 블록은 뺀다."""
    s = re.sub(r'(?is)<script\b.*?</script>|<style\b.*?</style>', ' ', html)
    s = re.sub(r'(?is)<nav class="toc".*?</nav>', ' ', s)              # 목차
    s = re.sub(r'(?is)<div class="panel-rail".*?$', ' ', s)            # 우측 패널
    s = re.sub(r'(?is)<table class="cover".*?</table>', ' ', s)        # 문제 배치표
    s = re.sub(r'data-tex="[^"]*"', ' ', s)
    def clean(x):
        x = re.sub(r'<[^>]+>', ' ', x)
        x = re.sub(r'&[a-z]+;|&#\d+;', ' ', x)
        return re.sub(r'\s+', ' ', x).strip()

    # 문제의 진술문: 영어 원문(.pen) 바로 뒤에 오는 한국어 문단. 해설은 빼고 진술만 본다.
    pset_spans = []
    for m in re.finditer(r'(?is)<p class="pen">.*?</p>\s*(<p[^>]*>.*?</p>)', s):
        pset_spans.append((m.start(), clean(m.group(0))))

    out = []
    for m in re.finditer(r'(?is)<(p|li|figcaption|h[1-4])\b[^>]*>(.*?)</\1>', s):
        t = clean(m.group(2))
        if t:
            kind = 'head' if m.group(1).lower().startswith('h') else 'text'
            out.append((kind, t, m.start()))
    for pos, t in pset_spans:
        out.append(('pset', t, pos))
    out.sort(key=lambda r: r[2])
    # 진술문 안에 들어 있는 text 블록은 중복이므로 뺀다
    spans = [(p, p + len(t) * 3) for p, t in pset_spans]
    return [b for b in out if b[0] == 'pset' or not any(a <= b[2] < z for a, z in spans)]


PART = re.compile(r'(으로부터|에게서|에서는|으로는|이라는|라는|에게|에서|부터|까지|으로|이고|'
                  r'입니다|합니다|이며|하며|들의|들이|들은|들을|은|는|이|가|을|를|의|에|도|만|'
                  r'과|와|로|나|랑)$')


def stem(w):
    """조사를 떼어 낸 꼴로 센다. '개수의'와 '개수'가 다른 말로 잡히면 오탐만 는다."""
    prev = None
    while prev != w:
        prev = w
        w = PART.sub('', w)
    return w


# 서술어는 그 문제의 '내용'이 아니다. 실측: "…와 다릅니다"가 소득 문제에만 있다는 이유로
# 앞에서 쓴 "값은 …와 다릅니다"가 앞선 언급으로 잡혔다. 잡아야 할 것은 미리 풀어 쓴 **대상**이다.
PRED = re.compile(r'(니다|세요|십시오|는다|ㄴ다|었다|았다|이다|해요|네요)$')


def words(t):
    out = set()
    for w in re.findall(r'[가-힣]{2,}', t):
        w = stem(w)
        if len(w) >= 3 and w not in STOP and not PRED.search(w):
            out.add(w)
    return out


def main():
    html = io.open(sys.argv[1], encoding='utf-8', errors='replace').read()
    blocks = prose_blocks(html)
    psets = [(i, t) for i, (k, t, _) in enumerate(blocks) if k == 'pset']
    if not psets:
        print('문제 블록(.pset)이 없어 검사할 것이 없습니다.'); return 0

    # 각 문제에만 나오는 낱말 = 그 문제의 고유어
    freq = collections.Counter()
    for _, t in psets:
        freq.update(words(t))

    hits = []
    for idx, t in psets:
        uniq = [w for w in words(t) if freq[w] == 1 and len(w) >= 3]
        if not uniq:
            continue
        # 같은 절 안에서 문제를 예고하는 것은 바로 뒤에 실물이 오므로 혼란이 아니다.
        # 그 절이 시작되기 **전**에 이미 내용을 풀어 쓴 자리만 잡는다.
        sec = max([j for j in range(idx) if blocks[j][0] == 'head'], default=0)
        before_raw = ' '.join(b[1] for b in blocks[:sec] if b[0] == 'text')
        before = {stem(w) for w in re.findall(r'[가-힣]{2,}', before_raw)}
        early = sorted({w for w in uniq if w in before})
        if early:
            head = t[:36]
            for w in early[:4]:
                # 그 낱말이 앞에서 쓰인 문장을 찾아 보인다
                m = re.search(r'[^.!?]{0,60}' + re.escape(w) + r'[^.!?]{0,50}', before_raw)
                hits.append((w, head, (m.group(0).strip() if m else '')))

    print(f'문제 블록 {len(psets)}개 · 앞선 언급 {len(hits)}건')
    for w, head, ctx in hits:
        print(f'  ✗ «{w}» — 「{head}…」보다 먼저 쓰였습니다')
        print(f'      앞자리: …{ctx[:88]}…')
    if hits:
        print('\n아직 주지 않은 것으로 설명한 자리입니다. 그 낱말을 빼거나, 설명을 문제 뒤로 옮기거나,')
        print('그 자리에서 뜻을 풀어 주십시오. 읽는 사람이 되돌아가게 만들지 않습니다.')
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
