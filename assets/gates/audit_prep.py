# -*- coding: utf-8 -*-
# usage: python audit_prep.py <src.html> <dst.html>
import io, sys
sys.stdout.reconfigure(encoding='utf-8')
src, dst = sys.argv[1], sys.argv[2]
s = io.open(src, encoding='utf-8').read()

hook = '<script>window.__ERRS=[];window.addEventListener("error",function(e){window.__ERRS.push(String(e.message)+" @"+String(e.filename).slice(-30)+":"+e.lineno);});</script>'
i = s.find('<head>')
if i < 0:
    i = s.find('<script')
    s = s[:i] + hook + s[i:]
else:
    s = s[:i+6] + hook + s[i+6:]

report = '''
<script>
setTimeout(function(){
  var out={errs:window.__ERRS||["NOHOOK"],blank:[],canv:0,mjx:0,toc:0,h3:0};
  var cs=document.querySelectorAll("canvas"); out.canv=cs.length;
  cs.forEach(function(cv){
    try{
      if(cv.width===0||cv.height===0){ out.blank.push((cv.id||"?")+":w0"); return; }
      var ctx=cv.getContext("2d"); if(!ctx){ return; }
      var d=ctx.getImageData(0,0,cv.width,cv.height).data; var n=0;
      for(var i=3;i<d.length;i+=997){ if(d[i]>0){ n=1; break; } }
      if(!n) out.blank.push(cv.id||"?");
    }catch(e){ out.blank.push((cv.id||"?")+":ex"); }
  });
  out.mjx=document.querySelectorAll("mjx-merror").length+document.querySelectorAll("[data-mjx-error]").length;
  var t=document.querySelector(".toc"); out.toc=t?t.querySelectorAll("a").length:0;
  out.h3=document.querySelectorAll("h3").length;
  var dv=document.createElement("div"); dv.id="__audit"; dv.textContent="AUDIT_REPORT "+JSON.stringify(out);
  document.body.appendChild(dv);
},6500);
</script>
'''
s = s + report
io.open(dst, 'w', encoding='utf-8').write(s)
print('prepared', dst)
