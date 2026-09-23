#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paper-study 콘텐츠·문체 린터.

voice.md 의 *결함 규칙*을 실행 가능한 점검으로 굳힌다. headless-render-verify(레이아웃·
패널 ID·도형 기하)가 못 잡는, 글의 결을 본다.

설계 원칙(2026-07 개편): 린터는 *결함*만 하드로 막고, *취향*은 소프트 권고로만 둔다.
어투를 정형으로 강제하면 오히려 기계투가 된다는 실측 결과에 따라, 종결 register(합니다체/
평서체) 강제와 은유·자기지시·감정부사 금지는 하드에서 뺐다. 자연스러운 한국어인지는
사람이 정독해 판정하고, 린터는 명백한 번역투·문법 결함과 관찰된 AI 상투구만 잡는다.

검사 항목 (하드 = 종료코드 1, 소프트 = 권고)
  [하드] 1) 번역체·AI 결함     — 영어/일본어 직역, 이중피동, 불필요한 사동, 구어·비표준어,
                                 술어 완결성('세 가지를 보입니다'), 그리고 관찰된 AI 상투구
                                 ('이 한 문장이~' 스포트라이트, 거짓대조, '…함수로 쓰다' calque)
  [하드] 2) 원전 정독 인용 3층 — .src 박스가 하나도 없으면 위반; 각 .src 에 src-en/src-ko 가
                                 둘 다 있어야 한다(한 층이라도 빠지면 위반)
  [소프트] register 혼재       — 합니다체/평서체 중 무엇을 쓰든 자유이나, 한 글 안에서 뒤섞이면 권고
  [소프트] 취향(은유·감정부사·자기지시·셈 등) — 결함이 아니라 취향. 사람이 정독해 판단
  [소프트] 서술형 소제목/수식 주석/판본/정리부사/빈 수식어/의인화/기본 어법/도입 register/
           호응/제목 비유/수식 단위/인용 해설/전제 박스 — 이하 종전과 동일(권고)

인용 박스(.src) 안의 영어 원문/한국어 옮김은 검사에서 제외한다(원문은 영어, 옮김은
논문의 평서체 번역이므로 노트 본문 규칙을 적용하지 않는다).

사용:  PYTHONUTF8=1 python check_content_style.py <note.html> [...]
종료코드: 하드 위반 있으면 1, 없으면 0. 소프트는 종료코드에 영향 없음.
"""
import re
import sys
from pathlib import Path

TAG = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", s)).strip()


def content_html(html: str) -> str:
    """좌측 본문(.content)만 떼어 본다."""
    m = re.search(r'<div class="content">(.*?)</div>\s*<!--\s*/\s*\.?content', html, re.S)
    if m:
        return m.group(1)
    m = re.search(r'<div class="content">(.*)', html, re.S)
    return m.group(1) if m else html


def visible_html(html: str) -> str:
    """CSS/JS를 제외한 보이는 HTML만 남긴다. 패널·헤더 문구도 문체 검사에 포함한다."""
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    return html


def strip_src(content: str) -> str:
    """인용 박스(.src) 전체를 들어낸다 — 문체 검사 대상에서 제외."""
    return re.sub(r'<blockquote class="src".*?</blockquote>', " ", content, flags=re.S)


# ── 문장 분해 헬퍼 ──────────────────────────────────────────────
def _sentences(text: str):
    for sent in re.split(r"(?<=[\.\?!。])\s+", text):
        t = sent.rstrip(" .。?!)」』\"'")
        if t:
            yield t


def _is_pyeongseo(t: str) -> bool:
    # '니다'(합니다체)·'시다'(청유형 봅시다/둡시다)는 존댓말이므로 제외
    return bool(re.search(r"[가-힣]다$", t)
                and not t.endswith("니다") and not t.endswith("시다"))


# ── 소프트: register 혼재 (강제 아님, 뒤섞임만 경고) ────────────
def check_register_mix(content_no_src: str):
    """종결 어투를 합니다체로 쓰든 평서체로 쓰든 자유다. 다만 한 글 안에서 둘이
    섞이면 부자연스러우므로 권고만 한다(voice.md: '한 글 안에서 뒤섞지 않기')."""
    haps = plain = 0
    for m in re.finditer(r'<p(?P<attr>[^>]*)>(?P<body>.*?)</p>', content_no_src, re.S):
        for t in _sentences(strip_tags(m.group("body"))):
            if not re.search(r"[가-힣][다요]$", t):
                continue
            if t.endswith("니다") or t.endswith("시다"):
                haps += 1
            elif _is_pyeongseo(t):
                plain += 1
    out = []
    tot = haps + plain
    if tot >= 12:
        minor = min(haps, plain)
        if minor >= 5 and minor / tot >= 0.15:
            out.append(f"종결 register 혼재 — 합니다체 {haps} · 평서체 {plain}. "
                       f"둘 중 하나로 통일(voice.md: 한 글 안에서 뒤섞지 않기)")
    return out


# ── 하드 1: 번역체·AI 결함 (직역·문법 결함 + 관찰된 AI 상투구) ──
AICHE_HARD = [
    # 영어·일본어 번역투
    (r"다름 아니다", "일본어 번역체 — '~와 같다'"),
    (r"함에 있어", "번역체 — '~할 때/~하면서'"),
    (r"deep dive|deep-dive", "영어 직역 — '심층 분석'"),
    (r"address한다|address합니다", "영어 직역 — '다룬다/해결한다'"),
    (r"non-?trivial", "영어 직역 — '간단하지 않다'"),
    # 문법 결함: 이중피동·불필요한 사동·구어 비표준어
    (r"되어진다|되어집니다", "이중 수동 — 능동으로"),
    (r"(?:되어|되여|보여|보아|나뉘어|모아|쓰여|씌여|읽혀|믿겨|불려|놓여|짜여|닫혀|덮여|걷혀|섞여|갈려|꺾여|뚫려|잊혀)(?:지|진|져|졌|질)",
     "이중피동 — 피동은 한 번만('보여진다→보인다, 나뉘어진다→나뉜다')"),
    (r"(?:소개|금지|접수|등록|연결|접목|숙지|복용|야기|초래|입력|주입|해소|제거|입증|설득|적용|완성|확정|해결|부각|관철|개선)시(?:키|킨|켜|켰|킬|킴)",
     "불필요한 사동 '시키다' — 이미 타동사면 '하다'로('적용시킨다→적용한다'). 증가·감소·안정시키다 같은 참사동만 허용"),
    (r"\s거(?:예요|에요|라고|라구)|같아요|강추|비추|열공|무의(?:했|하다|함|하여|한)",
     "구어·비표준어 — 학술문에 부적합('~할 거라고→것이라고', '무의→유의하지 않음')"),
    # 술어 완결성: 수량 분류사가 머리명사 없이 술어의 목적어·주어로
    (r"(한|두|세|네|다섯|여섯|여러|몇|두세|서너)\s*가지(?:를|가)?\s*(?:보입니다|보인다|보여\s*줍니다|밝힙니다|밝힌다|더합니다|더한다|더했|나옵니다|나왔습니다|나온다|풉니다|풀면|제시합니다|가립니다|가린다)",
     "수량 분류사가 머리명사 없이 술어에 붙음('세 가지를 보입니다') — '세 가지 사실/결과/수정'처럼 머리명사를 다세요"),
    # ── 관찰된 AI 상투구 (2026-07; 실제 산출물에서 반복 검출) ──
    (r"이\s*한\s*(?:문장|줄|식|숫자|그림|표|장면|마디)[이가]\s",
     "AI 리듬 '이 한 문장이~' — 스포트라이트 상투구. 빼고 바로 요점으로 (예: '초록은 …를 압축한다')"),
    (r"(?:지루한|뻔한|한낱|하찮은|사소한|시시한|단순한)[^.。!?]{0,30}(?:이?\s*아니라|아닙니다)",
     "거짓대조 상투구('뻔한 게 아니라 ~') — 아무도 안 한 주장을 가짜 대조항으로 세움. 대조 빼고 직접 진술로"),
    (r"함수로\s*(?:씁니다|쓴다|썼습니다|썼다|쓰는)",
     "번역투 '…함수로 쓰다'(영어 write/express as a function 직역) — '나타낸다/설정한다/둔다/모형화한다'로"),
]


def check_aiche(content_no_src: str):
    text = strip_tags(content_no_src)
    out = []
    for pat, msg in AICHE_HARD:
        for mm in re.finditer(pat, text):
            a = max(0, mm.start() - 14)
            out.append(f"{msg} … '{text[a:mm.end()+10]}'")
    return out


# ── 소프트: 취향(은유·감정부사·자기지시·셈 등) — 결함 아님 ──────
AICHE_SOFT = [
    (r"영리(합니다|하다|한)", "의인화('영리')(취향) — 동작으로 적기"),
    (r"기발(합니다|하다|한)", "의인화('기발')(취향)"),
    (r"논문의 (심장|심장부|백미|압권|정수)", "과장 수사('심장/백미')(취향)"),
    (r"(저자들?[은이]?\s*)?정직(합니다|하다)", "저자 인성 평가('정직')(취향)"),
    (r"(한 수|묘수)\b", "게임 비유(취향)"),
    (r"놀랍게도|흥미롭게도|재미있게도", "감정 강요 부사(취향)"),
    (r"마법", "'마법' 비유(취향)"),
    (r"Voil[aà]|짜잔|Ta-?da|Wow\b", "외래 감탄사(취향)"),
    (r"무려|자그마치", "TV 자막 어투(취향)"),
    (r"셈이다|셈입니다", "번역체 종결('셈')(취향 — 결함은 아님)"),
    (r"적분 한판|계산 한방|한방에", "게임 어조(취향)"),
    (r"펼쳐\s*읽|따라\s*읽|따라다(?:니|닙|녀)|핵심\s*길목|함께\s*떠나|흥미진진|정수를\s*만나|여정을\s*(?:떠|시작)",
     "자기지시 미사여구·여정 은유(취향)"),
    (r"결과를\s*(?:미리\s*)?빚|정체를\s*가리|핵심\s*고리|결과를\s*끌고",
     "극화 비유(취향)"),
    (r"한마디로|읽는\s*법|말풀이|딛고\s*가기|셀프\s*체크|신상명세",
     "튜토리얼 라벨(취향 — 강제 아님)"),
    (r"초록.{0,24}(?:뼈대|그대로\s*보여)", "초록 의인화(취향)"),
    (r"가격을\s*만들\s*수", "'가격을 만들다' 구어(취향)"),
    (r"직접\s*닿", "'직접 닿다' 비유(취향)"),
    (r"못\s*잡(?:나|는다|습니다|음)", "'못 잡다' 구어(취향)"),
]


def check_taste(content_no_src: str):
    text = strip_tags(content_no_src)
    out = []
    for pat, msg in AICHE_SOFT:
        for mm in re.finditer(pat, text):
            a = max(0, mm.start() - 12)
            out.append(f"{msg} … '{text[a:mm.end()+8]}'")
    return out


# ── 하드 2: 원전 정독 인용 3층 ──────────────────────────────────
def check_quote_triad(content: str):
    out = []
    blocks = re.findall(r'<blockquote class="src".*?</blockquote>', content, re.S)
    if not blocks:
        out.append("원문 인용 박스(.src)가 하나도 없음 — 정독 노트의 핵심은 원전 인용")
        return out
    for i, b in enumerate(blocks, 1):
        has_en = "src-en" in b
        has_ko = "src-ko" in b
        if not has_en:
            out.append(f"{i}번째 .src 에 영문 원문(src-en) 없음")
        if not has_ko:
            out.append(f"{i}번째 .src 에 한국어 옮김(src-ko) 없음")
    return out


# ── 소프트 4: 서술형 소제목 ─────────────────────────────────────
def check_seosulhyeong(content: str):
    out = []
    for h in re.findall(r'<h4 class="sub"[^>]*>(.*?)</h4>', content, re.S):
        t = strip_tags(h)
        if not t:
            continue
        if re.search(r"(?:\?|까요|인가요|일까요|나)$", t):
            out.append(f"질문형 소제목 — 답을 제목에 담아 서술형으로: 「{t}」")
            continue
        # 서술형 신호: 공백(여러 어절)·물음/서술 종결·줄표 부제 중 하나라도 있으면 통과
        descriptive = (" " in t or re.search(r"(나|까|가|는가|는지|다|요)[\?\.]?$", t)
                       or re.search(r"\s[—–-]\s", t))
        if not descriptive and len(t) <= 10:
            out.append(f"맨-명사 소제목 가능성 — 서술형으로: 「{t}」")
    return out


# ── 소프트 5: 수식 주석 ─────────────────────────────────────────
def check_eq_annotation(content: str):
    out = []
    for m in re.finditer(r'<div class="eq"[^>]*></div>', content):
        after = content[m.end():m.end() + 800]
        if 'class="tbl"' in after or after.count('class="eqi"') >= 2:
            continue
        out.append("주석 없는 display 수식 — 변수표나 인라인 변수 설명 권고")
    return out


# ── 소프트 6: 판본 상태 ─────────────────────────────────────────
def check_version_status(content: str):
    out = []
    if "chip wp" in content and "판본" not in content:
        out.append("최전선 WP(chip wp)가 있는데 '판본' 주의가 안 보임 — 판본 상태 경고 권고")
    return out


# ── 소프트 7: 정리 부사 남발 ────────────────────────────────────
def check_filler(content_no_src: str):
    text = strip_tags(content_no_src)
    out = []
    for w in ("것이다", "결국", "즉"):
        n = len(re.findall(w, text))
        if n >= 6:
            out.append(f"'{w}' {n}회 — 정리 부사/번역체 종결 남발 점검")
    n = len(re.findall(r"에 있어서", text))
    if n:
        out.append(f"'에 있어서' {n}회 — 번역체 가능성(존재 의미가 아니면 '~에서/~의 경우'로)")
    return out


# ── 소프트: 빈 수식어 ───────────────────────────────────────────
def check_empty_modifier(content_no_src: str):
    text = strip_tags(content_no_src)
    out = []
    for w in ("사실상", "그토록", "한낱"):
        for mm in re.finditer(w, text):
            a = max(0, mm.start() - 12)
            out.append(f"빈 수식어 '{w}' — 정도면 '거의/그렇게', 결론났으면 삭제 … '{text[a:mm.end()+12]}'")
    return out


# ── 소프트: 통계량·시장 의인화 ──────────────────────────────────
def check_stat_anthropomorphism(content_no_src: str):
    text = strip_tags(content_no_src)
    out = []
    for pat, name in ((r"죽어\s*버리", "죽어 버리다"), (r"살아남", "살아남다"), (r"주저앉", "주저앉다")):
        for mm in re.finditer(pat, text):
            a = max(0, mm.start() - 12)
            out.append(f"통계량·시장 의인화 '{name}'(취향) … '{text[a:mm.end()+8]}'")
    return out


# ── 소프트: 기본 어법(korean-grammar.md) 정규식 점검 ───────────
GRAMMAR_SOFT = [
    (r"화시키|화되어지", "'-화시키다/-화되어지다' — '-화하다/-화되다'로(안정화시켰다→안정화하였다)"),
    (r"약\s*[\d.]+\s*[%가-힣]*\s*정도|과반수\s*이상|미리\s*(?:예측|예견|예고|예정)|계속\s*지속|다시\s*재[가-힣]|각각의?\s*개별|서로\s*상이|역전\s*앞",
     "겹말(같은 뜻 중복) — 한쪽을 지운다(약 30% 정도→약 30%, 계속 지속→지속)"),
    (r"(?:요인|변수|결과|데이터|정보|증거|지식|내용|문제|특징|요소|현상|방법|개념|이론|효과|위험)들",
     "추상·집합명사 '-들' — 영어 복수 직역. 단수형으로(결과들→결과)"),
    (r"(?:결코|좀처럼|여간|도무지|그다지)(?:(?!않|없|아니|못|말|뿐).){0,25}[다요](?=[.!?)\s]|$)",
     "부정극성 부사 호응 — 결코·좀처럼·여간은 부정 서술어와 짝(‘결코 우연이다’→‘결코 우연이 아니다’). 오탐 가능, 사람 확인"),
    (r"(?:의미|특성|특징|성격|관계|상관관계|영향력|설명력|예측력|중요성|가능성|효과|기능|책임|권한|한계|성질|값|분포)(?:을|를)\s*(?:가지|가진|갖는|갖고|가졌|가지고)",
     "have 직역 '가지다' — 추상명사엔 '있다/하다/지니다/보이다'로(설명력을 가진다→설명력이 있다)"),
]


def check_grammar_soft(content_no_src: str):
    text = strip_tags(content_no_src)
    out = []
    for pat, msg in GRAMMAR_SOFT:
        for mm in re.finditer(pat, text):
            a = max(0, mm.start() - 10)
            out.append(f"{msg} … '{text[a:mm.end()+8]}'")
    return out


# ── 소프트: 도입·요약의 저널·에세이·구어체 (학술 논문에 안 쓰는 틀) ──
INTRO_ESSAYISM = [
    (r"(?:질문|화두|물음)을\s*던[지진집져졌짐]",
     "'질문을 던지다' — 논문(무생물)을 의인화한 직역. '본 연구는 ~를 다룬다 / ~에서 출발한다 / ~를 묻는다'로"),
    (r"(결과|이유|근거|특징|차이|기여|함의|핵심|장점|단점|문제점|발견|기둥|축|것|점|목표|방법)[은는이가]?\s*(하나|둘|셋|넷|다섯|여섯|일곱)입니다",
     "구어 수량 서술('결과는 셋입니다') — '주요 결과는 다음과 같다. 첫째…'로 머리명사를 살려 열거"),
    (r"다른\s*길을\s*(?:가|간다|갑니다|갔)",
     "'다른 길을 가다' — 에세이 관용구. '다른 방법을 쓴다 / 다른 접근을 취한다'로"),
    (r"(?:하|내|아내|뽑아내|풀어내|만들어)?려는\s*시도(?:입니다|이다|로|였)",
     "'~하려는 시도' — 구어·과정 묘사. '~를 목표로 한다 / ~하는 데 목적이 있다'로"),
]


def check_intro_register(content_no_src):
    text = strip_tags(content_no_src)
    out = []
    for pat, msg in INTRO_ESSAYISM:
        for mm in re.finditer(pat, text):
            a = max(0, mm.start() - 10)
            out.append(f"{msg} … '{text[a:mm.end()+10]}'")
    return out


# ── 소프트: 주어-서술어 호응(고빈도 혼동만; 일반 호응은 사람 자문) ──
HOEUNG_HINT = [
    (r"(문제의식|동기|배경|취지|착안점?)[은는][^<。.]{0,70}(정량화|추정|분석|측정|규명|검토|환산|제시|평가|구축|설계)하(?:는|려는)\s*데\s*있",
     "주어-서술어 호응 의심 — '문제의식/동기/배경은 …하는 데 있다'는 *목표* 술어와 짝지어졌다. "
     "목표를 말하려면 주어를 '목표/목적'으로, 문제의식이면 술어를 '…가 (그동안) 밝혀지지/해결되지 않았다는 데 있다'(공백)로"),
    (r"(목적|목표|취지)[은는][^<。.]{0,60}(다는 데서 출발|에서 비롯|때문입니다)",
     "주어-서술어 호응 의심 — '목적/목표는 …에서 출발/비롯'은 동기 술어. 목표면 '…하는 데 있다'로"),
]


def check_hoeung(content_no_src):
    text = strip_tags(content_no_src)
    out = []
    for pat, msg in HOEUNG_HINT:
        for mm in re.finditer(pat, text):
            a = max(0, mm.start() - 6)
            out.append(f"{msg} … '{text[a:mm.end()+8]}'")
    return out


# ── 소프트: 제목 속 비유·수수께끼어 ────────────────────────────
TITLE_META = re.compile(r"기둥|심장|엔진|민낯|민얼굴|여정|항해|만나는\s*자리|밑거름|날개|등불|꽃피|빌려(?:준|주는)")


def check_title_metaphor(content: str):
    out = []
    heads = re.findall(r'<h3 class="sec"[^>]*>(.*?)</h3>', content, re.S)
    heads += re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.S)
    for h in heads:
        t = strip_tags(h)
        if TITLE_META.search(t):
            out.append(f"제목 비유·수수께끼 가능성(취향) — 내용 요약형으로: 「{t[:44]}」")
    return out


# ── 소프트: 수식 단위·약어 첫 등장 정의 ─────────────────────────
def check_math_units(content: str):
    out = []
    if "bp" in content and "0.01%p" not in content and "0.01%포인트" not in content:
        out.append("'bp'가 정의 없이 등장 — 첫 등장에 'bp(=0.01%p)' 한 번 정의(math-exposition 규칙 8)")
    if "1표준편차" in content and not re.search(r"1표준편차.{0,40}%p", strip_tags(content)):
        out.append("'1표준편차' 충격의 크기(%p)가 병기되지 않음 — 예: '1표준편차 충격(0.75%p)'")
    return out


def check_quote_commentary(content: str):
    """권고: 인용 박스(.src) 직후에 해설 문단(<p>)이 따라오는지. 인용은 해설의 닻이다."""
    out = []
    for m in re.finditer(r'</blockquote>', content):
        rest = content[m.end():m.end() + 240].lstrip()
        if not rest.startswith("<p"):
            out.append("인용 박스 뒤 해설 문단(<p>) 없음 — 인용문의 의미와 논증상 위치를 설명")
    return out


# ── 소프트: 배경 개념 박스 존재 — 규칙 9 약프록시 ─────────────
STAT_KW = re.compile(r"도구변수|내생성|2SLS|2단계\s*최소자승|1단계\s*F|약\(?弱?\)?도구"
                     r"|부트스트랩|공적분|단위근|정상성|누락변수|최우도|위험가격|GMM")


def check_premise_scaffold(content: str):
    """통계·수식 절(.eq 또는 통계 키워드)이 있는데 전제를 끌어올린 배경 개념 .note
    박스가 하나도 없으면 권고. 정규식은 '박스 유무'만 보는 거친 프록시이므로 소프트로
    둔다 — 전제 충분성 자체는 math-exposition.md 규칙 9 자문으로 사람이 마무리한다."""
    out = []
    text = strip_tags(content)
    has_math = ('class="eq"' in content) or bool(STAT_KW.search(text))
    has_box = ("배경 개념" in content) or ("기본 개념" in content) or ("통계 개념" in content)
    if has_math and not has_box:
        out.append("통계·수식 절이 있는데 배경 개념 박스가 없음 — 성립 전제"
                   "(내생성·식별·정상성 등)를 한 단계 뒤까지 풀었는지 점검(math-exposition 규칙 9)")
    return out


def lint(path: Path):
    html = path.read_text(encoding="utf-8", errors="replace")
    visible = visible_html(html)
    content = content_html(visible)
    no_src = strip_src(content)
    all_no_src = strip_src(visible)
    hard = {
        "번역체·AI 결함": check_aiche(all_no_src),
    }
    # 원전 인용 3층은 **논문 정독 노트**의 규칙이다(paper-study에서 함께 넘어온 검사).
    # 강의노트는 원문 인용 박스가 없는 것이 정상이므로, .src를 쓰는 노트에 한해서만 본다.
    # 이 검사를 납품 게이트에 넣자마자 강의노트가 이 규칙 하나로 막혔다 — 도구를 빌려 올 때는
    # 딸려 온 규칙이 이 스킬의 것인지 따로 확인한다.
    if 'class="src"' in content:
        hard["원전 인용 3층"] = check_quote_triad(content)
    soft = {
        "register 혼재(권고)": check_register_mix(no_src),
        "취향: 은유·감정부사·자기지시(권고)": check_taste(all_no_src),
        "서술형 소제목(권고)": check_seosulhyeong(content),
        "제목 비유(권고)": check_title_metaphor(content),
        "인용 해설(권고)": check_quote_commentary(content),
        "수식 주석(권고)": check_eq_annotation(content),
        "수식 단위·약어(권고)": check_math_units(content),
        "판본 상태(권고)": check_version_status(content),
        "정리 부사(권고)": check_filler(all_no_src),
        "빈 수식어(권고)": check_empty_modifier(all_no_src),
        "통계량 의인화(권고)": check_stat_anthropomorphism(all_no_src),
        "기본 어법(권고)": check_grammar_soft(all_no_src),
        "도입·요약 구어체(권고)": check_intro_register(all_no_src),
        "주어-서술어 호응(권고)": check_hoeung(all_no_src),
        "전제 박스(권고)": check_premise_scaffold(content),
    }
    n_hard = sum(len(v) for v in hard.values())
    print(f"\n=== {path.name} ===")
    for name, items in hard.items():
        mark = "OK" if not items else f"위반 {len(items)}"
        print(f"  [{mark}] {name}")
        for it in items[:12]:
            print(f"       - {it}")
        if len(items) > 12:
            print(f"       … 외 {len(items) - 12}건")
    for name, items in soft.items():
        if items:
            print(f"  [권고 {len(items)}] {name}")
            for it in items[:6]:
                print(f"       - {it}")
    return n_hard


def main(argv):
    if len(argv) < 2:
        print("사용: PYTHONUTF8=1 python check_content_style.py <note.html> [...]")
        return 2
    total = 0
    for p in argv[1:]:
        total += lint(Path(p))
    if total == 0:
        print(f"\n총 하드 위반 {total}건. 통과.")
        print("[주의] 하드 통과는 '명백한 결함이 없다'는 뜻일 뿐입니다. 자연스러운 한국어인지"
              "(AI 리듬·번역투·어색한 연어)는 정규식이 다 못 잡으니, 본문을 직접 정독해"
              " 판정하세요.\n  '린트 통과'를 '어투 검증 완료'로 보고하지 마세요.")
    else:
        print(f"\n총 하드 위반 {total}건. 위 항목을 고치세요.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
