# 이 방법론의 출처

note-new는 새로 발명한 것이 아니라, 흩어져 있던 세 갈래를 한 폴더로 모은 것이다. 나중에 원리를
더 깊이 보거나 원본을 고쳐야 할 때 여기를 본다. (2026-09-20 정리)

## 1. 시각 셸과 집필 원리 — `blueprint-study-note`

`~/.claude/skills/blueprint-study-note/`

- `assets/reference.html` — 정본 셸. 이 스킬의 `assets/shell/head_css.html`은 그 CSS가
  MAT133 노트를 거쳐 온 사본이다(디자인 토큰, 마스트헤드·ISO 타이틀 블록, 두 플로팅 패널,
  수식 클릭-복사, 도표·표·코드 셀·접이식 컴포넌트).
- `references/floating-panels.md` — 우측 두 패널의 정밀 사양. 카드가 절과 묶이는 방식, 좁은
  폭에서 수식을 줄바꿈하는 법, scroll-spy 코드. 패널을 손볼 때 반드시 본다.
- `references/pedagogy.md` — 깊이를 낮추지 않고 발판을 까는 열한 가지 기법, 시각화 삽입 판단
  기준, 박스 라벨링 안티패턴, 한국어 문체 규칙. `references/content.md`의 뿌리다.
- `references/practitioner.md` — 실무 활용 박스의 규약(핵심 수식 직후, 빨간 보더, 행위 수준의
  서너 항목), 의사결정 매트릭스와 정직한 평가 표.
- `references/document-and-style.md` — 컴포넌트 라이브러리, MathJax 설정, 전역 `svg{}` 함정.
- `references/workbook.md` — 실행 코드가 주인공인 주제에서 동반 노트북을 만드는 법(이 스킬은
  다루지 않는다).

## 2. 그림 철학과 도구 — `interactive-note`

`~/.claude/skills/interactive-note/`

- 원리: 실측주의, 그림마다 "묻는 것/볼 것", 발견이 먼저·수식은 확인, 색 계약, 정직성 박스,
  정의 연쇄, 착지, 조작은 질문이 있을 때만.
- `assets/vz.js` — 의존성 0의 캔버스 라이브러리. 이 스킬의 `assets/js/vz-core.html`이 그
  사본이다(MAT133 노트에서 축 라벨 수정본을 떼어 왔다).
- `assets/audit_prep.py`, `assets/texscan.py` — 런타임 감사와 수식 파손 검사. 사본이
  `assets/gates/`에 있다.
- `assets/style.css`, `assets/example.html` — 그림 골격의 원형(`.fig-h`, `.lead2`, `.ctrls`,
  `.readout`).

## 3. 렌더 검증 절차 — `headless-render-verify`

`~/.claude/skills/headless-render-verify/`

Windows 헤드리스 Chrome 절차를 굳힌 스킬. 본 파일 렌더와 fcard 강제 표시 사본 렌더를 한 묶음으로
하고, 앵커 점프 대신 음수 마진 사본으로 긴 문서의 뒷부분을 찍으라는 실측 교훈이 담겨 있다.
`assets/gates/render_check.py`가 이 절차에 런타임 감사와 readout NaN 검사, 조각 내기를 더해
한 스크립트로 합친 것이다.

## 4. 문체 도구

- `ko_tell_scan.py` — 이전 노트 작업에서 쓰던 도구에서 왔다. 번역투·AI
  상투구 후보를 정규식 39개로 뽑는다. 판정이 아니라 후보다.
- `check_content_style.py` — `~/.claude/skills/paper-study-lite/assets/`. 번역체·AI 결함을
  하드로, 취향을 소프트로 나눠 본다. `.src` 인용 관련 위반은 강의노트 양식에서는 해당 없음.

## 5. 사용자 지침(메모리)에서 온 규칙

- **과외 자료의 기본 양식** — 개념 강의노트는 blueprint 셸 + interactive 그림. MAT133에서 세 번
  퇴짜 끝에 정해진 기본값.
- **게이트 먼저, 사후 수리 말 것** — 검사 계획을 먼저 짜고 단계마다 통과시킨다.
- **자연스러운 한국어** — 번역투·AI 말투 배제, 린터 통과를 자연스러움으로 오해하지 않기, 은유·
  줄표 남발 금지.
- **설명은 풀어쓰기** — 용어만 던지지 말고 정의·직관·숫자 예시·용어 풀이를 함께.
- **실증 주장엔 근거** — 숫자 주장마다 출처와 계산법.
- **대형 파일은 나눠 쓰기** — 한 응답 출력 상한 때문.
- **스킬은 명시 요청 시에만 발동** — 그래서 이 스킬의 description도 "지목할 때만"으로 썼다.

## 6. 참조 구현

이 방법론은 회계 입문 강의노트 두 편을 실제로 만들면서 굳었다. 그 두 편에서 확인된 구성:

- **1편** — 21절·그림 15·연습문제 20. 과제 안내표와 워크북 모범 답안 층, 자료 오류를 밝히는
  박스, 실제 기업 수치를 쓰되 회사 정체를 가린 데이터 그림.
- **2편** — 15절·그림 8·연습문제 12. 같은 데이터를 네 가지 표기(효과 템플릿·분개·T계정·
  시산표)로 다시 적는 구성, 오류 시뮬레이터, 시차 시간선.

`assets/example/`이 그 구성을 절 두 개짜리로 줄인 최소 실물이다. 새 노트는 여기서 시작한다.
