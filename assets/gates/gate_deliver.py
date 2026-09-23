# -*- coding: utf-8 -*-
"""납품 게이트 — 이것을 통과하지 못하면 노트를 넘기지 않는다.

usage: python gate_deliver.py <조립된.html> [--src <소스폴더>]

왜 이 파일이 있나. 게이트들이 저마다 종료코드를 내는 동안 **사냥 패스만 산출물이 없어서**
납품 판단에서 빠졌다. 돌려도 파일이 안 생기고 안 돌려도 아무것도 실패하지 않으니, 체크리스트
상으로는 존재하지 않는 단계였다. 그래서 사냥 패스에 흔적을 강제하고, 그 흔적이 **지금 조립한
파일과 짝이 맞는지**까지 본다. 본문을 고치면 기록이 낡아 다시 돌려야 한다.

검사하는 것
  1. 구조 게이트 통과              gate_struct.py
  2. 문체 HARD 0 + 판정 전량 기록  korean_scan.py --triage (문장의 수준도 이 층에 있다)
  3. 사냥 패스 기록 hunt.md 존재   유형 ②③④에 각각 적힌 내용이 있을 것
  4. 그 기록이 현재 빌드의 것      hunt.md의 build 해시 == 지금 파일의 해시
"""
import hashlib, io, os, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
# 정규식으로 표현할 수 없어 읽어야만 드러나는 유형들. 번호는 `hunt-pass.md`의 유형 번호다.
HUNT_TYPES = [('②', '지워도 되는 문장'), ('③', '글쓴이만 아는 은어'),
              ('④', '쓸데없이 쪼갠 문장'), ('⑫', '문장의 수준')]

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
"""


def sha(path):
    return hashlib.sha256(io.open(path, 'rb').read()).hexdigest()[:16]


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

    print('── 4~5. 사냥 패스 기록')
    hp = os.path.join(src, 'hunt.md')
    cur = sha(note)
    if not os.path.exists(hp):
        io.open(hp, 'w', encoding='utf-8').write(TEMPLATE.format(h=cur, f=os.path.basename(note)))
        fails.append(f'사냥 패스를 돌리지 않았습니다. {hp}를 만들어 두었으니 본문을 통독하고 채우십시오')
    else:
        t = io.open(hp, encoding='utf-8').read()
        m = re.search(r'^build:\s*(\w+)', t, re.M)
        if not m or m.group(1) != cur:
            fails.append(f'사냥 패스 기록이 낡았습니다. 본문이 바뀌었으니 다시 통독하고 build를 {cur}로 고치십시오')
        else:
            print(f'   build {cur} 일치')
        for mark, name in HUNT_TYPES:
            sec = re.search(r'##\s*' + mark + r'[^\n]*\n(.*?)(?=\n##|\Z)', t, re.S)
            body = (sec.group(1).strip() if sec else '')
            if len(body) < 15:
                fails.append(f'사냥 패스 유형 {mark} {name}: 적힌 내용이 없습니다')
            else:
                print(f'   {mark} {name} — {len(body)}자')

    print('\nFAILS:', len(fails))
    for f in fails: print('  ✗', f)
    if not fails:
        print('\n납품해도 됩니다.')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
