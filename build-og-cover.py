# -*- coding: utf-8 -*-
"""1200x630 link-preview card. This is what WhatsApp, iMessage and X render
when someone pastes attack.urbanpadel.om — until now they rendered nothing,
because the page carried no og: tags at all."""
import base64
SC='/tmp/claude-0/-home-user-May-madness/0e44f0ad-a683-5f0d-9de6-9459ae328963/scratchpad'
b64f=lambda f: base64.b64encode(open(f'{SC}/{f}','rb').read()).decode()
anton=b64f('anton.woff2'); mono=b64f('jbmono700.woff2'); arch8=b64f('archivo800.woff2')
word=b64f('aa-wordmark-clean.png'); emblem=b64f('aa-emblem.png')
RED,ICE,CHALK,STEEL,COURT='#FF2E43','#3DE1FF','#F4F6FA','#8B95A7','#0A0C12'
HTML=f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:'Anton';src:url(data:font/woff2;base64,{anton}) format('woff2');font-display:block}}
@font-face{{font-family:'Mono';font-weight:700;src:url(data:font/woff2;base64,{mono}) format('woff2')}}
@font-face{{font-family:'Archivo';font-weight:800;src:url(data:font/woff2;base64,{arch8}) format('woff2')}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1200px;height:630px;overflow:hidden;position:relative;color:{CHALK};
 font-family:Archivo,sans-serif;background:
 radial-gradient(ellipse 80% 62% at 26% 6%, rgba(255,46,67,.30), transparent 62%),
 radial-gradient(ellipse 54% 46% at 92% 88%, rgba(61,225,255,.13), transparent 64%),
 linear-gradient(155deg,#08090D 0%,{COURT} 55%,#06070B 100%)}}
.grid{{position:absolute;inset:0;opacity:.5;background-image:
 linear-gradient(rgba(255,46,67,.055) 1px,transparent 1px),
 linear-gradient(90deg,rgba(255,46,67,.055) 1px,transparent 1px);background-size:46px 46px;
 -webkit-mask-image:radial-gradient(110% 90% at 30% 20%,#000,transparent 88%)}}
.scan{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.16) 0 1px,transparent 1px 3px)}}
.tk{{position:absolute;width:56px;height:56px}}
.tl{{top:34px;left:34px;border-top:5px solid {ICE};border-left:5px solid {ICE}}}
.br{{bottom:34px;right:34px;border-bottom:5px solid {RED};border-right:5px solid {RED}}}
.z{{position:relative;z-index:3;height:100%;display:flex;align-items:center;
 justify-content:space-between;padding:70px 78px}}
.l{{max-width:700px}}
.kick{{display:inline-flex;align-items:center;gap:11px;font-weight:800;font-size:15px;
 letter-spacing:.32em;color:{STEEL};text-transform:uppercase}}
.kick i{{width:4px;height:15px;background:{RED};box-shadow:0 0 8px {RED};display:block}}
.word{{width:520px;margin:22px 0 24px;filter:drop-shadow(0 0 30px rgba(255,46,67,.45))}}
.tag{{font-family:Anton;font-size:40px;letter-spacing:.03em;line-height:1;
 text-shadow:-2px 0 {RED},2px 0 {ICE}}}
.tag b{{color:{RED};font-weight:400}}
.meta{{margin-top:22px;font-family:Mono;font-weight:700;font-size:17px;letter-spacing:.13em;
 color:{CHALK};line-height:1.7}}
.meta span{{color:{ICE}}}
.r{{display:flex;flex-direction:column;align-items:center;gap:22px}}
.r img{{width:150px;filter:drop-shadow(0 0 22px rgba(255,46,67,.55))}}
.pool{{text-align:center;padding:18px 26px 15px;background:rgba(16,20,32,.94);
 background-image:linear-gradient({ICE},{ICE}),linear-gradient({ICE},{ICE}),
  linear-gradient({RED},{RED}),linear-gradient({RED},{RED});
 background-size:24px 3px,3px 24px,24px 3px,3px 24px;
 background-position:0 0,0 0,100% 100%,100% 100%;background-repeat:no-repeat;
 box-shadow:0 0 50px rgba(255,46,67,.22)}}
.pool b{{display:block;font-family:Anton;font-size:74px;line-height:.85;color:{RED};
 text-shadow:0 0 38px rgba(255,46,67,.8)}}
.pool span{{display:block;margin-top:9px;font-family:Mono;font-weight:700;font-size:13px;
 letter-spacing:.2em;color:{STEEL}}}
</style>
<div class="grid"></div><div class="tk tl"></div><div class="tk br"></div><div class="scan"></div>
<div class="z">
  <div class="l">
    <span class="kick"><i></i>Urban Playground &middot; Vol.6</span>
    <img class="word" src="data:image/png;base64,{word}" alt="August Attack">
    <div class="tag">SERVE FIRST. <b>STRIKE HARD.</b></div>
    <div class="meta">MON &amp; WED &middot; <span>5:30 PM</span> &middot; ALL AUGUST<br>
      LIVE TABLE &middot; <span>ATTACK.URBANPADEL.OM</span></div>
  </div>
  <div class="r">
    <img src="data:image/png;base64,{emblem}" alt="Urban Playground">
    <div class="pool"><b>402</b><span>OMR POOL</span></div>
  </div>
</div>"""
open(f'{SC}/og-cover.html','w').write(HTML); print('built')
