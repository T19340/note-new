<script>
(function(){
  var links={};document.querySelectorAll('.nav-panel a').forEach(function(x){links[x.getAttribute('href').slice(1)]=x;});
  var fcards={};document.querySelectorAll('.fcard').forEach(function(c){fcards[c.getAttribute('data-sec')]=c;});
  var fpHead=document.getElementById('fpHead');
  var secName={s11:'§1.1 재고의 이월',s12:'§1.2 판매 금액'};
  var cur=null;
  function activate(id){if(!links[id]||cur===id)return;if(cur&&links[cur])links[cur].classList.remove('active');
    links[id].classList.add('active');cur=id;for(var k in fcards){fcards[k].classList.toggle('fc-on',k===id);}
    if(fpHead)fpHead.textContent='— '+(secName[id]||'참조')+' —';}
  if(fcards.s11)fcards.s11.classList.add('fc-on');
  var targets=['s11','s12'].map(function(id){return document.getElementById(id);}).filter(Boolean);
  function spy(){var line=window.innerHeight*0.2,best=null;targets.forEach(function(t){if(t.getBoundingClientRect().top<line)best=t.id;});if(best)activate(best);}
  window.addEventListener('scroll',spy,{passive:true});window.addEventListener('resize',spy,{passive:true});window.addEventListener('load',spy);
  if(window.MathJax&&MathJax.startup&&MathJax.startup.promise){MathJax.startup.promise.then(spy);} spy();
})();
</script>
</body>
</html>
