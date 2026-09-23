# -*- coding: utf-8 -*-
"""납품 게이트 — 이것을 통과하지 못하면 노트를 넘기지 않는다.

usage: python gate_deliver.py <조립된.html> [--src <소스폴더>]

왜 이 파일이 있나. 게이트들이 저마다 종료코드를 내는 동안 **사냥 패스만 산출물이 없어서**
납품 판단에서 빠졌다. 돌려도 파일이 안 생기고 안 돌려도 아무것도 실패하지 않으니, 체크리스트
상으로는 존재하지 않는 단계였다. 그래서 사냥 패스에 흔적을 강제하고, 그 흔적이 **지금 조립한
파일과 짝이 맞는지**까지 본다. 본문을 고치면 기록이 낡아 다시 돌려야 한다.

검사하는 것 — 전부, 매번, 조립본 전체를 대상으로 돈다. 골라 돌리는 선택지는 없다.
  1. 구조                          gate_struct.py
  2. 문체 HARD 0 + 판정 전량 기록  korean_scan.py --triage
                                   (문장의 수준 · 개념어와 원어 병기도 이 층에 있다)
  3. 읽는 순서                     gate_order.py
  3b. 번역투·AI 말투               check_content_style.py
  3c. 수식 파손                    texscan.py
  3d. 수치                         소스 폴더의 gate_numbers.py (없으면 실패)
  4. 사냥 패스 기록 hunt.md 존재   유형 ②③④⑫⑬에 각각 적힌 내용이 있을 것
  5. 그 기록이 현재 빌드의 것      hunt.md의 build 해시 == 지금 파일의 해시
"""
import hashlib, io, os, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
# 정규식으로 표현할 수 없어 읽어야만 드러나는 유형들. 번호는 `hunt-pass.md`의 유형 번호다.
HUNT_TYPES = [('②', '지워도 되는 문장'), ('③', '글쓴이만 아는 은어'),
              ('④', '쓸데없이 쪼갠 문장'), ('⑫', '문장의 수준'),
              ('⑬', '개념어 자리에 들어온 일상어')]

TEMPLATE = """# 사냥 패스 기록

build: {h}
file: {f}

이 파일이 "본문을 처음부터 끝까지 읽었다"는 유일한 증거다. 린터가 잡지 못하는 세 유형은
읽어야만 드러나므로, 유형마다 무엇을 찾아 어떻게 고쳤는지 적는다. 찾은 것이 없으면 "없음"이
아니라 **어디를 어떻게 훑었는지**를 적는다. 본문을 고치면 위 해시가 달라져 기록이 낡고,
납품 게이트가 다시 돌리라고 말한다.

## ② 지워도 되는 문장

## ③ 글쓴이만 아는 은어

## ④ 쓸데없이 쪼갠 문장

## ⑫ 문장의 수준

뜻이 통하는 것은 최저 조건이지 합격선이 아니다. 노트에 실리는 **모든** 문단에 넷을 묻는다.
부제와 요지만이 아니라 절을 여는 문장, 캡션, 표 앞뒤, 해설, 패널 카드까지다.

  1. 이 문장이 하는 일이 무엇인가          — 답이 없으면 줄이지 말고 지운다
  2. 앞이 이미 말한 것을 되풀이하지 않는가  — 절 제목·앞 문장·방금 지나온 표
  3. 한 가지로만 읽히는가                  — 일부러 다르게 읽어 본다
  4. 문단이 제자리를 돌고 있지 않은가       — 같은 낱말이 두세 문장에 세 번

수준이 떨어지는 자리는 정해져 있다 — 내용을 다 쓴 뒤에 채우는 칸이다. 그 칸들만 모아
한 번 더 읽고, 문단의 첫 문장만 위에서 아래로 죽 읽어 본다. 이어 읽을 때는 흐름에 묻혀
지나가는 빈 문장이 첫 문장만 모아 놓으면 드러난다.

## ⑬ 개념어 자리에 들어온 일상어

어려운 용어를 피해 주려고 일상어로 바꾸면, 뜻이 넓어서 독자가 무엇을 가리키는지 고를 수
없다. 쉽게 써 준 것이 아니라 해독을 시킨 것이다. 셋을 본다.

  1. 개념이 있는 자리에 비유가 앉아 있지 않은가 — 얽히다·맞물리다·서로 영향을 주다
  2. 개념어의 원어가 처음 나오는 자리에 있는가 — 독립(independent)
  3. 일상어에도 있는 낱말을 정의 없이 쓰지 않았는가 — 독립·상관·기대·정규·유의·표본

한 노트가 같은 개념을 두 이름으로 부르고 있지 않은지 함께 본다. 실제로 부제는 '얽힘',
본문은 '독립이 아님'으로 부르고 있었고, 독자는 둘이 같은 것인 줄 알 길이 없었다.
"""


def sha(path):
    return hashlib.sha256(io.open(path, 'rb').read()).hexdigest()[:16]


def sentences(note):
    """노트에 실린 문장 전부. 문체 검사와 같은 추출기를 쓴다 — 두 벌이면 갈라진다."""
    sys.path.insert(0, HERE)
    import korean_scan as K
    src = io.open(note, encoding='utf-8', errors='replace').read()
    return [s for _, t in K.blocks_of(src) for s in K.split_sents(t)]


def new_sentences(note, snap):
    """지난 기록 이후 새로 쓰거나 고친 문장."""
    cur = sentences(note)
    if not os.path.exists(snap):
        return cur, cur
    old = set(io.open(snap, encoding='utf-8').read().split('\n'))
    return [s for s in cur if s not in old], cur


READ_HEAD = """# 통독 장부 — 새로 쓰거나 고친 문장을 한 줄씩 읽었다는 증거다.
#
# 각 줄의 [ ]를 채운다.
#   [읽음]          읽었고 고칠 것이 없다.
#   [고침]          고쳤다. 다시 돌리면 그 줄은 사라지고 새 문장이 붙는다.
#
# [ ]가 하나라도 남으면 납품 게이트는 통과하지 않는다.
#
# 왜 이 파일이 있나. 사냥 패스에 흔적을 요구하고(hunt.md), 본문이 바뀌면 그 흔적이 낡게
# 만들고, 새로 생긴 문장을 짚어 주기까지 했는데도 **읽지 않고 기록만 갱신하는 일**이 반복됐다.
# 기록을 요구하는 것과 읽기를 요구하는 것은 다르다. 이 세션에서 실제로 나를 멈춰 세운 장치는
# 판정 기록의 빈 칸 하나뿐이었으므로, 같은 방식을 문장 단위로 적용한다. 한 줄씩 채우는
# 동안에는 그 문장을 읽을 수밖에 없다.
"""


def read_ledger(path, added):
    """새 문장마다 '읽었다'를 받아 적게 한다. 비어 있으면 통과시키지 않는다."""
    old = {}
    if os.path.exists(path):
        for ln in io.open(path, encoding='utf-8'):
            m = re.match(r'\[([^\]]*)\]\s*(.*)$', ln.rstrip('\n'))
            if m:
                old[m.group(2)] = m.group(1).strip()
    lines, blank = [], 0
    for s in added:
        key = re.sub(r'\s+', ' ', s)[:200]
        v = old.get(key, '')
        if not v:
            blank += 1
        lines.append(f'[{v or " "}] {key}')
    io.open(path, 'w', encoding='utf-8').write(READ_HEAD + '\n' + '\n'.join(lines) + '\n')
    return blank


def run(script, args):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)] + args,
                       capture_output=True, env=dict(os.environ, PYTHONUTF8='1'))
    out = (r.stdout or b'').decode('utf-8', 'replace')
    return r.returncode, out


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    note = os.path.abspath(sys.argv[1])
    src = os.path.dirname(note)
    if '--src' in sys.argv:
        src = os.path.abspath(sys.argv[sys.argv.index('--src') + 1])
    fails = []

    print('── 1. 구조')
    terms = os.path.join(src, 'terms.txt')
    rc, out = run('gate_struct.py', [note] + ([terms] if os.path.exists(terms) else []))
    print('   ' + (out.strip().splitlines() or [''])[-1][:110])
    if rc: fails.append('구조 게이트 실패')

    print('── 2. 문체 (HARD 0 + 판정 전량 기록)')
    # 본문 조각만 보면 마스트헤드·패널·캡션이 검사에서 빠진다. 실제로 그 구멍 때문에
    # 부제의 깨진 문장("몇 명이 …할까"의 평균)이 린터도 사냥 패스도 거치지 않고 나갔다.
    # 그래서 조립본을 본다 — 거기에 노트에 실리는 모든 글이 들어 있다.
    rc, out = run('korean_scan.py', [note, '--triage', os.path.join(src, 'triage.txt')])
    tail = [l for l in out.strip().splitlines() if '판정 기록' in l or '요약' in l]
    for l in tail[-3:]: print('   ' + l.strip()[:110])
    if rc: fails.append('문체 게이트 실패 (HARD가 남았거나 판정 기록이 비어 있음)')

    print('── 3. 읽는 순서 (아직 주지 않은 것으로 설명하지 않았는가)')
    rc, out = run('gate_order.py', [note])
    for l in out.strip().splitlines()[:6]: print('   ' + l.strip()[:110])
    if rc: fails.append('앞선 언급이 있습니다 — 독자가 되돌아가야 하는 자리를 없애십시오')

    # 아래 셋은 오래 "돌리면 좋은 것"으로만 적혀 있었다. 압박이 오면 그런 단계는 빠지므로
    # 납품 게이트 안으로 옮긴다. 검사는 전부, 매번, 조립본 전체를 대상으로 돈다.
    print('── 3b. 번역투·AI 말투 (하드)')
    rc, out = run('check_content_style.py', [note])
    print('   ' + (out.strip().splitlines() or [''])[-1][:110])
    if rc: fails.append('번역체·AI 어투 하드 위반이 남아 있습니다')

    print('── 3c. 수식 파손')
    rc, out = run('texscan.py', [note])
    print('   ' + (out.strip().splitlines() or [''])[-1][:110])
    if '(이상 없음)' not in out: fails.append('수식이 조용히 깨진 자리가 있습니다')

    gn = os.path.join(src, 'gate_numbers.py')
    if os.path.exists(gn):
        print('── 3d. 수치')
        r = subprocess.run([sys.executable, gn, note], capture_output=True,
                           cwd=src, env=dict(os.environ, PYTHONUTF8='1'))
        o = (r.stdout or b'').decode('utf-8', 'replace')
        print('   ' + (o.strip().splitlines() or [''])[-1][:110])
        if r.returncode: fails.append('수치 게이트 실패')
    else:
        fails.append(f'수치 게이트가 없습니다 — {gn}를 만들어 데이터와 본문 인용값을 묶으십시오')

    print('── 4~5. 사냥 패스 기록')
    hp = os.path.join(src, 'hunt.md')
    snap = os.path.join(src, '.hunt_sentences.txt')
    cur = sha(note)
    fresh = False
    if not os.path.exists(hp):
        io.open(hp, 'w', encoding='utf-8').write(TEMPLATE.format(h=cur, f=os.path.basename(note)))
        fails.append(f'사냥 패스를 돌리지 않았습니다. {hp}를 만들어 두었으니 본문을 통독하고 채우십시오')
    else:
        t = io.open(hp, encoding='utf-8').read()
        m = re.search(r'^build:\s*(\w+)', t, re.M)
        if not m or m.group(1) != cur:
            fails.append(f'사냥 패스 기록이 낡았습니다. 본문이 바뀌었으니 다시 통독하고 build를 {cur}로 고치십시오')
        else:
            fresh = True
            print(f'   build {cur} 일치')

        checked = 0
        for mark, name in HUNT_TYPES:
            sec = re.search(r'##\s*' + mark + r'[^\n]*\n(.*?)(?=\n##|\Z)', t, re.S)
            body = (sec.group(1).strip() if sec else '')
            checked += 1
            if len(body) < 15:
                fails.append(f'사냥 패스 유형 {mark} {name}: 적힌 내용이 없습니다')
            else:
                print(f'   {mark} {name} — {len(body)}자')
        # 검사를 몇 개 돌았는지 세어 둔다. 이 루프가 조건절 안으로 빨려 들어가 통째로
        # 건너뛰어진 적이 있고, 그때도 출력은 "FAILS: 0"이었다.
        if checked != len(HUNT_TYPES):
            fails.append(f'사냥 패스 유형 검사가 {checked}/{len(HUNT_TYPES)}개만 돌았습니다')

    print('── 6. 통독 장부 (새로 쓴 문장을 한 줄씩 읽었는가)')
    added, allsents = new_sentences(note, snap)
    ledger = os.path.join(src, 'hunt_read.txt')
    blank = read_ledger(ledger, added)
    print(f'   새로 쓰거나 고친 문장 {len(added)}개 · 아직 읽지 않은 것 {blank}개')
    if blank:
        for s in added[:8]:
            print(f'     · {s[:100]}')
        if len(added) > 8:
            print(f'     … 외 {len(added) - 8}개 — {ledger}')
        fails.append(f'통독하지 않은 문장이 {blank}개 남았습니다. {ledger}의 [ ]를 하나씩 '
                     f'채우십시오 — 읽고 [읽음], 고쳤으면 [고침]')
    elif fresh:
        # 새 문장을 전부 읽었고 사냥 패스 기록도 이 빌드의 것이다. 기준점을 옮긴다.
        io.open(snap, 'w', encoding='utf-8').write('\n'.join(allsents))
        io.open(ledger, 'w', encoding='utf-8').write(READ_HEAD)

    print('\nFAILS:', len(fails))
    for f in fails: print('  ✗', f)
    if not fails:
        print('\n납품해도 됩니다.')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
