# -*- coding: utf-8 -*-
"""note-new · 수치 게이트 뼈대. 주제마다 새로 쓰는 유일한 게이트다.

왜 필요한가. 노트의 숫자는 세 곳에 흩어진다 — 데이터 파일, 본문·캡션의 인용, 연습문제의 답.
셋이 어긋나면 독자는 어느 것이 맞는지 알 수 없고, 계산을 따라오던 학생은 거기서 멈춘다.
그래서 "데이터가 스스로 모순이 없는가"와 "본문이 인용한 값이 실제 계산과 같은가"를 기계로 본다.

쓰는 법: 아래 세 자리를 주제에 맞게 채운다.
  ① 항등식      — 원자료가 지켜야 할 관계(합계, 이월, 정의). 자료를 잘못 옮겨 적었는지 잡는다.
  ② 파생값      — 본문이 인용하는 계산값. 사람이 계산기로 두드린 값을 본문에 적지 않게 한다.
  ③ 연습문제    — 답과 검산. 문제를 만들 때 답이 딱 떨어지는지 먼저 확인한다.
본문을 쓰기 전에 이 파일을 먼저 통과시키면, 나중에 "본문 숫자가 틀렸다"를 찾아다니지 않는다.

사용:  python gate_numbers.py [out.html]
       out.html을 주면 CLAIMS의 문자열이 본문에 실제로 있는지까지 본다.
"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

H = os.path.dirname(os.path.abspath(__file__))
D = json.load(io.open(os.path.join(H, 'data.json'), encoding='utf-8'))
fails = []

def chk(label, got, want):
    if got != want: fails.append(f'{label}: {got} != {want}')

def ok(cond, msg):
    if not cond: fails.append(msg)

def f0(x): return f'{x:,.0f}'
def p1(x): return f'{x * 100:.1f}%'

# ① 원자료의 항등식 ---------------------------------------------------------
# 예) 재무제표: 자산 = 부채 + 자본, 기초 + 증감 = 기말, 각 줄의 합계
# for y, b in D['bs'].items():
#     ok(b['liab'] + b['eq'] == b['assets'], f'{y} A=L+E')

# ② 본문이 인용하는 파생값 --------------------------------------------------
CLAIMS = {
    # '라벨': p1(계산식),      # 본문에 이 문자열 그대로 등장해야 한다
}

# ③ 연습문제 산수 -----------------------------------------------------------
# chk('P1', 840000 - 510000, 330000)

if __name__ == '__main__':
    for k, v in CLAIMS.items():
        print(f'  {k:28s} {v}')
    if len(sys.argv) > 1:
        txt = re.sub(r'<script[\s\S]*?</script>', ' ', io.open(sys.argv[1], encoding='utf-8').read())
        for k, v in CLAIMS.items():
            if v not in txt:
                fails.append(f'본문에 없음: {k} = {v}')
    print('FAILS:', len(fails))
    for f in fails: print('  ✗', f)
    sys.exit(1 if fails else 0)
