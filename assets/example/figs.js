(function(){
'use strict';
const {D, N, el} = RSM;
(function(){
  const cv = el('c-f1'); if (!cv) return;
  const c = D.cups;
  function draw(){
    RSM.waterfall(cv, [{lab:'기초', v:c.begin, type:'bal'},{lab:'매입', v:c.sold},{lab:'파손', v:-c.spilled},{lab:'기말', v:c.end, type:'bal'}]);
    VZ.rs('r-f1','<span class="k">식</span> ' + N(c.begin) + ' + ' + N(c.sold) + ' − ' + N(c.spilled) + ' = <b>' + N(c.end) + '</b>잔 · <span class="k">매출</span> ' + N(c.sold) + ' × ' + D.price + ' = ' + N(c.sold * D.price));
  }
  VZreg(draw);
})();
RSM.Quiz({grid:'q-f2', fb:'fb-f2', ro:'r-f2', btnSel:'#q-f2 ~ .ctrls button[data-a]', reset:'f2-reset',
  labels:{up:'늘림', down:'줄임'}, items:[
  {t:'원두 매입', a:'up', why:'재고가 들어옵니다.'},
  {t:'커피 판매', a:'down', why:'팔린 만큼 재고가 나갑니다.'},
  {t:'컵 파손', a:'down', why:'쓸 수 없게 되어 재고에서 빠집니다.'}
]});
})();
