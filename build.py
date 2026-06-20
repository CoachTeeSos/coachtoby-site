#!/usr/bin/env python3
"""Build Singer OS index.html - clean build, no quote escaping issues"""

# Strategy: Write the entire file as a raw string using triple quotes
# For JS strings containing HTML, use double quotes for JS and escaped double quotes (\\\") for HTML attributes
# For JS strings containing single quotes, use double quotes for the JS string

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Singer OS</title>
<style>
:root{--bg:#080808;--card:#181818;--bd:#282828;--pri:#6366f1;--ok:#22c55e;--gold:#eab308;--tx:#f0f0f0;--tx2:#a0a0a0;--tx3:#6a6a6a;--r:12px;--rl:16px}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--tx);min-height:100vh;padding-bottom:80px;font-size:15px}
screen{display:none;min-height:calc(100vh - 80px)}screen.active{display:block}
.sp{padding:20px 16px 40px}
.tb{position:sticky;top:0;background:rgba(8,8,8,.95);border-bottom:1px solid var(--bd);padding:12px 16px;display:flex;justify-content:space-between}
.tb-t{font-size:1rem;font-weight:700}.tb-r{font-size:.8rem;color:var(--gold)}
.bn{position:fixed;bottom:0;left:0;right:0;background:rgba(17,17,17,.97);border-top:1px solid var(--bd);height:68px}
.bn-in{display:flex;justify-content:space-around;height:100%;max-width:500px;margin:0 auto}
.bn-i{display:flex;flex-direction:column;align-items:center;gap:3px;padding:6px;color:var(--tx3);min-width:52px;font-size:.6rem;font-weight:600}
.bn-i.on{color:var(--pri)}.bn-ic{font-size:1.2rem}
.c{background:var(--card);border:1px solid var(--bd);border-radius:var(--rl);padding:18px;margin-bottom:10px}
.c-a{border-color:rgba(99,102,241,.3)}.c-g{border-color:rgba(234,179,8,.3)}
.btn{display:flex;align-items:center;justify-content:center;gap:8px;padding:14px;border-radius:var(--r);font-weight:600;font-size:.9rem;width:100%;margin-bottom:8px}
.btn-p{background:var(--pri);color:#fff}.btn-g{background:transparent;color:var(--tx2)}.btn-s{background:var(--ok);color:#000}
.tag{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.6rem;font-weight:700;text-transform:uppercase}
.tag-p{background:rgba(99,102,241,.1);color:var(--pri)}.tag-s{background:rgba(34,197,94,.1);color:var(--ok)}
.pr{height:5px;background:var(--bd);border-radius:3px;overflow:hidden}.pr-f{height:100%;background:var(--pri);transition:width .5s}
.li{display:flex;align-items:center;gap:12px;padding:14px;background:var(--card);border:1px solid var(--bd);border-radius:var(--r);margin-bottom:6px;cursor:pointer}
.li-ic{width:40px;height:40px;border-radius:var(--r);display:flex;align-items:center;justify-content:center;background:rgba(99,102,241,.08)}
.li-b{flex:1}.li-t{font-weight:600;font-size:.9rem}.li-sub{font-size:.7rem;color:var(--tx3)}
.sec{margin-bottom:20px}.sec-h{display:flex;justify-content:space-between;margin-bottom:10px}
.sec-t{font-size:.7rem;font-weight:700;text-transform:uppercase;color:var(--tx3)}
.hero{padding:16px 0}.hero h1{font-size:1.4rem;font-weight:800;margin-bottom:4px}
.qo{display:flex;align-items:center;gap:10px;padding:14px;border:2px solid var(--bd);border-radius:var(--r);margin-bottom:6px;cursor:pointer}
.qo.sel{border-color:var(--pri)}.qo.ok{border-color:var(--ok)}.qo.bad{border-color:var(--ef4444)}
.qr{width:18px;height:18px;border-radius:50%;border:2px solid var(--bd)}
.qo.sel .qr{background:var(--pri);border-color:var(--pri)}
.es{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--bd)}
.esn{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;background:rgba(99,102,241,.1);color:var(--pri)}
.est p{font-size:.8rem;color:var(--tx3)}
.ft{position:fixed;top:16px;left:50%;transform:translateX(-50%) translateY(-150%);background:var(--card);border:1px solid var(--bd);border-radius:var(--r);padding:12px 18px;z-index:9999;transition:transform .3s}
.ft.show{transform:translateX(-50%) translateY(0)}
screen.active{animation:fi .2s ease both}@keyframes fi{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
</style>
</head>
<body>
<screen class="active" id="s-home"><div class="tb"><div class="tb-t">Singer OS</div><div class="tb-r" id="h-xp">0 XP</div></div><div class="sp" id="h-c"></div></screen>
<screen id="s-learn"><div class="tb"><div class="tb-t">Learn</div></div><div class="sp" id="l-c"></div></screen>
<screen id="s-practice"><div class="tb"><div class="tb-t">Practice</div></div><div class="sp" id="p-c"></div></screen>
<screen id="s-songs"><div class="tb"><div class="tb-t">Songs</div></div><div class="sp" id="g-c"></div></screen>
<screen id="s-progress"><div class="tb"><div class="tb-t">Progress</div></div><div class="sp" id="r-c"></div></screen>
<screen id="s-session"><div class="sp" id="v-c"></div></screen>
<screen id="s-profile"><div class="tb"><div class="tb-t">Profile</div></div><div class="sp" id="f-c"></div></screen>
<nav class="bn"><div class="bn-in">
<a class="bn-i on" id="n-home" href="#" onclick="go('home')"><span class="bn-ic">H</span></a>
<a class="bn-i" id="n-learn" href="#" onclick="go('learn')"><span class="bn-ic">L</span></a>
<a class="bn-i" id="n-practice" href="#" onclick="go('practice')"><span class="bn-ic">P</span></a>
<a class="bn-i" id="n-songs" href="#" onclick="go('songs')"><span class="bn-ic">S</span></a>
<a class="bn-i" id="n-progress" href="#" onclick="go('progress')"><span class="bn-ic">R</span></a>
<a class="bn-i" id="n-profile" href="#" onclick="go('profile')"><span class="bn-ic">M</span></a>
</div></nav>
<div class="ft" id="ft"></div>
<script>
'''

# Now build JS line by line using a list
js = []

js.append("var U={name:'Singer',email:'',xp:0,sessions:0,skills:{airflow:0,source:0,resonance:0,articulation:0,ear:0,mix:0},completed:[],completedSongs:[]};")
js.append("try{var d=localStorage.getItem('singerOS');if(d){var p=JSON.parse(d);if(p&&p.skills){for(var k in p)U[k]=p[k];}}}catch(e){}")
js.append("function save(){try{localStorage.setItem('singerOS',JSON.stringify(U))}catch(e){}}")
js.append("function toast(m){var t=document.getElementById('ft');t.textContent=m;t.className='ft show';setTimeout(function(){t.className='ft';},2500);}")
js.append("")
js.append("function go(id){")
js.append("var ss=document.querySelectorAll('screen');")
js.append("for(var i=0;i<ss.length;i++)ss[i].classList.remove('active');")
js.append("document.getElementById('s-'+id).classList.add('active');")
js.append("var items=document.querySelectorAll('.bn-i');")
js.append("for(var j=0;j<items.length;j++)items[j].classList.remove('on');")
js.append("var ni=document.getElementById('n-'+id);if(ni)ni.classList.add('on');")
js.append("if(id==='home')renderHome();")
js.append("if(id==='learn')renderLearn();")
js.append("if(id==='practice')renderPractice();")
js.append("if(id==='songs')renderSongs();")
js.append("if(id==='progress')renderProgress();")
js.append("if(id==='profile')renderProfile();")
js.append("}")

# renderHome - use ONLY double-quoted JS strings with escaped double quotes for HTML
js.append("")
js.append("function renderHome(){")
js.append("var c=document.getElementById('h-c');")
js.append("document.getElementById('h-xp').textContent=U.xp+' XP';")
js.append('var h="";')
js.append('h+="<div class=\\"hero\\"><h1>Welcome, "+U.name+"</h1><p>Your vocal training starts now.</p></div>";')
js.append('h+="<div class=\\"sec\\"><div class=\\"sec-h\\"><span class=\\"sec-t\\">Quick Practice</span></div>";')
js.append('h+="<div style=\\"display:grid;grid-template-columns:1fr 1fr;gap:8px\\">";')
js.append("var dp=[{n:'Breath',s:'airflow'},{n:'Onset',s:'source'},{n:'Words',s:'articulation'},{n:'Place',s:'resonance'}];")
js.append("for(var i=0;i<dp.length;i++){var d=dp[i];")
js.append('h+="<div class=\\"c\\" style=\\"text-align:center;padding:14px;cursor:pointer\\" onclick=\\"quickDrill(\\\'"+d.s+"\\')\\"><div style=\\"font-size:1.5rem;margin-bottom:4px\\">"+d.n.substring(0,1)+"</div><div style=\\"font-size:.75rem;font-weight:600\\">"+d.n+"</div></div>";')
js.append("}")
js.append("h+='</div></div>';")
js.append('h+="<div class=\\"sec\\"><a class=\\"li\\" href=\\"#\\" onclick=\\"go(\'learn\')\\"><div class=\\"li-ic\\">L</div><div class=\\"li-b\\"><div class=\\"li-t\\">Full Curriculum</div><div class=\\"li-sub\\">12+ lessons</div></div></a></div>";')
js.append('h+="<div class=\\"sec\\"><a class=\\"li\\" href=\\"#\\" onclick=\\"go(\'songs\')\\"><div class=\\"li-ic\\">S</div><div class=\\"li-b\\"><div class=\\"li-t\\">Song Library</div><div class=\\"li-sub\\">8 songs</div></div></a></div>";')
js.append('h+="<div class=\\"sec\\"><a class=\\"li\\" href=\\"#\\" onclick=\\"startDiag()\\"><div class=\\"li-ic\\">D</div><div class=\\"li-b\\"><div class=\\"li-t\\">Voice Check</div><div class=\\"li-sub\\">Get a targeted exercise</div></div></a></div>";')
js.append("c.innerHTML=h;")
js.append("}")

# renderLearn
js.append("")
js.append("function renderLearn(){")
js.append("var c=document.getElementById('l-c');")
js.append('var h="<h2>Curriculum</h2><p style=\\"color:var(--tx3);margin-bottom:14px\\">Complete lessons to level up.</p>";')
lessons = [('vm1','How Your Voice Works',10),('vm2','Breath Appoggio',15),('vm3','Vocal Fold Closure',15),('vm4','Resonance',15),('vm5','Articulation',15),('vm6','Mix Voice',20),('et1','Pitch Matching',10),('vl1','Vocal Load',10)]
for i,(lid,title,xp) in enumerate(lessons):
    num = str(i+1)
    js.append('h+="<div class=\\"li\\" onclick=\\"openLesson(\''+lid+'\')\\"><div class=\\"esn\\">'+num+'</div><div class=\\"li-b\\"><div class=\\"li-t\\">'+title+'</div><div class=\\"li-sub\\">+'+str(xp)+' XP</div></div></div>";')
js.append("c.innerHTML=h;")
js.append("}")

# renderPractice
js.append("")
js.append("function renderPractice(){")
js.append("var c=document.getElementById('p-c');")
js.append('var h="<h2>Practice</h2><p style=\\"color:var(--tx3);margin-bottom:14px\\">Repetition builds mastery.</p>";')
for sk,name in [('airflow','Breath'),('source','Onset'),('articulation','Diction'),('resonance','Hum')]:
    js.append('h+="<div class=\\"li\\" onclick=\\"quickDrill(\''+sk+'\')\\"><div class=\\"li-b\\"><div class=\\"li-t\\">'+name+'</div></div><span class=\\"li-r\\">+10</span></div>";')
js.append('h+="<div class=\\"c c-a\\" onclick=\\"startDiag()\\"><b>Voice Diagnostic</b><br><span style=\\"font-size:.75rem;color:var(--tx3)\\">Get prescribed exercise</span></div>";')
js.append("c.innerHTML=h;")
js.append("}")

# renderSongs
js.append("")
js.append("function renderSongs(){")
js.append("var c=document.getElementById('g-c');")
js.append('var h="<h2>Songs</h2><p style=\\"color:var(--tx3);margin-bottom:14px\\">Apply your training.</p>";')
songs = [('s1','Breathe On Me','Worship'),('s2','Great Are You Lord','Worship'),('s3','Hallelujah','Buckley'),('s4','Essence','Wizkid'),('s5','Someone Like You','Adele'),('s6','Thinking Out Loud','Sheeran')]
for sid,title,artist in songs:
    js.append('h+="<div class=\\"li\\" onclick=\\"openSong(\''+sid+'\')\\"><div class=\\"li-b\\"><div class=\\"li-t\\">'+title+'</div><div class=\\"li-sub\\">'+artist+'</div></div></div>";')
js.append("c.innerHTML=h;")
js.append("}")

# renderProgress
js.append("")
js.append("function renderProgress(){")
js.append("var c=document.getElementById('r-c');")
js.append('var h="<h2>Progress</h2><div class=\\"c c-g text-center\\" style=\\"padding:24px;margin-bottom:16px\\"><h2>"+U.xp+" XP</h2><p style=\\"color:var(--tx3);font-size:.8rem\\">"+U.sessions+" sessions</p></div>";')
js.append("var sys=['airflow','source','resonance','articulation','mix','ear'];")
js.append("for(var s=0;s<sys.length;s++){var sk=sys[s],lvl=U.skills[sk]||0,pct=lvl*10;")
js.append('h+="<div style=\\"margin-bottom:10px\\"><div style=\\"display:flex;justify-content:space-between;margin-bottom:4px\\"><span style=\\"font-size:.8rem\\">"+sk+"</span><span style=\\"font-size:.7rem;color:var(--tx3)\\">"+lvl+"/10</span></div><div class=\\"pr\\"><div class=\\"pr-f\\" style=\\"width:"+pct+"%\\"></div></div></div>";')
js.append("}")
js.append('h+="<button class=\\"btn btn-g\\" style=\\"margin-top:16px\\" onclick=\\"resetAll()\\">Reset All</button>";')
js.append("c.innerHTML=h;")
js.append("}")

# renderProfile
js.append("")
js.append("function renderProfile(){")
js.append("var c=document.getElementById('f-c');")
js.append('var h="<h2>Profile</h2><div class=\\"c\\"><label style=\\"font-size:.75rem;color:var(--tx3)\\">Name</label><input type=\\"text\\" value=\\""+U.name+"\\" style=\\"width:100%;padding:8px 0;border-bottom:1px solid var(--bd)\\" onchange=\\"U.name=this.value;save();\\"></div><div class=\\"c\\"><label style=\\"font-size:.75rem;color:var(--tx3)\\">Email</label><input type=\\"email\\" value=\\""+U.email+"\\" placeholder=\\"your@email.com\\" style=\\"width:100%;padding:8px 0;border-bottom:1px solid var(--bd)\\" onchange=\\"U.email=this.value;save();\\"></div><div class=\\"c\\"><div style=\\"display:flex;justify-content:space-between\\"><span>XP</span><strong>"+U.xp+"</strong></div><div style=\\"display:flex;justify-content:space-between\\"><span>Sessions</span><strong>"+U.sessions+"</strong></div></div>";')
js.append("c.innerHTML=h;")
js.append("}")

# openLesson
js.append("")
js.append("function openLesson(id){")
js.append("var c=document.getElementById('v-c');")
js.append("var L={vm1:{t:'How Your Voice Works',b:'Four systems: Airflow, Source, Resonance, Articulation. Train each separately.',e:'Hum on m for 5 sec. Open to ah. Repeat 5x.',x:10},vm2:{t:'Breath Appoggio',b:'Control the cage around your lungs. Expand ribs, maintain while singing.',e:'Hands on ribs. Breathe in. Hiss sss holding ribs. Goal: 20 sec.',x:15},vm3:{t:'Vocal Fold Closure',b:'Three states: Breathy, Strained, Balanced. Target: balanced.',e:'Say ah -- find clean onset. Hum 5 sec first.',x:15},vm4:{t:'Resonance',b:'Forward placement = clear, projecting. About WHERE vibration is felt.',e:'Hum m, feel buzz. Open to mah -- buzz stays forward.',x:15},vm5:{t:'Articulation',b:'Singing is sustained speech. Lips and tongue work, jaw relaxed.',e:'Speak ma-me-mi-mo-mu. Sing it on one pitch.',x:15},vm6:{t:'Mix Voice',b:'Voice is a continuous gradient. Mix = TA + CT both engaged.',e:'Find your break. Sing on ng. Slide through zone.',x:20},et1:{t:'Pitch Matching',b:'Listen BEFORE you sing. Trainable skill.',e:'Think of a note. Sing it. Imagine higher. Sing that.',x:10},vl1:{t:'Vocal Load',b:'Vocal folds are muscles. They fatigue. If it hurts, stop.',e:'Track practice time. Notice when tired. That is your budget.',x:10}};")
js.append("var ls=L[id];if(!ls)return;")
js.append('var h="<a class=\\"btn btn-g btn-sm\\" href=\\"#\\" onclick=\\"go(\'learn\')\\">Back</a><h1 style=\\"font-size:1.2rem;margin:12px 0\\">"+ls.t+"</h1><div style=\\"background:var(--card);border:1px solid var(--bd);border-radius:var(--rl);padding:16px;margin-bottom:12px;line-height:1.7\\">"+ls.b+"</div><div style=\\"background:rgba(99,102,241,.06);border:1px solid rgba(99,102,241,.15);border-radius:var(--rl);padding:14px;margin-bottom:12px\\"><h3 style=\\"margin-bottom:6px\\">Exercise <span class=\\"tag tag-g\\">+"+ls.xp+" XP</span></h3>"+ls.e+"</div><button class=\\"btn btn-s\\" onclick=\\"finishLesson(\'"+id+"\',"+ls.xp+")\\">I Completed This</button>";')
js.append("c.innerHTML=h;")
js.append("go('session');")
js.append("}")

# finishLesson
js.append("function finishLesson(id,xp){U.xp+=xp;U.sessions++;if(U.completed.indexOf(id)===-1)U.completed.push(id);save();toast('Complete! +'+xp+' XP');go('learn');}")

# quickDrill
js.append("function quickDrill(skill){var c=document.getElementById('v-c');c.innerHTML='<a class=\\"btn btn-g btn-sm\\" href=\\"#\\" onclick=\\"go(\\'home\\')\\">Back</a><div class=\\"c c-a text-center\\" style=\\"padding:28px;margin:12px 0\\"><h2>'+skill+' Drill</h2><p style=\\"color:var(--tx3)\\">Do this now. Tap when done.</p></div><button class=\\"btn btn-s\\" onclick=\\"finishQD(\\''+skill+'\\')\\">I Did It</button>';go('session');}")
js.append("function finishQD(skill){U.xp+=10;U.skills[skill]=Math.min(10,U.skills[skill]+1);U.sessions++;save();toast('Done! +10 XP');go('home');}")

# openSong
js.append("function openSong(id){var S={s1:{t:'Breathe On Me',a:'Worship'},s2:{t:'Great Are You Lord',a:'Worship'},s3:{t:'Hallelujah',a:'Buckley'},s4:{t:'Essence',a:'Wizkid'},s5:{t:'Someone Like You',a:'Adele'},s6:{t:'Thinking Out Loud',a:'Sheeran'}};var s=S[id];if(!s)return;var c=document.getElementById('v-c');c.innerHTML='<a class=\\"btn btn-g btn-sm\\" href=\\"#\\" onclick=\\"go(\\'songs\\')\\">Back</a><h1 style=\\"font-size:1.2rem;margin:12px 0 4px\\">'+s.t+'</h1><p style=\\"color:var(--tx3);margin-bottom:16px\\">'+s.a+'</p><button class=\\"btn btn-p\\" onclick=\\"practiceSong(\\''+id+'\\')\\">I Sang It</button>';go('session');}")
js.append("function practiceSong(id){U.xp+=50;U.sessions++;if(U.completedSongs.indexOf(id)===-1)U.completedSongs.push(id);save();document.getElementById('v-c').innerHTML='<div class=\\"c c-g text-center\\" style=\\"padding:28px\\"><h2>Complete!</h2><p style=\\"color:var(--tx3)\\">+50 XP</p></div><a class=\\"btn btn-p\\" href=\\"#\\" onclick=\\"go(\\'songs\\')\\">Back</a>';}")

# startDiag
js.append("function startDiag(){var syms=[{id:'pitch',l:'Pitch wavers'},{id:'strain',l:'Voice tight'},{id:'breathy',l:'Breathy'},{id:'power',l:'Low volume'},{id:'crack',l:'Cracks'}];var c=document.getElementById('v-c');var h='<a class=\\"btn btn-g btn-sm\\" href=\\"#\\" onclick=\\"go(\\'practice\\')\\">Back</a><h1 style=\\"font-size:1.2rem;margin:12px 0 6px\\">Voice Check</h1><p style=\\"color:var(--tx3);margin-bottom:16px\\">Select all that apply.</p>';for(var i=0;i<syms.length;i++){h+='<div class=\\"qo\\" onclick=\\"togDiag(\\''+syms[i].id+'\\')\\"><div class=\\"qr\\"></div><span>'+syms[i].l+'</span></div>';}h+='<button class=\\"btn btn-p\\" style=\\"margin-top:16px\\" onclick=\\"subDiag()\\">Get Exercise</button>';c.innerHTML=h;go('session');}")
js.append("var diagSel=[];function togDiag(id){var i=diagSel.indexOf(id);if(i===-1){diagSel.push(id);}else{diagSel.splice(i,1);}}")
js.append("function subDiag(){if(diagSel.length===0){toast('Select one');return;}var p='source',mx=0;var sc={airflow:0,source:0,resonance:0};var map={pitch:['source','airflow'],strain:['source'],breathy:['source','airflow'],power:['airflow'],crack:['source']};for(var i=0;i<diagSel.length;i++){var s=map[diagSel[i]];if(s)for(var j=0;j<s.length;j++)sc[s[j]]++;}for(var k in sc)if(sc[k]>mx){mx=sc[k];p=k;}var e={airflow:['Hands on ribs','Breathe in -- ribs push','Hiss sss, hold ribs','Sing phrase -- ribs stay'],source:['Hum m 5 sec','Say ah -- no breathy h','Find clean ah','Scale -- balanced'],resonance:['Hum m -- lip buzz','Open to mah -- forward','Slide on mee','Phrase -- stays forward'],articulation:['Speak ma-me-mi-mo-mu','Fast -- keep clarity','Sing on one pitch','Lyric -- every word']};var steps=e[p]||e.source;var c=document.getElementById('v-c');var h='<a class=\\"btn btn-g btn-sm\\" href=\\"#\\" onclick=\\"go(\\'practice\\')\\">Back</a><h1 style=\\"font-size:1.2rem;margin:12px 0 6px\\">Exercise</h1><p style=\\"color:var(--tx3);margin-bottom:16px\\">Based on your answers.</p>';for(var i=0;i<steps.length;i++){h+='<div class=\\"es\\"><div class=\\"esn\\">'+(i+1)+'</div><div class=\\"est\\"><p>'+steps[i]+'</p></div></div>';}h+='<button class=\\"btn btn-s\\" onclick=\\"finishDiag(\\''+p+'\\',20)\\">I Completed This</button>';c.innerHTML=h;diagSel=[];}")
js.append("function finishDiag(skill,xp){U.xp+=xp;U.skills[skill]=Math.min(10,U.skills[skill]+1);U.sessions++;save();toast('Complete! +'+xp+' XP');go('practice');}")
js.append("function resetAll(){U={name:'Singer',email:'',xp:0,sessions:0,skills:{airflow:0,source:0,resonance:0,articulation:0,ear:0,mix:0},completed:[],completedSongs:[]};save();toast('Reset');go('home');}")
js.append("go('home');")

# Combine
js_str = "\n".join(js)
full = html + js_str + "\n</script>\n</body>\n</html>"

with open('/data/data/com.termux/files/home/sessions-with-toby/index.html', 'w') as f:
    f.write(full)

print(f"Written: {len(full)} bytes, {full.count(chr(10))} lines")

# Verify JS
import subprocess
with open('/data/data/com.termux/files/usr/tmp/t.js', 'w') as f:
    f.write(js_str)
r = subprocess.run(['node', '--check', '/data/data/com.termux/files/usr/tmp/t.js'], capture_output=True, text=True)
print('JS OK' if r.returncode == 0 else 'ERROR: ' + r.stderr[:300])

# Verify HTML structure
print('Has </html>:', '</html>' in full)
print('Has </body>:', '</body>' in full)
print('Has </script>:', '</script>' in full)
print('Braces balanced:', full.count('{') == full.count('}'))
print('Parens balanced:', full.count('(') == full.count(')'))
