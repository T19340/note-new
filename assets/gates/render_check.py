# -*- coding: utf-8 -*-
"""note-new · 헤드리스 Chrome 렌더 검증 (Windows).

한 번의 렌더로는 검증이 끝나지 않는다는 것이 이 스크립트의 존재 이유다.
  ① 런타임 감사   — JS 오류, 빈 캔버스, MathJax 오류, readout의 NaN을 DOM에서 직접 읽는다.
                    스크린샷만 보면 "그림이 그려졌다"까지만 알 수 있고 값이 NaN인 것은 못 본다.
  ② 전체 스크린샷 — 문서가 창보다 길면 아래가 잘리므로, 음수 마진 사본으로 구간을 나눠 찍는다.
                    (앵커 #id 점프는 헤드리스에서 빈 화면이 찍히는 일이 있어 쓰지 않는다.)
  ③ fcard 강제 표시 — 우측 패널은 현재 절의 카드만 보이므로, 전부 펼친 사본을 따로 찍어야
                    좁은 패널에서 수식이 넘치는 카드를 찾을 수 있다.
임시 사본은 끝나고 지운다. Chrome stderr의 GPU·DEPRECATED_ENDPOINT 경고는 무시해도 된다.

사용:  python render_check.py out.html [--shots shots] [--slice 2700] [--audit-only]
"""
import io, os, re, subprocess, sys, tempfile
sys.stdout.reconfigure(encoding='utf-8')

SRC = os.path.abspath(sys.argv[1])
OUT = os.path.dirname(SRC)
SHOTS = os.path.join(OUT, 'shots')
SLICE = 2700
AUDIT_ONLY = '--audit-only' in sys.argv
if '--shots' in sys.argv: SHOTS = os.path.abspath(sys.argv[sys.argv.index('--shots') + 1])
if '--slice' in sys.argv: SLICE = int(sys.argv[sys.argv.index('--slice') + 1])

CHROME = next((p for p in [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'] if os.path.exists(p)), None)
if not CHROME:
    sys.exit('chrome.exe를 찾지 못했습니다. 경로를 직접 지정하세요.')

def url(path): return 'file:///' + os.path.abspath(path).replace('\\', '/')

def run(args, timeout=180):
    return subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars'] + args,
                          capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=timeout).stdout

HOOK = ('<script>window.__ERRS=[];window.addEventListener("error",function(e){'
        'window.__ERRS.push(String(e.message)+" @"+e.lineno);});</script>')
REPORT = '''<script>setTimeout(function(){
 var o={errs:window.__ERRS||["NOHOOK"],blank:[],canv:0,mjx:0,nan:[],empty:[],h:document.documentElement.scrollHeight,sec:{}};
 document.querySelectorAll("canvas").forEach(function(cv){o.canv++;try{
   if(!cv.width||!cv.height){o.blank.push((cv.id||"?")+":size0");return;}
   var d=cv.getContext("2d").getImageData(0,0,cv.width,cv.height).data,n=0;
   for(var i=3;i<d.length;i+=997){if(d[i]>0){n=1;break;}}
   if(!n)o.blank.push(cv.id||"?");}catch(e){o.blank.push((cv.id||"?")+":ex");}});
 o.mjx=document.querySelectorAll("mjx-merror,[data-mjx-error]").length;
 document.querySelectorAll(".readout").forEach(function(r){var t=r.textContent||"";
   if(/NaN|undefined|Infinity/.test(t))o.nan.push(r.id||"?"); if(!t.trim())o.empty.push(r.id||"?");});
 document.querySelectorAll("h3.sec,.part").forEach(function(h){o.sec[h.id||"part"]=Math.round(h.getBoundingClientRect().top+window.scrollY);});
 var d=document.createElement("div");d.id="__audit";d.textContent="AUDIT "+JSON.stringify(o);document.body.appendChild(d);},7000);</script>'''

src = io.open(SRC, encoding='utf-8').read()
tmp = []
def temp(name, content):
    p = os.path.join(tempfile.gettempdir(), name)
    io.open(p, 'w', encoding='utf-8').write(content); tmp.append(p); return p

# ① 런타임 감사
audit = temp('_nn_audit.html', src.replace('<head>', '<head>' + HOOK, 1).replace('</body>', REPORT + '</body>'))
dom = run(['--virtual-time-budget=16000', '--window-size=1400,2000', '--dump-dom', url(audit)])
m = re.search(r'AUDIT (\{.*?\})</div>', dom, re.S)
print(m.group(1) if m else '감사 보고를 읽지 못했습니다 (virtual-time-budget을 늘려 보세요)')
height = int(re.search(r'"h":(\d+)', m.group(1)).group(1)) if m else 0

if not AUDIT_ONLY:
    os.makedirs(SHOTS, exist_ok=True)
    # ② 전체 스크린샷 (길면 음수 마진 사본으로 나눠 찍기)
    WIN = 24000
    for i, off in enumerate(range(0, max(height, 1), WIN)):
        page = src if off == 0 else src.replace('</style>', f'.wrap{{margin-top:-{off}px !important;}}</style>', 1)
        p = temp(f'_nn_shot{i}.html', page)
        png = os.path.join(SHOTS, f'full{i}.png')
        run(['--virtual-time-budget=20000', f'--window-size=1400,{min(WIN, height - off + 400)}',
             f'--screenshot={png}', url(p)], timeout=300)
        print('screenshot', png)
    # ③ fcard 전부 펼친 사본 — 패널 폭에서 수식이 넘치는 카드 찾기
    cards = src.replace('</style>', '.fcard{display:block!important;border-bottom:3px solid #C53030;}'
                        '.panel-rail{position:static!important;max-height:none!important;overflow:visible!important;}'
                        '.content{display:none;}.with-layer-panel{grid-template-columns:264px!important;}</style>', 1)
    p = temp('_nn_cards.html', cards)
    png = os.path.join(SHOTS, 'fcards.png')
    run(['--virtual-time-budget=15000', '--window-size=700,9000', f'--screenshot={png}', url(p)], timeout=300)
    print('screenshot', png)
    try:                                  # 눈으로 훑기 좋게 잘라 둔다
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        n = 0
        for i, f in enumerate(sorted(x for x in os.listdir(SHOTS) if x.startswith('full'))):
            im = Image.open(os.path.join(SHOTS, f))
            for y in range(0, im.height, SLICE):
                c = im.crop((150, y, min(1260, im.width), min(im.height, y + SLICE)))
                c.resize((c.width * 6 // 10, c.height * 6 // 10)).save(os.path.join(SHOTS, f's{n:02d}.png')); n += 1
        print('slices', n)
    except ImportError:
        print('PIL 없음 — full*.png를 직접 열어 보세요')

for p in tmp:
    try: os.remove(p)
    except OSError: pass
print('문서 높이', height, 'px · 조각은', SHOTS)
