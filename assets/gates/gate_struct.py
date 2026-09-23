# -*- coding: utf-8 -*-
"""note-new · 구조 게이트.

사람이 눈으로 절대 못 잡는 종류만 본다 — 절 id와 목차·패널·scroll-spy의 불일치, 그림 번호의
구멍, 외부 의존(오프라인 요구 위반), id 충돌. 이 넷은 렌더해도 조용히 지나가고, 나중에 독자가
링크를 눌렀을 때에야 드러난다.

사용:  python gate_struct.py out.html [terms.txt]
       terms.txt: 본문에 반드시 등장해야 할 용어를 한 줄에 하나(주석은 #). 시험 대비 노트에서
       영어 용어 누락을 막는 용도. 없으면 이 검사는 건너뛴다.
종료코드 1 = 위반 있음.
"""
import io, re, sys
sys.stdout.reconfigure(encoding='utf-8')

src = io.open(sys.argv[1], encoding='utf-8').read()
terms = []
if len(sys.argv) > 2:
    terms = [l.strip() for l in io.open(sys.argv[2], encoding='utf-8') if l.strip() and not l.startswith('#')]

fails = []
def ok(cond, msg):
    if not cond: fails.append(msg)

body = re.sub(r'<script[\s\S]*?</script>', '', src)
text = re.sub(r'<[^>]+>', ' ', body)

ids = re.findall(r'\sid="([^"]+)"', body)
dup = sorted({x for x in ids if ids.count(x) > 1})
ok(not dup, f'id 중복: {dup}')

# <title>은 탭·북마크·검색결과에 뜨는 이름인데 본문 어디에도 보이지 않아 눈으로는 못 잡는다.
# 셸을 복사해 쓰는 방식이라 앞 노트의 제목이 그대로 따라오고, 실제로 확률론 노트가 회계
# 노트의 제목을 달고 납품됐다. 제목이 h1과 한 낱말도 겹치지 않으면 남의 제목일 가능성이 높다.
_t = re.search(r'(?is)<title>(.*?)</title>', src)
_h = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', src)
_tt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', _t.group(1))).strip() if _t else ''
ok(bool(_tt), '<title>이 비어 있습니다')
ok('제목을 정하십시오' not in _tt, f'<title>이 자리표시자 그대로입니다: 「{_tt}」')
if _tt and _h:
    _hw = set(re.findall(r'[가-힣]{2,}', re.sub(r'<[^>]+>', '', _h.group(1))))
    _tw = set(re.findall(r'[가-힣]{2,}', _tt))
    ok(not _hw or bool(_hw & _tw),
       f'<title>「{_tt}」이 h1과 한 낱말도 겹치지 않습니다 — 다른 노트의 제목이 남아 있는지 보십시오')

secs = re.findall(r'<h3 class="sec" id="([^"]+)"', body)
nav = re.findall(r'href="#([^"]+)"', re.search(r'<aside class="tool-panel nav-panel">([\s\S]*?)</aside>', body).group(1))
fcards = re.findall(r'<div class="fcard" data-sec="([^"]+)"', body)
spy = re.search(r"var targets=\[([^\]]*)\]", src)
spy = re.findall(r"'([^']+)'", spy.group(1)) if spy else []
names = re.search(r'var secName=\{([^}]*)\}', src)
names = re.findall(r"(\w+)\s*:\s*'", names.group(1)) if names else []
toc = re.search(r'<nav class="toc">([\s\S]*?)</nav>', body)
toc = re.findall(r'href="#([^"]+)"', toc.group(1)) if toc else secs

ok(nav == secs, f'패널 목차 != 섹션: {nav} vs {secs}')
ok(fcards == secs, f'fcard data-sec != 섹션: {fcards}')
ok(spy == secs, f'scroll-spy targets != 섹션: {spy}')
ok(names == secs, f'secName 키 != 섹션: {names}')
ok(toc == secs, f'상단 목차 != 섹션: {toc}')

nums = [int(x) for x in re.findall(r'class="figtag">그림 (\d+)', body)]
ok(nums == list(range(1, len(nums) + 1)), f'그림 번호가 연속이 아님: {nums}')
refs = {int(x) for x in re.findall(r'(?<!노트 )그림 (\d+)', text)}   # "다른 노트 그림 N" 참조는 제외
ok(not {r for r in refs if r > len(nums)}, f'없는 그림을 가리킴: {sorted(r for r in refs if r > len(nums))}')

ok(not re.search(r'<script[^>]+src=', src), '외부 <script src> — 오프라인에서 깨진다')
ok(not re.search(r'<link[^>]+>', src), '<link> 태그 — 폰트·CSS가 외부 의존이 된다')
ok(not re.search(r'<img[^>]+src="https?:', src), '원격 <img>')
ok('NaN' not in text and 'undefined' not in text, '본문에 NaN/undefined')

miss = [t for t in terms if t.lower() not in text.lower()]
ok(not miss, f'빠진 필수 용어: {miss}')

# 수식 클릭-복사 적용률. 본문에 \[ \] · \( \)를 직접 쓰면 MathJax가 렌더는 하므로 눈으로도
# 게이트로도 멀쩡해 보이지만, 클릭해도 LaTeX이 복사되지 않는다. 그래서 여기서 센다.
main = body.split('<div class="panel-rail"')[0]   # 패널 카드의 수식은 클릭 대상이 아니다
clickable = len(re.findall(r'data-tex=', main))
raw = len(re.findall(r'\\\[', main)) + len(re.findall(r'\\\(', main))
total = clickable + raw
rate = clickable / total if total else 1.0
ok(rate >= 0.9, f'수식 클릭-복사 적용률 {rate:.0%} '
                f'(복사 가능 {clickable} · 직접 쓴 수식 {raw}) — 본문 수식은 '
                f'<div class="eq" data-tex="…"></div> / <span class="eqi" data-tex="…"></span>로 쓴다')

# 해설 분량. 계산만 적은 해설은 답안지이지 해설이 아니다(references/content.md §6).
# 길다고 좋은 해설은 아니지만, **짧은 해설은 거의 언제나 답만 적은 것**이라 여기서 지목한다.
sol = []
for d in re.findall(r'(?is)<details\b[^>]*>(.*?)</details>', body):
    t = re.sub(r'(?is)<table\b.*?</table>', ' ', d)          # 표는 답이지 해설이 아니다
    t = re.sub(r'data-tex="[^"]*"', ' ', t)
    t = re.sub(r'(?s)\\\[.*?\\\]|\\\(.*?\\\)', ' ', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    sol.append(len(re.findall(r'[가-힣]', t)))
if sol:
    thin = [n for n in sol if n < 100]
    sol_msg = f'해설 {len(sol)}개 · 한글 산문 중앙값 {sorted(sol)[len(sol) // 2]}자'
    ok(len(thin) <= len(sol) // 4,
       f'{sol_msg} — 100자 미만이 {len(thin)}개({len(thin) * 100 // len(sol)}%). '
       f'계산만 적고 "무엇을 보고 이 방법을 골랐는지"가 빠졌을 수 있다. content.md §6의 다섯 층 확인')
else:
    sol_msg = '해설 0개'

print(f'섹션 {len(secs)} · 그림 {len(nums)} · id {len(ids)} · 수식 복사 {rate:.0%} · {sol_msg}')
print('FAILS:', len(fails))
for f in fails: print('  ✗', f)
sys.exit(1 if fails else 0)
