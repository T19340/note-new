# -*- coding: utf-8 -*-
"""한국어 문체 검사.  usage: python korean_scan.py <html 또는 조각 파일…>

`ko_tell_scan.py`와 `literal_scan.py`를 합친 것이다. 둘로 나눠 두었더니 본문 추출 함수가 두
벌로 복사됐고, 손을 대다 갈라져서 **납품을 막는 HARD 게이트가 제목과 표 칸을 못 보는** 상태가
됐다. 실제로 "1.1 길은 둘뿐이다"는 절 제목이었고, 그 꼴이면 게이트를 통과한다. 추출기는 한
벌이어야 한다.

세 층으로 나눠 보고한다.

  1. HARD   — 맥락과 무관하게 고쳐야 하는 것. 하나라도 남으면 종료코드 1.
  2. 판정   — 맥락상 정상인 경우가 많다. 세어서 보여 주기만 하고 통과시킨다.
              직역 자국(관사 '하나/한' · 다의어 고정 · 유정물 전용 말 · 영어 주어 ·
              명사 겹싸기)과 번역투·비유가 여기 있다. **전량을 하나씩 읽고 판정해야 한다.**
  3. 통계   — 짧은 문장 연타 구간, 낱말 편중표.

**이 검사를 통과해도 자연스러운 한국어라는 뜻은 아니다.** 정규식은 알려진 패턴만 잡는다.
지워도 되는 문장, 글쓴이만 아는 은어는 사람이 읽어야 드러난다 — `references/hunt-pass.md`의
사냥 패스를 반드시 함께 돌린다. 판정 기준과 고친 예도 거기에 있다.

낱말 편중표가 이 검사에서 유일하게 **아직 모르는 결함**을 잡는 장치다. 주제어가 아닌 낱말이
빈도 상위에 있으면 그 말이 여러 영어 낱말을 혼자 떠맡고 있다는 뜻이다(실측: 확산모형 장에서
'자리'가 48회로 1위, 평균·잡음·분산보다 위).
"""
import io, re, sys, os, collections
sys.stdout.reconfigure(encoding='utf-8')

CLS = '장|개|명|권|줄|번|차례|대|그루|가지|마리|벌|쌍|켤레|채|척|톨|자루|편|쪽|칸|걸음|판'

# ── 1. HARD — 고쳐야 하는 것 ──────────────────────────────────────
# 정밀도를 먼저 맞춘다. 오탐을 내는 게이트는 곧 무시당하고, 무시당한 게이트는 없는 것과 같다.
# 그래서 "답은 5입니다"(값을 바로 말함)나 "서랍을 한 줄로 늘어놓습니다"(글자 그대로)는 잡지
# 않고, 상투구가 완성된 것만 잡는다. 새 유형도 실제 노트로 오탐을 확인한 뒤에 HARD로 올린다.
HARD = [
    (r'(정체|이유|까닭|비밀|열쇠)[은는이가][^.!?]{0,18}(였습니다|이었습니다)',
     '극적 제시 "…의 정체는 X였습니다" → 바로 진술한다'),
    (r'(정체|비밀|열쇠)[은는이가][^.!?]{0,14}(입니다|이다)[.」"]',
     '극적 제시 "…의 정체는 X입니다" → 그냥 "…는 X입니다"로'),
    (r'(답|이유|까닭|방법|길|할 일|남은 일)[은는이]\s*(하나|둘|셋)(뿐)?(입니다|였습니다|이다)',
     '카운트다운 "…는 하나입니다" → 세지 말고 바로 말한다'),
    (r'(이유|까닭|사연)[이가]\s*있습니다',
     '예고 후 공개 "…이유가 있습니다" → 다음 문장과 합쳐 바로 말한다'),
    (r'(길|방법|경우|선택지|갈래)[은는이가]\s*(하나|둘|셋|넷|두 가지|세 가지)\s*(뿐|밖에)',
     '카운트다운 "…는 둘뿐입니다" → 세지 말고 바로 열거한다'),
    (r'한 (줄|문장)(로|으로|이면|만으로)?\s*(끝|충분|족합|정리하면|요약하면|말하면 끝)',
     'AI 상투구 "이 한 줄로 끝납니다" 류'),
    (r'(핵심|요지|요점)입니다', 'AI 상투구 "…핵심입니다"'),
    (r'놀랍게도|흥미롭게도|무려|자그마치', '감정 강요·과장 부사 → 빼거나 사실로'),
    (r'되어집니다|되어진|되어졌습니다', '이중 피동'),
    (r'(가|이) 말해 줍니다|식이 말해|가 속삭|이 외칩니다', '의인화'),
    (r'여기가 (전환점|분기점|갈림길)|여기서 갈립니다', 'AI 상투구 "여기가 전환점입니다"'),
]

# ── 2. 판정 — 읽고 정해야 하는 것 ─────────────────────────────────
# 영어로 생각한 뒤 옮기면 **뜻은 맞는데 한국어가 아닌** 문장이 남는다. 읽으면 어색한데 어디가
# 어색한지 짚기 어렵고 렌더도 게이트도 통과한다. 갈래별로 모아 전량을 보인다.
JUDGE = [
    ("관사를 옮긴 '하나 / 한'", [
        ('하나의 X — 직역이 거의 확실하다', r'하나의\s+\S+'),
        ('명사 + 하나', r'[가-힣]{2,}\s하나(?![도둘셋])'),
        # '필요한 재료'처럼 형용사 어미 -한은 앞 글자가 한글이므로 제외한다.
        ('한 + 분류사', r'(?<![가-힣])한\s(?:' + CLS + r')(?![가-힣])'),
        ('한 + 명사', r'(?<![가-힣])한\s(?!번|가지|편|쪽|장|개|명|권|줄|차례|대|그루|마리|벌|쌍|'
                      r'켤레|채|척|톨|자루|칸|걸음|판|때|참|동안|달|해|살|시|분|초)[가-힣]{2,}'),
    ], r'하나(뿐|씩|도 |마다)|어느 하나|다른 하나|하나는 |하나가 아니|하나로 묶|'
       r'한 치도|한 점도|한 글자도|한 번도'),

    ('다의어를 첫 뜻으로 고정', [
        ("'줄' — 무엇이 놓여 있는지 이름을 대라",
         r'(?<![가-힣])줄(?:[이가을를로에은는만씩])?(?=[\s,.)·…"」\']|$)'),
        ("'걸음' — 유도의 단계인가, 학습 반복인가, 진짜 걸음인가",
         r'(매|한|두|세|네|첫|마지막|학습|여러|번째)\s?걸음'),
        ("'길' — 방법·방식을 '길'로 세고 있지 않은가",
         r'(가지|째|의)\s길|두 길|길입니다|길을 고른|가는 길'),
        ("'읽다' — 해석하다·따져 보다가 갈 자리인가",
         r'(으로|로|쪽에서|축에 대고)\s?읽[으은는어]'),
        ("'닫다' — 끝내다·완성되다·순환에 빠지다가 갈 자리인가", r'닫[았혔]|원[이을]\s닫'),
        ("'주다' — 매기다·내놓다·나오다가 갈 자리인가",
         r'(밀도|가능도|값|것)[을를]\s주[는면]|준\s(것|값)[은이]'),
    ], r'닫힌 꼴|줄\s+(아는|아느|알|아야|아신|모르|몰라)|그런 줄|줄\s*수\s*(있|없|가)|'
       r'내리막|한 걸음씩 걸'),

    ('유정물 전용 말을 무정물에', [
        ('데려오다 — 분포·함수는 마련한다·도입한다', r'데려[오와온다]'),
        ('먹이다 — 수식·절차는 넣는다·대입한다', r'먹이[는다]|먹일|먹여'),
        ('물건 — 추상 대상은 양·대상·것', r'물건'),
        ('일하다 — 규칙·도구는 쓰인다·구실을 한다', r'일했|일합니다|일한\s셈'),
        ('요금·공짜 — 손실은 손해·대가, for free는 그냥·덤으로', r'요금|공짜'),
        ('정직한 — 사람의 품성이다. 방법·값에는 곧이곧대로·원칙대로', r'정직[한하]'),
        ('차이를 만들다 — make a difference. 차이가 난다·결정적이다', r'차이를\s만[듭드]'),
    ], None),

    ('영어 주어·대용어를 그대로', [
        ("'우리' — 한국어는 이 주어를 비운다", r'(?<!봉)우리[가는를]'),
        ('장·절·그림이 행위 주체 — 처소격 "6장에서"로', r'\d장[이은]\s|이 문서[가는]\s|그림\s[\d.]+[가이]\s'),
        ("'이것/그것'이 앞 문장을 통째로 받음 — 이름을 다시 부른다", r'(이것|그것)[이은을를]\s'),
    ], r'우리말|우리나라'),

    ('명사로 한 번 더 싸기', [
        ("'…라는 사실/점입니다' — 어미가 이미 명사화한다", r'(다|라|이라)는\s(사실|점)|이\s사실|그\s사실'),
        ("'…다는 것이 보입니다/알려져 있습니다'", r'(다|라)는\s것\s?이\s(보입|알려)'),
        ("'…되고 있습니다 / 되어 있습니다' — 진행 중인 동작인가", r'(되고\s있|되어\s있|어지고\s있)'),
        # "X입니다. Y이기 때문입니다." — 한 번이면 강조, 한 절에 여러 번이면 단정→변명의 반복.
        ('문장 전체가 이유절 — 앞 문장에 접어 넣는다', r'^[^.!?]{0,70}기?\s때문입니다\.?$'),
    ], r'사실상'),

    ('번역투·분열문·비유', [
        ('"…것뿐입니다 / …이 전부입니다"', r'(것|일)뿐입니다|(의|이|가) 전부입니다'),
        ('분열문 "바로 …" / "다름 아닌"', r'바로 (그|이|여기|그것|이것)|다름 아닌'),
        ('분열문 "그것이 …입니다"', r'그것이 [^.]{0,20}(입니다|이유입니다)|정확히 (그것|이것|그 )'),
        ('AI 접속구', r'중요한 것은|결정적인 것은|주목할 점은|말 그대로|정석입니다|예고편'),
        ('비유', r'그릇|문지기|손잡이|판자|얼굴|태생|여행|항해|손에 (쥐|넣|있)|'
                 r'신호입니다|장면입니다|감각(을|이)'),
        ('번역투 have / provide', r'(을|를) 가집니다|(을|를) 가지고 있|(을|를) 제공합니다'),
        ('번역투 by / make', r'에 의해|에 불과합니다|하게 만듭니다|하도록 만듭니다'),
        ('번역투 from', r'(으로|로)부터'),
        ('줄표로 문장 잇기 — 접속어로 끊어 쓸 자리인지 본다', r'[—–]'),
    ], None),
]

# 낱말 편중표에서 뺄 말 — 조사·의존명사·흔한 기능어
STOP = set('''그리고 그러나 그래서 그런데 하지만 다만 또는 여기 거기 저기 이것 그것 무엇 어디
같은 다른 모든 어떤 이런 그런 저런 위의 아래 다음 이제 지금 아까 먼저 나중 자체 경우 때문
것은 것이 것을 것도 수가 수는 대로 만큼 까지 부터 에서 에게 한테 보다 처럼 마다 이나 라도
있습니다 없습니다 합니다 입니다 됩니다 옵니다 갑니다 봅니다'''.split())

PROSE_KINDS = ('p', 'li')          # 문장 연타는 산문 블록에서만 센다


def blocks_of(src):
    """본문 블록을 (종류, 글) 목록으로 뽑는다. 제목·표 칸까지 본다 — 결함은 거기에도 앉는다."""
    s = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', src)
    s = re.sub(r'(?s)<!--.*?-->', ' ', s)
    # 패널의 참조 카드도 학생이 읽는 글이므로 검사에 넣는다. 목차 링크만 뺀다.
    s = re.sub(r'(?is)<nav class="toc".*?</nav>', ' ', s)        # 상단 목차
    s = re.sub(r'(?is)<div class="(orig|enans)".*?</div>', ' ', s)
    s = re.sub(r'(?is)<span class="en".*?</span>', ' ', s)

    if '<' in s and '>' in s:
        raw = re.findall(r'(?is)<(p|li|figcaption|h[1-4]|td|th)\b[^>]*>(.*?)</\1>', s)
    else:
        raw = [('p', x) for x in s.split('\n')]

    out, seen = [], set()
    for kind, b in raw:
        t = re.sub(r'(?s)\\\[.*?\\\]|\\\(.*?\\\)', ' [식] ', b)
        t = re.sub(r'(?s)\$\$.*?\$\$', ' [식] ', t)
        t = re.sub(r'\$[^$\n]{0,200}?\$', ' [식] ', t)
        t = re.sub(r'data-tex="[^"]*"', ' ', t)
        t = re.sub(r'<[^>]+>', ' ', t)
        t = re.sub(r'&[a-z]+;|&#\d+;', ' ', t)
        t = re.sub(r'(\s*\[식\]\s*)+', ' [식] ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        if t and t not in seen:
            seen.add(t); out.append((kind.lower(), t))
    return out


def split_sents(t):
    return [x.strip() for x in re.split(r'(?<=[.!?])\s+', t) if x.strip()]


def hits_for(sents, pat, skip):
    out = []
    for s in sents:
        for m in re.finditer(pat, s):
            if skip and (skip.search(m.group(0)) or skip.search(s[max(0, m.start() - 6):m.end() + 10])):
                continue
            out.append((m.group(0).strip(), s))
    return out


def bias_table(sents, top=15):
    body = ' '.join(sents)
    chars = len(re.findall(r'[가-힣]', body))
    cnt = collections.Counter()
    for tok in re.findall(r'[가-힣]{2,}', body):
        w = re.sub(r'(으로|에서|에게|에는|이라|라는|하는|한다|합니다|입니다|이다|들이|들은|들을|'
                   r'은|는|이|가|을|를|의|에|도|만|과|와|로|나|랑|께|야)$', '', tok)
        if len(w) >= 2 and w not in STOP:
            cnt[w] += 1
    return chars, cnt.most_common(top)


def run(fn, judged):
    blocks = blocks_of(io.open(fn, encoding='utf-8', errors='replace').read())
    sents = [x for _, t in blocks for x in split_sents(t)]
    print('==', os.path.basename(fn), f'· 블록 {len(blocks)} · 문장 {len(sents)}')

    print('  ── 1. HARD — 고쳐야 합니다')
    nh = 0
    for pat, why in HARD:
        h = hits_for(sents, pat, None)
        if not h:
            continue
        nh += len(h)
        print(f'     [{why}] {len(h)}건')
        for g, s in h[:3]:
            print(f'         · {s[:90]}')
    if not nh:
        print('     없음')

    print('  ── 2. 판정 — 하나씩 읽고 정하십시오')
    nj = 0
    for title, pats, skip in JUDGE:
        sk = re.compile(skip) if skip else None
        sub = []
        for name, p in pats:
            h = hits_for(sents, p, sk)
            if h:
                sub.append((name, h))
        if not sub:
            continue
        print(f'     ▸ {title}')
        for name, h in sub:
            nj += len(h)
            judged.extend((title, name, s) for _, s in h)
            print(f'       [{name}] {len(h)}건')
            for g, s in h[:5]:
                print(f'           «{g}»  {s[:88]}')
            if len(h) > 5:
                print(f'           … 외 {len(h) - 5}건')
    if not nj:
        print('     없음')

    print('  ── 3. 통계')
    runs = []
    for kind, t in blocks:
        if kind not in PROSE_KINDS:
            continue
        ss = split_sents(t)
        if len(ss) < 3:
            continue
        cur = []
        for x in ss:
            ko = len(re.findall(r'[가-힣]', x))
            if 0 < ko <= 24:
                cur.append(x)
            else:
                if len(cur) >= 3:
                    runs.append(cur)
                cur = []
        if len(cur) >= 3:
            runs.append(cur)
    print(f'     짧은 문장 3연속 — {len(runs)}구간 (합칠 자리인지 읽어 본다)')
    for r in runs[:3]:
        print('         · ' + ' / '.join(x[:34] for x in r[:3]))

    chars, top = bias_table(sents)
    print(f'     낱말 편중표 (본문 한글 {chars:,}자) — 주제어가 아닌데 상위면 다의어 고정을 의심')
    for w, c in top:
        print(f'         {w:<10} {c:>4}  ' + '█' * min(28, c * 28 // max(top[0][1], 1)))

    print(f'  요약: HARD {nh}건 · 판정 {nj}건 · 연타 {len(runs)}구간')
    return nh


TRIAGE_HEAD = """# 판정 기록 — 이 파일이 '판정 목록을 읽었다'는 증거다.
#
# 아래 각 줄의 [ ]에 판정을 적는다. 둘 중 하나다.
#   [고침]  실제로 고쳤다. 다시 돌리면 그 줄은 목록에서 사라진다.
#   [유지]  맥락상 정상이다. 왜 그런지 한마디를 뒤에 붙인다.
#
# [ ]로 남은 줄이 하나라도 있으면 검사는 실패한다. 요약만 보고 넘어가는 것을 막기 위해서다.
# 본문을 고치면 그 줄은 자동으로 빠지고, 새로 생긴 것은 [ ]로 다시 붙는다.
"""


def triage(path, items):
    """판정 항목마다 사람의 판단을 받아 적게 한다. 비어 있으면 통과시키지 않는다."""
    old = {}
    if os.path.exists(path):
        for ln in io.open(path, encoding='utf-8'):
            m = re.match(r'\[([^\]]*)\]\s*(.*?)\s*\|\|\s*(.*)$', ln.rstrip('\n'))
            if m:
                old[m.group(3)] = m.group(1).strip()

    lines, blank = [], 0
    for title, name, sent in items:
        key = re.sub(r'\s+', ' ', sent)[:120]
        verdict = old.get(key, '')
        if not verdict:
            blank += 1
        lines.append(f'[{verdict or " "}] {title} · {name} || {key}')

    io.open(path, 'w', encoding='utf-8').write(
        TRIAGE_HEAD + '\n' + '\n'.join(lines) + '\n')
    return blank, len(lines)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    tpath = None
    if '--triage' in sys.argv:
        i = sys.argv.index('--triage')
        tpath = sys.argv[i + 1] if len(sys.argv) > i + 1 else 'triage.txt'
        args = [a for a in args if a != tpath]

    judged = []
    bad = sum(run(f, judged) for f in args)

    if tpath:
        blank, total = triage(tpath, judged)
        print(f'\n판정 기록: {tpath} · 항목 {total}개 · 아직 판정하지 않은 것 {blank}개')
        if blank:
            print('  판정을 적지 않은 항목이 남아 있습니다. 각 줄의 [ ]에 [고침] 또는'
                  ' [유지 · 이유]를 적으십시오.')
            bad += blank

    if bad:
        print('\n통과하지 못했습니다. 고친 뒤 다시 돌리십시오.')
    else:
        print('\nHARD 0 · 판정 완료.')
    sys.exit(1 if bad else 0)
