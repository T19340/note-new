<script>
setTimeout(function(){
  var L=[],E=window.__IE||[];
  function t(id){var e=document.getElementById(id);return e?e.textContent.replace(/\s+/g,' ').slice(0,260):'MISSING '+id;}
  function c(id){var e=document.getElementById(id);if(e)e.click();else E.push('noel '+id);}
  try{
  c('f1-next');c('f1-next');c('f1-next');c('f1-next');c('f1-next'); L.push('f1 k5 => '+t('r-f1'));
  c('f1-all'); L.push('f1 all => '+t('r-f1')); L.push('f1 rows '+document.querySelectorAll('#t-f1 tbody tr').length);
  var q=document.querySelectorAll('#q-f2 .qcard'); q[9].click(); document.querySelector('#q-f2 ~ .ctrls button[data-a="Dr"]').click(); L.push('f2 => '+t('fb-f2'));
  // f3: T10 wrong then T13 right
  var g=document.querySelectorAll('#q-f3 .qcard'); g[9].click();
  document.querySelector('#pk-dr button[data-k="dep"]').click(); document.querySelector('#pk-cr button[data-k="equip"]').click(); c('f3-check'); L.push('f3 T10 wrong => '+t('fb-f3'));
  document.querySelectorAll('#q-f3 .qcard')[12].click(); document.querySelector('#pk-dr button[data-k="ap"]').click(); document.querySelector('#pk-cr button[data-k="cash"]').click(); c('f3-check'); L.push('f3 T13 right => '+t('fb-f3'));
  document.querySelectorAll('#q-f3 .qcard')[14].click(); document.querySelector('#pk-dr button[data-k="re"]').click(); document.querySelector('#pk-cr button[data-k="cash"]').click(); c('f3-check'); L.push('f3 T15 via RE => '+t('fb-f3').slice(0,60)); L.push('f3 score => '+t('r-f3'));
  c('f4-next');c('f4-next');c('f4-next'); L.push('f4 k3 => '+t('r-f4')); L.push('f4 now cells '+document.querySelectorAll('#tg-f4 .e.now').length+' dim '+document.querySelectorAll('#tg-f4 .tacc.dim').length);
  c('f4-all'); L.push('f4 all => '+t('r-f4'));
  var bal=[].map.call(document.querySelectorAll('#tg-f4 .tacc'),function(x){return x.querySelector('.tn').textContent+':'+x.querySelector('.bal').textContent.replace(/\s+/g,'|');}); L.push('f4 balances '+bal.join(' ; '));
  [].forEach.call(document.querySelectorAll('#pk-f5 button'),function(b){b.click(); L.push('f5 '+b.getAttribute('data-e')+' => '+t('r-f5').slice(0,120)+' || tot: '+document.querySelector('#t-f5 tr.tot').textContent.replace(/\s+/g,' '));});
  var h=document.querySelectorAll('#q-f6 .qcard'); h[5].click(); document.querySelector('#q-f6 ~ .ctrls button[data-a="liab"]').click(); L.push('f6 => '+t('fb-f6'));
  ['A','B','C','D'].forEach(function(k){c('f7-'+k); L.push('f7 '+k+' Dec => '+t('r-f7'));});
  var s=document.getElementById('f7-m'); s.value=5; s.dispatchEvent(new Event('input')); L.push('f7 D Feb => '+t('r-f7'));
  c('f7-A'); L.push('f7 A Feb => '+t('r-f7'));
  var p=document.querySelectorAll('#pk-f8 button'); p[1].click(); L.push('f8 b before => '+t('r-f8')); c('f8-show'); L.push('f8 b after => '+t('r-f8'));
  p[4].click(); c('f8-show'); L.push('f8 e => '+t('r-f8'));
  }catch(err){E.push('TEST '+err.message);}
  var d=document.createElement('pre');d.id='__it';d.textContent='ITEST_ERRS '+JSON.stringify(E)+'\n'+L.join('\n');document.body.appendChild(d);
},7000);
</script>
