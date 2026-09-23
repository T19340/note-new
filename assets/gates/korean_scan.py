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
              명사 겹싸기)과 번역투·비유, 그리고 **문장의 수준**(제목을 되풀이한 첫 문장 ·
              존재만 알리는 서술 · 한 문단 같은 낱말 세 번)이 여기 있다. 마지막 갈래는
              표현이 틀려서가 아니라 **그 문장이 하는 일이 없어서** 걸린다.
              **전량을 하나씩 읽고 판정해야 한다.**
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
        # 한 음절 명사도 잡는다. {2,}로 두었더니 "식 하나로 정해집니다"가 통째로 빠졌다 —
        # 정작 관사 자국은 짧은 명사(식·말·점·곳·줄)에 더 잘 붙는다.
        ('명사 + 하나', r'[가-힣]+\s하나(?![도둘셋])'),
        # '필요한 재료'처럼 형용사 어미 -한은 앞 글자가 한글이므로 제외한다.
        ('한 + 분류사', r'(?<![가-힣])한\s(?:' + CLS + r')(?![가-힣])'),
        ('한 + 명사', r'(?<![가-힣])한\s(?!번|가지|편|쪽|장|개|명|권|줄|차례|대|그루|마리|벌|쌍|'
                      r'켤레|채|척|톨|자루|칸|걸음|판|때|참|동안|달|해|살|시|분|초)[가-힣]{2,}'),
    ], r'하나(뿐|씩|도 |마다)|어느 하나|다른 하나|하나는 |하나가 아니|하나로 묶|'
       r'(중|가운데|중에서) 하나|한 치도|한 점도|한 글자도|한 번도'),

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

    # 문장의 수준은 뜻이 맞는지와 별개로 본다(`content.md` 머리말). 뜻이 통하는 것은 최저
    # 조건이지 합격선이 아니다. 여기 걸리는 것은 티가 나는 꼴뿐이고, 나머지는 사냥 패스 ⑫.
    ('문장의 수준 — 하는 일이 없는 문장', [
        # "…를 다룹니다 / …문제가 있습니다"는 무엇이 어떻다는 내용이 없다. 그 내용을 바로 쓴다.
        ('"…를 다룹니다 / 알아봅니다" — 내용을 바로 쓴다',
         r'[을를]\s*(다룹니다|알아봅니다|살펴봅니다|짚어 봅니다|소개합니다)'),
        ('"…문제가 있습니다" 류 — 무엇이 어떤지를 쓴다',
         r'(문제|경우|상황|방법|자리|대목|차이)[가이]\s*있습니다'),
    ], None),

    # 개념이 있는 자리에 일상 비유가 앉으면 독자는 뜻을 고를 수 없다. 실측: 부제의 "서로
    # 얽혀 있어도"가 "서로 독립이 아니어도"를 뜻했는데, 같은 노트 본문은 '독립'을 아홉 번
    # 제대로 쓰고 있었다. 한 노트가 같은 것을 두 이름으로 부른 셈이다(`content.md` §11).
    ('개념 자리에 들어온 일상어', [
        ('얽히다·엮이다 — 가리키는 개념의 이름을 대라(독립이 아님·종속·상관 등)',
         r'얽[히혀힌힘힐]|엮[이여인]|뒤엉|맞물[리려린]'),
        ('"서로 영향을 주다 / 따라 움직이다 / 붙어 다니다" — 같은 자리',
         r'서로\s*영향|따라\s*움직|붙어\s*다니|딸려\s*(가|다니)'),
        ('"…와 상관없이" — 통계의 상관(correlation)과 부딪힌다. "관계없이"로',
         r'상관\s*(없|않)'),
    ], None),

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
        # 셸이 쓰는 패널 라벨(— 목차 —, — §1.1 —)은 문장을 잇는 줄표가 아니라 구분 기호다.
        # 모든 노트에 똑같이 들어 있어, 잡으면 판정 목록만 매번 불린다.
        ('줄표로 문장 잇기 — 접속어로 끊어 쓸 자리인지 본다', r'[—–]'),
    ], r'—\s*(목차|§|참고)|(목차|§[\d.]*|자료)\s*—'),
]

# 낱말 편중표에서 뺄 말 — 조사·의존명사·흔한 기능어
STOP = set('''그리고 그러나 그래서 그런데 하지만 다만 또는 여기 거기 저기 이것 그것 무엇 어디
같은 다른 모든 어떤 이런 그런 저런 위의 아래 다음 이제 지금 아까 먼저 나중 자체 경우 때문
것은 것이 것을 것도 수가 수는 대로 만큼 까지 부터 에서 에게 한테 보다 처럼 마다 이나 라도
있습니다 없습니다 합니다 입니다 됩니다 옵니다 갑니다 봅니다'''.split())

PROSE_KINDS = ('p', 'li')          # 문장 연타는 산문 블록에서만 센다


# 글을 나르지 않는 껍데기. 텍스트는 이 바깥의 가장 가까운 조상에 붙인다.
INLINE = {'b', 'i', 'em', 'strong', 'span', 'a', 'sup', 'sub', 'code', 'u', 'small',
          'mark', 'abbr', 'kbd', 'var', 'del', 'ins', 'q', 'cite', 'time', 'label'}
VOID = {'br', 'img', 'input', 'hr', 'meta', 'link', 'source', 'col', 'area', 'wbr'}


def strip_excluded(src):
    """검사에서 빼는 것은 여기 한 곳에만 적는다. 무엇을 왜 뺐는지 셀 수 있어야 한다."""
    cuts = []
    def cut(pat, why, s):
        n = [0]
        def f(m):
            n[0] += len(re.findall(r'[가-힣]', re.sub(r'<[^>]+>', ' ', m.group(0))))
            return ' '
        s = re.sub(pat, f, s)
        if n[0]:
            cuts.append((why, n[0]))
        return s
    s = cut(r'(?is)<(script|style)\b.*?</\1>', '스타일시트·코드(한국어 문자열은 따로 검사)', src)
    s = cut(r'(?s)<!--.*?-->', '주석', s)
    s = cut(r'(?is)<(p|div|span)[^>]*class="[^"]*\b(pen|orig|enans|en)\b[^"]*"[^>]*>.*?</\1>',
            '영어 원문(고쳐 쓰면 인용이 깨진다)', s)
    s = re.sub(r'data-tex="[^"]*"', ' ', s)       # 수식은 texscan이 본다
    return s, cuts


def text_nodes(s):
    """모든 텍스트 노드를 가장 가까운 블록 조상에 묶어 (태그, 글)로 돌려준다.

    예전에는 `p·li·h·td·th·figcaption`만 뽑았다. 그 바깥의 글 — 문제 머리표(.ph/.tg),
    그림 태그(.figtag), 캔버스 설명(.sub), 버튼 라벨, 접기 요약(summary), 패널 카드의 값 —
    은 **한 번도 검사된 적이 없었다.** 실측으로 노트의 한글 16%가 검사 밖이었다.
    학생이 읽는 글이면 검사한다. 화이트리스트는 빠뜨린 것을 조용히 만든다."""
    blocks, order, stack, pos, uid = {}, [], [('body', 0)], 0, 0
    def put(txt):
        key = next((u for n, u in reversed(stack) if n not in INLINE), 0)
        name = next((n for n, _ in reversed(stack) if n not in INLINE), 'body')
        if key not in blocks:
            blocks[key] = [name, []]
            order.append(key)
        blocks[key][1].append(txt)

    for m in re.finditer(r'(?s)<(/?)([a-zA-Z][\w-]*)[^>]*?(/?)>', s):
        if s[pos:m.start()].strip():
            put(s[pos:m.start()])
        pos = m.end()
        closing, name = m.group(1), m.group(2).lower()
        if closing:
            if any(n == name for n, _ in stack):
                while stack and stack.pop()[0] != name:
                    pass
        elif not m.group(3) and name not in VOID:
            uid += 1
            stack.append((name, uid))
    if s[pos:].strip():
        put(s[pos:])
    return [(blocks[k][0], ' '.join(blocks[k][1])) for k in order]


def js_strings(src):
    """그림 코드 안의 한국어 문자열. readout·퀴즈 피드백·버튼 라벨은 화면에 그대로 뜬다.

    스크립트를 통째로 빼 두었더니 이 글이 검사 밖이었다. 그렇다고 코드 전체를 훑으면
    예전처럼 오탐만 쏟아지므로(CSS 주석의 줄표 8건), **한글이 든 문자열 리터럴만** 본다."""
    out = []
    for m in re.finditer(r'(?is)<script\b([^>]*)>(.*?)</script>', src):
        if 'application/json' in m.group(1):
            continue                     # 데이터는 수치 게이트가 본다
        for lm in re.finditer(r'"([^"\\\n]{0,400})"|\'([^\'\\\n]{0,400})\'|`([^`\\]{0,400})`',
                              m.group(2)):
            t = (lm.group(1) or lm.group(2) or lm.group(3) or '').strip()
            if re.search(r'[가-힣]', t):
                out.append(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)).strip())
    return out


def blocks_of(src):
    """노트에 실리는 글 전부를 (종류, 글) 목록으로 뽑는다."""
    s, _cuts = strip_excluded(src)
    if '<' not in s or '>' not in s:
        raw = [('p', x) for x in s.split('\n')]
    else:
        raw = text_nodes(s)

    out, seen = [], set()
    for kind, b in raw:
        t = re.sub(r'(?s)\\\[.*?\\\]|\\\(.*?\\\)', ' [식] ', b)
        t = re.sub(r'(?s)\$\$.*?\$\$', ' [식] ', t)
        t = re.sub(r'\$[^$\n]{0,200}?\$', ' [식] ', t)
        t = re.sub(r'<[^>]+>', ' ', t)
        t = re.sub(r'&[a-z]+;|&#\d+;', ' ', t)
        t = re.sub(r'(\s*\[식\]\s*)+', ' [식] ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        if t and t not in seen:
            seen.add(t); out.append((kind.lower(), t))
    for t in js_strings(src):
        if t and t not in seen:
            seen.add(t); out.append(('js', t))
    return out


def coverage(src):
    """검사한 글자 수와 뺀 글자 수를 센다. 빠짐없이 보았는지는 세어 봐야 안다.

    블록 목록은 같은 글을 한 번만 보므로(목차가 절 제목을 되풀이하는 식), 검사한 쪽도
    중복을 없앤 뒤에 견준다. 그러지 않으면 중복이 '누락'으로 보여 진짜 구멍을 덮는다."""
    s, cuts = strip_excluded(src)
    if '<' in s and '>' in s:
        nodes = text_nodes(s)
    else:
        nodes = [('p', x) for x in s.split('\n')]
    uniq, total = set(), 0
    for b in js_strings(src):
        if b and b not in uniq:
            uniq.add(b); total += len(re.findall(r'[가-힣]', b))
    for _, b in nodes:
        t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', b)).strip()
        if t and t not in uniq:
            uniq.add(t)
            total += len(re.findall(r'[가-힣]', t))
    seen = sum(len(re.findall(r'[가-힣]', t)) for _, t in blocks_of(src))
    return total, seen, cuts


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



def title_echo(html):
    """부제·요지의 첫 문장이 제목을 바꿔 말한 것인지 본다.
    제목을 읽은 독자에게 아무것도 주지 않는 첫 문장은 노트에서 가장 흔한 빈 서술이다."""
    t = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', html)
    if not t:
        return []
    title = content_words(re.sub(r'<[^>]+>', ' ', t.group(1)))
    out = []
    for cls in ('subtitle', 'summary'):
        m = re.search(r'(?is)class="[^"]*\b' + cls + r'\b[^"]*"[^>]*>(.*?)</(?:p|div)>', html)
        if not m:
            continue
        txt = re.sub(r'<[^>]+>', ' ', m.group(1))
        first = re.split(r'(?<=[.!?])\s', re.sub(r'\s+', ' ', txt).strip())[0]
        share = echo_of(title, first)
        if share is not None:
            out.append((cls, first[:70], share))
    return out


PART = re.compile(r'(으로|에서|에게|에는|이라|라는|하는|한다|합니다|입니다|이다|들이|들은|들을|'
                  r'은|는|이|가|을|를|의|에|도|만|과|와|로|나|랑|께|야)$')


def stem(w):
    """조사를 떼어 낸 꼴로 견준다. '개수'와 '개수의'가 다른 말로 세어지면 검사가 눈을 감는다."""
    prev = None
    while prev != w:
        prev, w = w, PART.sub('', w)
    return w if len(w) >= 2 else prev


def content_words(t):
    return {w for w in (stem(x) for x in re.findall(r'[가-힣]{2,}', t))
            if len(w) >= 2 and w not in STOP}


def echo_of(hw, first, share_min=0.6, new_min=3):
    """제목을 되풀이하면서 **새로 보태는 말이 없는** 첫 문장인가. 겹침 비율을 돌려준다.

    제목의 낱말을 쓰는 것 자체는 정상이다 — 그것이 그 절의 주제어이기 때문이다. 겹침만 보면
    잘 쓴 문장까지 걸린다(실측: "분포를 구할 수 없는 상황에서도 개수의 평균은 구할 수
    있습니다"가 「개수의 평균」과 100% 겹쳐 잡혔다). 걸러야 할 것은 제목 말고는 말하는 것이
    없는 문장이므로, 겹침과 함께 **제목 밖의 낱말이 몇 개인지**를 같이 본다."""
    fw = content_words(first)
    if not fw or not hw:
        return None
    share = len(fw & hw) / len(hw)
    return share if share >= share_min and len(fw - hw) < new_min else None


def heading_echo(blocks):
    """절 제목을 말만 바꿔 되풀이한 첫 문장을 찾는다.

    부제만의 버릇이 아니다. 절을 여는 한두 문장은 본문을 다 쓴 뒤에 채우는 칸이라, 제목을
    다시 적어 놓고 넘어가기 쉽다. 제목을 읽은 독자는 그 문장에서 아무것도 얻지 못한다.
    제목의 실질 낱말이 하나뿐이면 우연히 겹치므로 둘 이상일 때만 본다."""
    out = []
    for i, (kind, t) in enumerate(blocks):
        if not kind.startswith('h'):
            continue
        hw = content_words(re.sub(r'^[\d.\s]+', '', t))
        if len(hw) < 2:
            continue
        nxt = next((x for x in blocks[i + 1:] if x[0] in PROSE_KINDS), None)
        if not nxt:
            continue
        ss = split_sents(nxt[1])
        share = echo_of(hw, ss[0]) if ss else None
        if share is not None:
            out.append((t[:30], ss[0][:74], share))
    return out


# 일상어에도 있어서 학생이 아는 뜻으로 읽고 지나가는 낱말들. 처음 쓰는 자리에서 원어를
# 밝히고 일상 뜻과 어디가 다른지 적어야 한다(`content.md` §11).
OVERLAP = ['독립', '상관', '기댓값', '정규', '유의', '신뢰구간', '표본', '수렴', '조건부',
           '모수', '분산', '편향', '효용', '한계', '탄력성', '수요', '자산', '부채', '자본',
           '수익', '비용', '발생주의', '감가상각']


def term_gloss(blocks, extra=()):
    """개념어가 처음 나오는 자리에 원어가 붙어 있는지 본다.

    한국어 술어만 주면 학생이 교재·강의·시험지의 영어와 잇지 못한다. 시험이 영어로 나오는
    과목이면 그대로 실점이다. 겹침 낱말(OVERLAP)은 더 위험하다 — 학생이 이미 아는 일상 뜻으로
    읽고 넘어가므로, 처음 보는 용어보다 조용히 틀린다."""
    want = [w for w in list(OVERLAP) + [x for x in extra if x] if w]
    out, seen = [], set()
    for kind, t in blocks:
        for w in want:
            if w in seen or w not in t:
                continue
            seen.add(w)
            i = t.index(w)
            # 원어는 그 낱말 바로 뒤 괄호에 붙인다. 같은 문장 안이면 붙은 것으로 본다.
            if not re.search(r'[(（][^)）]*[A-Za-z]{3}', t[i:i + 60]):
                out.append((w, t[max(0, i - 24):i + 56]))
    return out


def word_churn(blocks, times=3):
    """한 문단 안에서 같은 실질 낱말이 세 번 이상 나오면 문장이 제자리를 도는 신호다."""
    out = []
    for kind, t in blocks:
        if kind not in PROSE_KINDS:
            continue
        c = collections.Counter()
        for w in re.findall(r'[가-힣]{3,}', t):
            w = re.sub(r'(으로|에서|입니다|합니다|이고|은|는|이|가|을|를|의|에|도|만|과|와|로)$', '', w)
            if len(w) >= 2 and w not in STOP:
                c[w] += 1
        for w, n in c.items():
            if n >= times:
                out.append((w, n, t[:70]))
    return out


def read_terms(path):
    """이 노트의 핵심 용어 목록. 구조 게이트가 쓰는 파일을 그대로 본다 — 용어를 두 곳에
    적게 하면 한쪽만 고쳐진다."""
    if not path or not os.path.exists(path):
        return []
    out = []
    for ln in io.open(path, encoding='utf-8'):
        ln = re.sub(r'#.*', '', ln).strip()
        if ln and re.search(r'[가-힣]', ln):
            out.append(ln.split()[0])
    return out


def run(fn, judged, terms=()):
    raw = io.open(fn, encoding='utf-8', errors='replace').read()
    blocks = blocks_of(raw)
    sents = [x for _, t in blocks for x in split_sents(t)]
    total, seen, cuts = coverage(raw)
    cut_txt = ' · '.join(f'{w} {n}자' for w, n in cuts) or '없음'
    print('==', os.path.basename(fn), f'· 블록 {len(blocks)} · 문장 {len(sents)}')
    print(f'  검사 범위: 한글 {seen:,}자 / {total:,}자'
          + (f' — 못 본 {total - seen:,}자' if total > seen else ' (빠짐없음)'))
    print(f'  검사에서 뺀 것: {cut_txt}')

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

    LV = '문장의 수준 — 하는 일이 없는 문장'
    for cls, first, share in title_echo(raw):
        nj += 1
        judged.append((LV, '첫 문장이 제목의 바꿔 말하기', first))
        print(f'     ▸ {cls}의 첫 문장이 제목과 낱말이 {share:.0%} 겹칩니다 — 제목이 이미 말한 것을 빼십시오')
        print(f'         «{first}»')
    ech = heading_echo(blocks)
    if ech:
        print(f'     ▸ 절 제목을 되풀이한 첫 문장 — {len(ech)}건 (제목이 말하지 않은 것부터 씁니다)')
        for head, first, share in ech:
            nj += 1
            judged.append((LV, f'절 제목 「{head}」을 되풀이', first))
            print(f'         「{head}」 {share:.0%}  «{first}»')
    gloss = term_gloss(blocks, terms)
    if gloss:
        print(f'     ▸ 원어를 밝히지 않은 개념어 — {len(gloss)}건 (처음 쓰는 자리에 괄호로 붙입니다)')
        for w, ctx in gloss[:6]:
            print(f'         «{w}»  …{ctx}…')
        for w, ctx in gloss:
            nj += 1
            judged.append(('개념어 · 원어 병기', f"'{w}' 처음 쓰는 자리", ctx))
    churn = word_churn(blocks)
    if churn:
        print(f'     ▸ 한 문단에 같은 낱말 3회 이상 — {len(churn)}건 (문장이 제자리를 도는 신호)')
        for w, n, t in churn[:3]:
            print(f'         «{w}» {n}회  {t}')
        for w, n, t in churn:
            nj += 1
            judged.append((LV, f"'{w}' {n}회 반복", t))

    chars, top = bias_table(sents)
    print(f'     낱말 편중표 (본문 한글 {chars:,}자) — 주제어가 아닌데 상위면 다의어 고정을 의심')
    for w, c in top:
        print(f'         {w:<10} {c:>4}  ' + '█' * min(28, c * 28 // max(top[0][1], 1)))

    print(f'  요약: HARD {nh}건 · 판정 {nj}건 · 연타 {len(runs)}구간')
    # 검사 범위가 100%가 아니면 그 노트는 검사된 적이 없는 글을 품고 있다. 실측: 추출기가
    # 태그 화이트리스트였을 때 노트 한글의 16%(682자)가 한 번도 검사되지 않았고, 거기에
    # 다른 노트에서 따라온 <title>이 들어 있었다.
    return nh + (1 if total > seen else 0)


SELFTEST = [
    ('개수의 평균', '개수의 평균을 구하는 문제를 다룹니다.', True),
    ('지시자 변수', '지시자 변수를 알아봅니다.', True),
    ('개수의 평균', '분포를 구할 수 없는 상황에서도 개수의 평균은 구할 수 있습니다.', False),
    ('비복원추출', '앞의 결과가 뒤의 확률을 바꾸는 상황입니다.', False),
]


def selftest():
    """검사기가 살아 있는지 본다. 규칙이 조용히 죽는 일이 실제로 있었다 — 정규식의 경계
    표시가 파일에 제어문자로 들어가 `title_echo`가 어떤 부제와도 매치하지 못한 채 두 번의
    작업 동안 '통과'를 찍었다. **아무것도 못 잡은 것과 잡을 것이 없는 것이 같은 출력으로
    보이면 게이트는 장식이다.** 알려진 결함과 알려진 정상을 넣어 그 둘을 갈라 놓는다."""
    bad = 0
    for head, first, want in SELFTEST:
        got = bool(heading_echo([('h2', head), ('p', first)]))
        if got != want:
            bad += 1
            print(f'  ✗ 「{head}」 «{first[:40]}» 잡힘={got} 기대={want}')
    if not title_echo('<h1>제목 자리</h1><p class="subtitle">제목 자리를 다룹니다.</p>'):
        bad += 1
        print('  ✗ 부제 검사가 알려진 결함을 못 잡습니다 — 선택자나 정규식이 깨졌습니다')
    if term_gloss([('p', '사건이 서로 독립이면 곱으로 나눕니다.')]) == []:
        bad += 1
        print('  ✗ 원어 병기 검사가 알려진 결함을 못 잡습니다')
    if term_gloss([('p', '사건이 서로 독립(independent)이면 곱으로 나눕니다.')]) != []:
        bad += 1
        print('  ✗ 원어 병기 검사가 정상까지 잡습니다')
    # 실제로 새어 나간 문장을 그대로 넣어 둔다. 규칙을 좁게 써서 놓친 자리는 다시 좁아진다.
    for sent, why in [('확률에서는 식 하나로 정해집니다.', "한 음절 명사 + '하나'"),
                      ('일상어와 다른 자리가 있습니다.', '존재만 알리는 문장')]:
        if not any(hits_for([sent], p, re.compile(sk) if sk else None)
                   for _, pats, sk in JUDGE for _, p in pats):
            bad += 1
            print(f'  ✗ 판정 규칙이 알려진 결함을 못 잡습니다 — {why}: 「{sent}」')
    if not any(re.search(p, '막힌 자리의 정체는 적분이었습니다') for p, _ in HARD):
        bad += 1
        print('  ✗ HARD 규칙이 알려진 결함을 못 잡습니다')
    return bad


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

    bad = selftest()
    if bad:
        print(f'자체 시험 실패 {bad}건 — 검사기가 깨졌습니다. 결과를 믿지 마십시오.\n')

    # 용어 파일은 지정하지 않으면 검사 대상 옆에서 찾는다.
    if '--terms' in sys.argv:
        i = sys.argv.index('--terms')
        tf = sys.argv[i + 1] if len(sys.argv) > i + 1 else ''
        args = [a for a in args if a != tf]
    else:
        tf = os.path.join(os.path.dirname(os.path.abspath(args[0])), 'terms.txt') if args else ''
    terms = read_terms(tf)

    judged = []
    bad += sum(run(f, judged, terms) for f in args)

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
