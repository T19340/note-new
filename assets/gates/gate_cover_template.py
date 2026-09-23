# -*- coding: utf-8 -*-
"""문제 배치 게이트 — 풀 수 있게 만들어야 할 문제가 하나도 빠지지 않았는지 본다.

usage: python gate_cover.py [조립본.html]

강의의 목표가 "문제지와 기출의 모든 문제를 풀 수 있게 하는 것"이라면, 노트가 그 문제들을
빠짐없이 다뤘는지는 의견이 아니라 **확인할 수 있는 사실**이어야 한다. 그래서 문제 번호를
원자료에서 직접 세고, `map.json`의 배치와 맞대 본다. 기억으로 세면 반드시 빠진다.

쓰는 법. 아래 ①②를 이 노트의 자료에 맞게 고친다. 나머지는 그대로 둔다.
  ① SOURCES — 원자료 파일과 그 안에서 문제 번호를 뽑는 규칙
  ② 번호 표기 — map.json의 문제 이름과 ①이 뽑은 번호를 잇는 규칙

`map.json`의 꼴은 `assets/map.example.json` 참고. 단위마다 넷을 적는다 —
지식 / 단서 / 대표 예제 / 그 지식으로 풀리는 문제 전량(`content.md` §8).
"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
H = os.path.dirname(os.path.abspath(__file__))

fails = []
def ok(c, m):
    if not c:
        fails.append(m)


# ── ① 원자료에서 문제 번호를 직접 센다 ───────────────────────────
# 예시: 문제지가 "본문 1~7" + "Some additional problems 1~11"로 나뉜 경우.
# 자료마다 꼴이 다르므로 이 블록은 노트마다 고쳐 쓴다.
def numbers(path, split_on=None, after=None, pat=r'^(\d+)\.\s'):
    t = io.open(os.path.join(H, path), encoding='utf-8', errors='replace').read()
    if split_on:
        head, tail = t.split(split_on)
        t = tail if after is None else tail.split(after)[-1]
    return sorted({int(n) for n in re.findall(pat, t, re.M)})


SOURCES = {
    # 'PS7':    numbers('problems07.txt'),
    # 'PS7add': numbers('problems07.txt', split_on='Some additional problems'),
}

# ── ② map.json의 배치를 읽는다 ──────────────────────────────────
M = json.load(io.open(os.path.join(H, 'map.json'), encoding='utf-8'))
units = M['units']
placed = set()
for u in units:
    for q in u['문제']:
        placed.add(re.sub(r'\(.*?\)', '', q).strip())   # 'PS7-3(a)' → 'PS7-3'

print(f'단위 {len(units)}개 · 배치된 문제 {len(placed)}개')
for u in units:
    for key in ('지식', '단서', '대표 예제', '문제'):
        ok(u.get(key), f'{u["id"]}에 "{key}"가 없습니다')
    ok(u.get('대표 예제') in u.get('문제', []) or not u.get('문제'),
       f'{u["id"]}의 대표 예제가 그 단위의 문제 목록에 없습니다')

# ── ③ 빠진 문제를 찾는다 ────────────────────────────────────────
for src, nums in SOURCES.items():
    missing = [f'{src}-{n}' for n in nums if f'{src}-{n}' not in placed]
    print(f'  {src}: 원자료 {len(nums)}문 · 미배치 {len(missing)}문 {missing}')
    ok(not missing, f'{src}에 어느 단위에도 들어가지 않은 문제: {missing}')

# ── ④ 배치한 문제가 실제로 본문에 실렸는지 ──────────────────────
if len(sys.argv) > 1:
    html = io.open(sys.argv[1], encoding='utf-8', errors='replace').read()
    text = re.sub(r'<[^>]+>', ' ', html)
    for u in units:
        for q in u['문제']:
            m = re.match(r'([A-Za-z]+)\D*(\d+)', q)
            if m and not re.search(m.group(2) + r'\s*번', text):
                fails.append(f'{u["id"]}에 배치한 {q}이 본문에 보이지 않습니다')

print('\nFAILS:', len(fails))
for f in fails:
    print('  ✗', f)
sys.exit(1 if fails else 0)
