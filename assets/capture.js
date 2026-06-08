(function(){
  var BTN_ID='tg-capture-btn', POP_ID='tg-capture-popup', shown=false;
  var btn=document.createElement('div');
  btn.id=BTN_ID;
  btn.innerHTML='💬&ensp;Chat on Telegram';
  Object.assign(btn.style,{position:'fixed',bottom:'24px',right:'24px',zIndex:'9998',padding:'14px 22px',background:'var(--surface)',color:'var(--text)',border:'1px solid var(--border)',borderRadius:'999px',fontFamily:"'Inter',sans-serif",fontSize:'14px',fontWeight:'600',cursor:'pointer',boxShadow:'0 4px 24px rgba(0,0,0,0.10)',display:'flex',alignItems:'center',transition:'transform .2s,box-shadow .2s',letterSpacing:'-0.01em'});
  btn.onmouseenter=function(){btn.style.transform='translateY(-2px)';btn.style.boxShadow='0 8px 32px rgba(0,0,0,0.14)';};
  btn.onmouseleave=function(){btn.style.transform='';btn.style.boxShadow='0 4px 24px rgba(0,0,0,0.10)';};
  btn.onclick=function(){window.open('https://t.me/Retpipebot?start=capture|site|visitor','_blank');};
  document.body.appendChild(btn);
  var timer=setTimeout(function(){
    if(shown)return;shown=true;
    var ovl=document.createElement('div');
    ovl.id=POP_ID;
    Object.assign(ovl.style,{position:'fixed',inset:0,background:'rgba(0,0,0,0.35)',zIndex:'9999',display:'flex',alignItems:'flex-end',justifyContent:'center',padding:'24px',opacity:0,transition:'opacity .3s'});
    ovl.innerHTML='<div style="background:var(--surface);border-radius:20px;padding:28px 24px;max-width:420px;width:100%;box-shadow:0 12px 48px rgba(0,0,0,0.18);position:relative"><button id="tg-popup-close" style="position:absolute;top:12px;right:16px;background:none;border:none;font-size:20px;cursor:pointer;color:var(--muted);line-height:1">&times;</button><p style="font-size:16px;font-weight:600;color:var(--text);margin-bottom:6px">Got questions?</p><p style="font-size:14px;color:var(--muted);margin-bottom:20px;line-height:1.6">Chat with Toby on Telegram — quick, personal, no pressure.</p><a href="https://t.me/Retpipebot?start=capture|site|visitor" target="_blank" rel="noopener" id="tg-popup-cta" style="display:block;text-align:center;padding:14px 24px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;transition:background .2s">Chat with Toby on Telegram →</a></div>';
    document.body.appendChild(ovl);
    requestAnimationFrame(function(){ovl.style.opacity='1';});
    document.getElementById('tg-popup-close').onclick=function(){ovl.style.opacity='0';setTimeout(function(){ovl.remove();},300);};
    ovl.onclick=function(e){if(e.target===ovl){document.getElementById('tg-popup-close').click();}};
    document.getElementById('tg-popup-cta').onmouseenter=function(){this.style.background='var(--surface2)';};
    document.getElementById('tg-popup-cta').onmouseleave=function(){this.style.background='var(--surface)';};
  },15000);
})();
