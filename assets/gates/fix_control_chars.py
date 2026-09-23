# -*- coding: utf-8 -*-
"""셸 헤어독이 백슬래시를 먹어 남은 제어문자를 되돌린다.

usage: python fix_control_chars.py <파일…>

무엇을 고치나. bash 헤어독으로 조각이나 스크립트를 쓰면 `\\b` `\\f` `\\v` `\\a`의 백슬래시가
먹히고 제어문자 한 글자만 남는다. 화면에서는 보이지 않고, 파일은 멀쩡해 보이며, 오류도
나지 않는다. 그래서 **조용히 죽는다.** 이 스킬에서 실제로 세 번 났다.

  1. `korean_scan.py`의 정규식 `\\b`가 0x08이 되어 부제 검사가 어떤 부제와도 매치하지
     않았다. 출력은 "없음"이라 두 번의 작업에서 통과로 보고됐다.
  2. 같은 파일에서 또 났다. 첫 복구가 `\\b`만 고쳤기 때문이다.
  3. 본문 수식 `\\frac`이 0x0C가 되어 `EX=12\\cdot\x0crac{5}{20}=3`이 됐다. 렌더 게이트의
     mjx 오류 수로만 드러났고, 어느 수식인지는 DOM을 뒤져야 알 수 있었다.

`\\t`와 `\\n`은 파일에 정상적으로 들어가므로 손대지 않는다. 나머지 넷은 본문·코드에 나올
일이 없다. **헤어독으로 파일을 고친 뒤에는 이것을 돌린다.** `texscan.py`가 수식 안의 것을
잡아 주지만, 정규식이나 JS 문자열에 박힌 것은 여기서만 잡힌다.
"""
import io, sys

MAP = {b'\x07': b'\\a', b'\x08': b'\\b', b'\x0b': b'\\v', b'\x0c': b'\\f'}


def repair(path):
    b = io.open(path, 'rb').read()
    hits = {k.decode('latin1').encode('unicode_escape').decode(): b.count(k)
            for k in MAP if b.count(k)}
    if hits:
        for k, v in MAP.items():
            b = b.replace(k, v)
        io.open(path, 'wb').write(b)
    return hits


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    n = 0
    for p in sys.argv[1:]:
        h = repair(p)
        if h:
            n += sum(h.values())
            print(f'  {p} — 되돌림 {h}')
    print(f'제어문자 {n}개를 되돌렸습니다.' if n else '제어문자 없음.')
