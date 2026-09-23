# -*- coding: utf-8 -*-
"""note-new · 조각 파일을 단일 HTML 노트로 조립한다.

한 응답에 큰 파일을 통째로 쓰면 출력 상한에 걸려 작업이 통째로 날아가므로, 본문은 절 단위
조각(p0.html, p1.html …)으로 쓰고 이 스크립트로 합친다. 수정도 조각을 고쳐 다시 조립한다.

사용:  python assemble.py [note.json]        # 기본값: 같은 폴더의 note.json
note.json 예시는 note.example.json 참고.
"""
import re
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

H = os.path.dirname(os.path.abspath(__file__))
cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, 'note.json')
CFG = json.load(io.open(cfg_path, encoding='utf-8'))
ROOT = os.path.dirname(os.path.abspath(cfg_path))
SKILL = CFG.get('skill_assets') or H          # 셸·엔진이 있는 note-new/assets 경로

def rd(*p):
    return io.open(os.path.join(*p), encoding='utf-8').read()

def asset(name):
    return rd(SKILL, name)

parts = ''.join(rd(ROOT, p) for p in CFG['parts'])
data = json.dumps(json.load(io.open(os.path.join(ROOT, CFG['data']), encoding='utf-8')), ensure_ascii=False) if CFG.get('data') else None

out = [
    asset(os.path.join('shell', 'head_css.html')),          # <!DOCTYPE>~<style> 본문 (blueprint 셸)
    '\n', asset(os.path.join('shell', 'components.css')),   # 본문 컴포넌트 CSS
    '\n', rd(ROOT, CFG['head_extra']),                      # 노트별 CSS + </style></head><body> + 마스트헤드
    '<div class="with-layer-panel">\n<div class="content">\n',
    parts,
    rd(ROOT, CFG['panel']),                                 # </div> + 패널 레일 + 참고문헌 + 푸터 + </div>
    asset(os.path.join('shell', 'eq-copy-and-mathjax-config.html')),
    asset(os.path.join('shell', 'mathjax-tex-svg-inline.html')),
    '\n', asset(os.path.join('js', 'vz-core.html')),
]
if data:
    out.append('<script type="application/json" id="note-data">' + data + '</script>\n')
for f in [os.path.join(SKILL, 'js', 'common.js')] + [os.path.join(ROOT, f) for f in CFG.get('figures', [])]:
    out.append('<script>\n' + io.open(f, encoding='utf-8').read() + '\n</script>\n')
out.append(rd(ROOT, CFG['spy']))                            # scroll-spy + </body></html>

html = ''.join(out)

# 브라우저 탭·북마크에 뜨는 이름. 셸에 박힌 채로 두면 다른 노트의 제목을 그대로 물려받는다.
# 실제로 확률론 노트가 회계 노트의 제목을 달고 납품됐고, 검사기가 <title>을 보지 않아
# 아무도 몰랐다. note.json의 title, 없으면 마스트헤드의 <h1>에서 가져온다.
title = CFG.get('title')
if not title:
    m = re.search(r'(?is)<h1[^>]*>(.*?)</h1>', html)
    title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else ''
if title:
    html = re.sub(r'(?is)<title>.*?</title>', '<title>' + title + '</title>', html, count=1)

dst = os.path.join(ROOT, CFG.get('out', 'out.html'))
io.open(dst, 'w', encoding='utf-8').write(html)
print('written', dst, len(html), 'chars ·', title or '(제목 없음)')
