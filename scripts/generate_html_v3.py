#!/usr/bin/env python3
"""
Generate v3 HTML: pre-compute all layouts in Python, NO animation/physics in the browser.
The browser just renders static SVG and handles interaction (hover, click, zoom, pan, drag).
"""
import json, math, random

random.seed(42)

with open("graph_data.json") as f:
    graph = json.load(f)

nodes = graph["nodes"]
edges = graph["edges"]

# Build adjacency
adj = {}
for n in nodes:
    adj[n["id"]] = []
for e in edges:
    adj.setdefault(e["source"], []).append(e["target"])
    adj.setdefault(e["target"], []).append(e["source"])

# =======================================
# PRE-COMPUTE LAYOUTS IN PYTHON
# =======================================

# We'll compute 3 layouts and embed all positions.
# The browser just picks which set of (x,y) to use.

W, H = 1400, 900  # reference viewport

def compute_column_layout():
    """4 columns: Presentations | Authors | Departments | Institutions"""
    cols_order = ["presentation", "author", "department", "institution"]
    col_x = {}
    pad = 80
    col_w = (W - pad * 2) / len(cols_order)
    for i, t in enumerate(cols_order):
        col_x[t] = pad + i * col_w + col_w / 2

    groups = {t: [] for t in cols_order}
    for n in nodes:
        if n["type"] in groups:
            groups[n["type"]].append(n)

    # Sort by degree descending within each column
    for t in groups:
        groups[t].sort(key=lambda n: -n["degree"])

    positions = {}
    for t, arr in groups.items():
        if not arr:
            continue
        spacing = min(20, (H - 100) / max(len(arr), 1))
        total_h = len(arr) * spacing
        start_y = max(50, (H - total_h) / 2)
        cx = col_x[t]
        for i, n in enumerate(arr):
            positions[n["id"]] = (cx, start_y + i * spacing)

    return positions


def compute_radial_layout():
    """Concentric rings: presentations in center, then authors, dept, institutions."""
    rings = {"presentation": 60, "author": 200, "department": 320, "institution": 400}
    groups = {"presentation": [], "author": [], "department": [], "institution": []}
    for n in nodes:
        if n["type"] in groups:
            groups[n["type"]].append(n)

    # Sort by degree descending so high-degree nodes are spread
    for t in groups:
        groups[t].sort(key=lambda n: -n["degree"])

    cx, cy = W / 2, H / 2
    positions = {}
    for t, arr in groups.items():
        r = rings[t]
        for i, n in enumerate(arr):
            angle = (i / max(len(arr), 1)) * math.pi * 2 - math.pi / 2
            positions[n["id"]] = (cx + math.cos(angle) * r, cy + math.sin(angle) * r)

    return positions


def compute_force_layout(iterations=400):
    """Force-directed with type-cluster separation. Fully converged in Python."""
    pos = {}
    vel = {}
    cx, cy = W / 2, H / 2

    # Type cluster centers — spread far apart so types don't overlap
    type_centers = {
        "presentation": (cx - 350, cy - 200),
        "author":       (cx, cy),
        "department":   (cx + 200, cy + 250),
        "institution":  (cx + 350, cy - 100),
    }

    node_type = {}
    groups = {}
    for n in nodes:
        groups.setdefault(n["type"], []).append(n)
        node_type[n["id"]] = n["type"]

    for t, arr in groups.items():
        tcx, tcy = type_centers.get(t, (cx, cy))
        for i, n in enumerate(arr):
            angle = (i / len(arr)) * math.pi * 2
            r = 30 + math.sqrt(len(arr)) * 14
            pos[n["id"]] = [tcx + math.cos(angle) * r + random.uniform(-15, 15),
                            tcy + math.sin(angle) * r + random.uniform(-15, 15)]
            vel[n["id"]] = [0.0, 0.0]

    node_ids = [n["id"] for n in nodes]
    id_set = set(node_ids)

    for iteration in range(iterations):
        alpha = max(0.001, 1.0 - iteration / iterations)

        # Repulsion
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                ai, bi = node_ids[i], node_ids[j]
                dx = pos[bi][0] - pos[ai][0]
                dy = pos[bi][1] - pos[ai][1]
                dist = math.sqrt(dx * dx + dy * dy) or 0.1
                if dist > 400:
                    continue
                force = -400 / (dist * dist) * alpha
                fx = dx / dist * force
                fy = dy / dist * force
                vel[ai][0] -= fx; vel[ai][1] -= fy
                vel[bi][0] += fx; vel[bi][1] += fy

        # Attraction along edges (weaker to preserve cluster shape)
        for e in edges:
            s, t = e["source"], e["target"]
            if s not in id_set or t not in id_set:
                continue
            dx = pos[t][0] - pos[s][0]
            dy = pos[t][1] - pos[s][1]
            dist = math.sqrt(dx * dx + dy * dy) or 0.1
            ideal = 100
            force = (dist - ideal) * 0.012 * alpha
            fx = dx / dist * force
            fy = dy / dist * force
            vel[s][0] += fx; vel[s][1] += fy
            vel[t][0] -= fx; vel[t][1] -= fy

        # Type-cluster gravity: each node pulled toward its type center
        for nid in node_ids:
            tcx, tcy = type_centers.get(node_type[nid], (cx, cy))
            vel[nid][0] += (tcx - pos[nid][0]) * 0.004 * alpha
            vel[nid][1] += (tcy - pos[nid][1]) * 0.004 * alpha

        # Gentle global center gravity
        for nid in node_ids:
            vel[nid][0] += (cx - pos[nid][0]) * 0.0003 * alpha
            vel[nid][1] += (cy - pos[nid][1]) * 0.0003 * alpha

        # Integrate with heavy damping
        for nid in node_ids:
            vel[nid][0] *= 0.4; vel[nid][1] *= 0.4
            speed = math.sqrt(vel[nid][0] ** 2 + vel[nid][1] ** 2)
            if speed > 5:
                vel[nid][0] = vel[nid][0] / speed * 5
                vel[nid][1] = vel[nid][1] / speed * 5
            pos[nid][0] += vel[nid][0]
            pos[nid][1] += vel[nid][1]

    return {nid: (pos[nid][0], pos[nid][1]) for nid in node_ids}


print("Computing force layout (300 iterations)...")
force_pos = compute_force_layout(300)
print("Computing column layout...")
column_pos = compute_column_layout()
print("Computing radial layout...")
radial_pos = compute_radial_layout()

# Embed positions into nodes
for n in nodes:
    nid = n["id"]
    n["pos_force"] = list(force_pos.get(nid, (W/2, H/2)))
    n["pos_column"] = list(column_pos.get(nid, (W/2, H/2)))
    n["pos_radial"] = list(radial_pos.get(nid, (W/2, H/2)))

graph_json = json.dumps(graph)

# =======================================
# HTML TEMPLATE
# =======================================
html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BioSafe GenAI 2025 — Author-Affiliation Network</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0e17;color:#e0e6f0;overflow:hidden}
#app{display:flex;height:100vh;width:100vw}
#sidebar{width:360px;min-width:360px;background:#111827;border-right:1px solid #1e293b;display:flex;flex-direction:column;z-index:10}
#sidebar-header{padding:14px 16px;border-bottom:1px solid #1e293b}
#sidebar-header h1{font-size:14px;font-weight:700;color:#f8fafc}
#sidebar-header p{font-size:11px;color:#94a3b8;margin-top:2px}
#controls{padding:10px 16px;border-bottom:1px solid #1e293b}
.cg{margin-bottom:8px}
.cg label{font-size:10px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:3px}
.row{display:flex;gap:4px;flex-wrap:wrap}
.btn{padding:4px 10px;font-size:11px;border:1px solid #334155;border-radius:4px;background:#1e293b;color:#cbd5e1;cursor:pointer;transition:all .15s}
.btn:hover{background:#334155}
.btn.active{background:#3b82f6;border-color:#3b82f6;color:#fff}
.chip{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:12px;font-size:10px;cursor:pointer;border:1px solid transparent;margin:1px;transition:all .15s}
.chip .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.chip.off{opacity:.3}
.chip:hover{border-color:#475569}
#search{width:100%;padding:5px 10px;font-size:12px;border:1px solid #334155;border-radius:4px;background:#0f172a;color:#e2e8f0;outline:none}
#search:focus{border-color:#3b82f6}
#search::placeholder{color:#4b5563}
#stats{padding:6px 16px;font-size:10px;color:#64748b;border-bottom:1px solid #1e293b}
#detail{flex:1;overflow-y:auto;padding:14px 16px}
#detail::-webkit-scrollbar{width:4px}
#detail::-webkit-scrollbar-thumb{background:#334155;border-radius:2px}
.placeholder{color:#4b5563;font-size:12px;text-align:center;padding-top:40px}
.card{background:#1e293b;border-radius:8px;padding:12px}
.card h3{font-size:13px;color:#f1f5f9;word-break:break-word}
.card .tag{font-size:9px;display:inline-block;padding:1px 6px;border-radius:3px;margin-bottom:6px}
.card .links a{display:inline-block;margin:2px 4px 2px 0;padding:2px 7px;font-size:10px;color:#93c5fd;background:#1e3a5f;border-radius:3px;text-decoration:none}
.card .links a:hover{background:#2563eb;color:#fff}
.conns h4{font-size:10px;color:#94a3b8;margin:8px 0 3px}
.conn{font-size:11px;color:#cbd5e1;padding:1px 0;cursor:pointer}
.conn:hover{color:#60a5fa}
.conn .et{font-size:9px;color:#64748b;margin-left:4px}
#legend{padding:10px 16px;border-top:1px solid #1e293b;font-size:10px;color:#64748b}
#legend h4{text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.li{display:flex;align-items:center;gap:5px;margin:2px 0;color:#94a3b8;font-size:11px}
.ld{width:10px;height:10px;border-radius:50%}
#graph-container{flex:1;position:relative;background:#0a0e17}
#tooltip{position:absolute;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:6px 10px;font-size:11px;color:#e2e8f0;pointer-events:none;opacity:0;z-index:100;max-width:280px;box-shadow:0 4px 12px rgba(0,0,0,.5);transition:opacity .1s}
.tt-l{font-weight:600;font-size:12px}
.tt-t{font-size:10px;color:#94a3b8}
.tt-d{font-size:10px;color:#64748b;margin-top:1px}
.col-lbl{position:absolute;top:10px;font-size:11px;font-weight:700;color:#334155;text-transform:uppercase;letter-spacing:1px;pointer-events:none;z-index:5;display:none;text-align:center}
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <div id="sidebar-header">
      <h1>BioSafe GenAI 2025</h1>
      <p>NeurIPS Workshop — Author &amp; Affiliation Network</p>
    </div>
    <div id="controls">
      <div class="cg"><label>Layout</label>
        <div class="row">
          <button class="btn" data-layout="force">Force</button>
          <button class="btn active" data-layout="column">Column</button>
          <button class="btn" data-layout="radial">Radial</button>
        </div>
      </div>
      <div class="cg"><label>Complexity</label>
        <div class="row">
          <button class="btn active" data-detail="full">Full (350 nodes)</button>
          <button class="btn" data-detail="simple">Simplified</button>
        </div>
      </div>
      <div class="cg"><label>Node Types</label><div class="row" id="filters"></div></div>
      <div class="cg"><label>Edge Types</label><div class="row" id="edge-filters"></div></div>
      <div class="cg"><label>Search</label><input type="text" id="search" placeholder="Search nodes…" /></div>
    </div>
    <div id="stats"></div>
    <div id="detail"><div class="placeholder">Click a node to see details</div></div>
    <div id="legend"></div>
  </div>
  <div id="graph-container">
    <svg id="svg"></svg>
    <div id="tooltip"></div>
    <div class="col-lbl" id="cl0">Presentations</div>
    <div class="col-lbl" id="cl1">Authors</div>
    <div class="col-lbl" id="cl2">Departments</div>
    <div class="col-lbl" id="cl3">Institutions</div>
  </div>
</div>
<script>
const G = __GRAPH_JSON__;
const REF_W = 1400, REF_H = 900;

const COL={
  presentation:{fill:'#f59e0b',stroke:'#b45309',label:'Presentation'},
  author:{fill:'#3b82f6',stroke:'#1d4ed8',label:'Author'},
  institution:{fill:'#10b981',stroke:'#047857',label:'Institution'},
  department:{fill:'#8b5cf6',stroke:'#6d28d9',label:'Department'}
};
const ECOL={authored:'#f59e0b',current_affiliation:'#10b981',past_affiliation:'#065f46',part_of:'#8b5cf6'};

let allNodes=G.nodes, allEdges=G.edges, nodeMap={};
allNodes.forEach(n=>nodeMap[n.id]=n);

let layout='column';
let filtType={presentation:true,author:true,institution:true,department:true};
let filtEdge={authored:true,current_affiliation:true,past_affiliation:true,part_of:true};
let searchQ='', selNode=null, hovNode=null;
let simpleMode=false;
let tx=0,ty=0,tk=1;

// Which nodes/edges are active (after simplification filter)
let activeNodes=allNodes, activeEdges=allEdges;

function setSimple(on){
  simpleMode=on;
  if(!on){ activeNodes=allNodes; activeEdges=allEdges; }
  else {
    // Keep: all presentations, all authors, all departments,
    // institutions with degree>=3 OR with current_affiliation edges
    const keepInst=new Set();
    allEdges.forEach(e=>{if(e.type==='current_affiliation'||e.type==='part_of'){keepInst.add(e.target);keepInst.add(e.source);}});
    allNodes.forEach(n=>{if(n.type==='institution'&&n.degree>=3) keepInst.add(n.id);});
    const keep=new Set();
    allNodes.forEach(n=>{if(n.type!=='institution'||keepInst.has(n.id)) keep.add(n.id);});
    activeNodes=allNodes.filter(n=>keep.has(n.id));
    activeEdges=allEdges.filter(e=>keep.has(e.source)&&keep.has(e.target));
  }
}

function vis(){ return activeNodes.filter(n=>filtType[n.type]&&(!searchQ||n.label.toLowerCase().includes(searchQ))); }
function visE(){ const s=new Set(vis().map(n=>n.id)); return activeEdges.filter(e=>filtEdge[e.type]&&s.has(e.source)&&s.has(e.target)); }
function neighbors(id){ const r=[]; activeEdges.forEach(e=>{
  if(e.source===id&&nodeMap[e.target]) r.push({n:nodeMap[e.target],e});
  if(e.target===id&&nodeMap[e.source]) r.push({n:nodeMap[e.source],e});
}); return r; }

const svg=document.getElementById('svg'), ctr=document.getElementById('graph-container'), tip=document.getElementById('tooltip');
let W,H;
function resize(){ const r=ctr.getBoundingClientRect(); W=r.width; H=r.height; svg.setAttribute('width',W); svg.setAttribute('height',H); }
resize();
window.addEventListener('resize',()=>{resize();render();});

function nr(n){ return Math.max(3,Math.min(18,2+n.degree*1.1)); }

// Get node position for current layout, scaled to viewport
function getPos(n){
  const key='pos_'+layout;
  const p=n[key]||[REF_W/2,REF_H/2];
  return [p[0]*W/REF_W, p[1]*H/REF_H];
}

// Animated transition
let animating=false, animStart=0, animDur=600;
let posFrom={}, posTo={};

function animateToLayout(){
  const vn=vis();
  posFrom={}; posTo={};
  vn.forEach(n=>{
    posFrom[n.id]=[n._rx||getPos(n)[0], n._ry||getPos(n)[1]];
    posTo[n.id]=getPos(n);
  });
  animStart=performance.now();
  animating=true;
  function tick(now){
    let t=Math.min(1,(now-animStart)/animDur);
    // ease out cubic
    t=1-Math.pow(1-t,3);
    vn.forEach(n=>{
      const f=posFrom[n.id]||getPos(n), to=posTo[n.id]||getPos(n);
      n._rx=f[0]+(to[0]-f[0])*t;
      n._ry=f[1]+(to[1]-f[1])*t;
    });
    render();
    if(t<1) requestAnimationFrame(tick);
    else { animating=false; vn.forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];}); render(); }
  }
  requestAnimationFrame(tick);
}

// ===== RENDER (pure, no physics) =====
function render(){
  const vn=vis(), ve=visE();
  // Ensure positions exist
  vn.forEach(n=>{ if(n._rx==null){const p=getPos(n);n._rx=p[0];n._ry=p[1];} });

  svg.innerHTML='';
  const g=document.createElementNS('http://www.w3.org/2000/svg','g');
  g.setAttribute('transform','translate('+tx+','+ty+') scale('+tk+')');
  svg.appendChild(g);

  // Highlight set: selected node takes priority over hover
  const hn=selNode||hovNode;
  const hl=new Set();
  if(hn){ hl.add(hn.id); neighbors(hn.id).forEach(({n})=>hl.add(n.id)); }

  // Edges
  ve.forEach(e=>{
    const a=nodeMap[e.source], b=nodeMap[e.target];
    if(!a||!b||a._rx==null||b._rx==null) return;
    const ln=document.createElementNS('http://www.w3.org/2000/svg','line');
    ln.setAttribute('x1',a._rx);ln.setAttribute('y1',a._ry);
    ln.setAttribute('x2',b._rx);ln.setAttribute('y2',b._ry);
    let col=ECOL[e.type]||'#444',w=0.4,op=0.2;
    if(hn){
      if(e.source===hn.id||e.target===hn.id){col=COL[hn.type]?.fill||'#fff';w=1.8;op=0.9;}
      else op=0.03;
    }
    ln.setAttribute('stroke',col);ln.setAttribute('stroke-width',w);ln.setAttribute('opacity',op);
    g.appendChild(ln);
  });

  // Nodes
  vn.forEach(n=>{
    const r=nr(n), c=COL[n.type]||{fill:'#666',stroke:'#444'};
    let op=hn&&!hl.has(n.id)?0.08:1;
    let sw=n===selNode?2.5:0.8, sc=n===selNode?'#fff':c.stroke;
    const x=n._rx, y=n._ry;

    if(n.subtype==='oral'){
      const s=r*1.3;
      const p=document.createElementNS('http://www.w3.org/2000/svg','polygon');
      p.setAttribute('points',x+','+(y-s)+' '+(x+s)+','+y+' '+x+','+(y+s)+' '+(x-s)+','+y);
      p.setAttribute('fill',c.fill);p.setAttribute('stroke',sc);p.setAttribute('stroke-width',sw);
      p.setAttribute('opacity',op);p.dataset.id=n.id;p.style.cursor='pointer';g.appendChild(p);
    } else {
      const ci=document.createElementNS('http://www.w3.org/2000/svg','circle');
      ci.setAttribute('cx',x);ci.setAttribute('cy',y);ci.setAttribute('r',r);
      ci.setAttribute('fill',c.fill);ci.setAttribute('stroke',sc);ci.setAttribute('stroke-width',sw);
      ci.setAttribute('opacity',op);ci.dataset.id=n.id;ci.style.cursor='pointer';g.appendChild(ci);
    }

    // Labels
    const showLabel=n.degree>=8||n===selNode||n===hovNode||(hn&&hl.has(n.id)&&n.degree>=2);
    if(showLabel){
      const t=document.createElementNS('http://www.w3.org/2000/svg','text');
      t.setAttribute('x',x);t.setAttribute('y',y-r-3);
      t.setAttribute('text-anchor','middle');t.setAttribute('fill','#cbd5e1');
      t.setAttribute('font-size',Math.max(7,Math.min(11,5+n.degree*0.3)));
      t.setAttribute('opacity',op);t.setAttribute('pointer-events','none');
      const mx=35;t.textContent=n.label.length>mx?n.label.slice(0,mx)+'…':n.label;
      g.appendChild(t);
    }
  });

  // Column headers
  ['cl0','cl1','cl2','cl3'].forEach(id=>document.getElementById(id).style.display='none');
  if(layout==='column'){
    const pad=80*W/REF_W, colW=(W-pad*2)/4;
    ['cl0','cl1','cl2','cl3'].forEach((id,i)=>{
      const el=document.getElementById(id);
      el.style.display='block';
      el.style.left=(pad+i*colW+colW/2-50)+'px';
      el.style.width='100px';
    });
  }

  document.getElementById('stats').textContent=vn.length+' nodes, '+ve.length+' edges | '+G.metadata.total_papers+' papers, '+G.metadata.total_authors+' authors';
}

// ===== INTERACTION =====
function showTip(n,x,y){
  tip.innerHTML='<div class="tt-l">'+n.label+'</div><div class="tt-t">'+n.type+(n.subtype!==n.type?' · '+n.subtype:'')+'</div><div class="tt-d">'+n.degree+' connections</div>';
  tip.style.opacity=1;tip.style.left=(x+14)+'px';tip.style.top=(y-8)+'px';
}

function showInfo(n){
  const d=document.getElementById('detail'), c=COL[n.type]?.fill||'#666';
  let lnk='';
  if(n.details) Object.entries(n.details).forEach(([k,v])=>{
    if(v&&typeof v==='string'&&v.startsWith('http')) lnk+='<a href="'+v+'" target="_blank">'+k+'</a>';
    else if(v) lnk+='<span style="font-size:10px;color:#94a3b8;margin-right:6px">'+k+': '+v+'</span>';
  });
  const nb=neighbors(n.id), grp={};
  nb.forEach(({n:nn,e})=>{if(!grp[nn.type])grp[nn.type]=[];grp[nn.type].push({n:nn,et:e.type});});
  let cn='';
  Object.entries(grp).forEach(([t,items])=>{
    cn+='<h4 style="color:'+(COL[t]?.fill||'#888')+'">'+(COL[t]?.label||t)+' ('+items.length+')</h4>';
    items.forEach(({n:nn,et})=>{cn+='<div class="conn" data-id="'+nn.id+'">'+nn.label+'<span class="et">'+et.replace(/_/g,' ')+'</span></div>';});
  });
  d.innerHTML='<div class="card"><div class="tag" style="background:'+c+'22;color:'+c+'">'+n.type+(n.subtype!==n.type?' · '+n.subtype:'')+'</div><h3>'+n.label+'</h3>'+(n.tldr?'<p style="font-size:11px;color:#94a3b8;margin-top:5px">'+n.tldr+'</p>':'')+'<div class="links" style="margin-top:6px">'+lnk+'</div><div class="conns">'+cn+'</div></div>';
  d.querySelectorAll('.conn').forEach(el=>el.addEventListener('click',()=>{
    const t=nodeMap[el.dataset.id];if(t){selNode=t;showInfo(t);render();}
  }));
}

function hitTest(mx,my){
  let cl=null,md=Infinity;
  vis().forEach(n=>{
    if(n._rx==null) return;
    const dx=n._rx-mx,dy=n._ry-my,d=Math.sqrt(dx*dx+dy*dy);
    if(d<nr(n)+6&&d<md){cl=n;md=d;}
  });
  return cl;
}

svg.addEventListener('mousemove',e=>{
  if(dragging||panning) return;
  const r=ctr.getBoundingClientRect();
  const mx=(e.clientX-r.left-tx)/tk, my=(e.clientY-r.top-ty)/tk;
  const cl=hitTest(mx,my);
  if(cl!==hovNode){
    hovNode=cl;
    if(cl){
      showTip(cl,e.clientX-r.left,e.clientY-r.top);
      // Only re-render hover highlight if nothing is selected
      if(!selNode) render();
    } else {
      tip.style.opacity=0;
      if(!selNode) render();
    }
  } else if(cl) {
    showTip(cl,e.clientX-r.left,e.clientY-r.top);
  }
});

svg.addEventListener('click',e=>{
  if(justDragged){justDragged=false;return;}
  const r=ctr.getBoundingClientRect();
  const mx=(e.clientX-r.left-tx)/tk, my=(e.clientY-r.top-ty)/tk;
  const cl=hitTest(mx,my);
  if(cl){
    selNode=cl;showInfo(cl);
  } else {
    // Only deselect if clicking on empty space (not panning)
    selNode=null;hovNode=null;
    document.getElementById('detail').innerHTML='<div class="placeholder">Click a node to see details</div>';
  }
  render();
});

// Drag nodes
let dragging=null, dragOff={x:0,y:0}, justDragged=false;
svg.addEventListener('mousedown',e=>{
  if(e.button!==0) return;
  const r=ctr.getBoundingClientRect();
  const mx=(e.clientX-r.left-tx)/tk, my=(e.clientY-r.top-ty)/tk;
  const cl=hitTest(mx,my);
  if(cl){dragging=cl;dragOff={x:cl._rx-mx,y:cl._ry-my};e.preventDefault();e.stopPropagation();return;}
});

// Pan
let panning=false, panS={x:0,y:0};
svg.addEventListener('mousedown',e=>{
  if(!dragging&&e.button===0){panning=true;panS={x:e.clientX-tx,y:e.clientY-ty};}
});
window.addEventListener('mousemove',e=>{
  if(dragging){
    const r=ctr.getBoundingClientRect();
    const mx=(e.clientX-r.left-tx)/tk, my=(e.clientY-r.top-ty)/tk;
    dragging._rx=mx+dragOff.x; dragging._ry=my+dragOff.y;
    justDragged=true;
    render();
  } else if(panning){tx=e.clientX-panS.x;ty=e.clientY-panS.y;render();}
});
window.addEventListener('mouseup',()=>{dragging=null;panning=false;});

// Zoom
svg.addEventListener('wheel',e=>{
  e.preventDefault();
  const r=ctr.getBoundingClientRect();
  const mx=e.clientX-r.left, my=e.clientY-r.top;
  const d=e.deltaY>0?0.92:1.08;
  const nk=Math.max(0.1,Math.min(8,tk*d));
  tx=mx-(mx-tx)*(nk/tk); ty=my-(my-ty)*(nk/tk); tk=nk;
  render();
},{passive:false});

// ===== CONTROLS =====
document.querySelectorAll('[data-layout]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-layout]').forEach(x=>x.classList.remove('active'));
  b.classList.add('active'); layout=b.dataset.layout;
  animateToLayout();
}));
document.querySelectorAll('[data-detail]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-detail]').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  setSimple(b.dataset.detail==='simple');
  tx=0;ty=0;tk=1;
  vis().forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});
  render();
}));

const ff=document.getElementById('filters');
Object.entries(COL).forEach(([t,cfg])=>{
  const c=document.createElement('div');c.className='chip';
  c.innerHTML='<span class="dot" style="background:'+cfg.fill+'"></span>'+cfg.label;
  c.addEventListener('click',()=>{filtType[t]=!filtType[t];c.classList.toggle('off',!filtType[t]);render();});
  ff.appendChild(c);
});
const ef=document.getElementById('edge-filters');
Object.entries(ECOL).forEach(([t,col])=>{
  const c=document.createElement('div');c.className='chip';
  c.innerHTML='<span class="dot" style="background:'+col+'"></span>'+t.replace(/_/g,' ');
  c.addEventListener('click',()=>{filtEdge[t]=!filtEdge[t];c.classList.toggle('off',!filtEdge[t]);render();});
  ef.appendChild(c);
});
document.getElementById('search').addEventListener('input',e=>{searchQ=e.target.value.toLowerCase();render();});

const lg=document.getElementById('legend');
lg.innerHTML='<h4>Legend</h4>';
Object.entries(COL).forEach(([t,cfg])=>{lg.innerHTML+='<div class="li"><span class="ld" style="background:'+cfg.fill+'"></span>'+cfg.label+'</div>';});
lg.innerHTML+='<div class="li" style="margin-top:3px"><span style="font-size:10px">&#9670; Oral &nbsp; &#9679; Poster &nbsp; Size = degree</span></div>';

// ===== BOOT =====
setSimple(false);
vis().forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});
render();
</script>
</body>
</html>"""

html = html.replace('__GRAPH_JSON__', graph_json)

out_path = "/sessions/eloquent-jolly-knuth/mnt/outputs/biosafe_network.html"
with open(out_path, "w") as f:
    f.write(html)

print(f"Generated v3: {len(html)//1024} KB — ZERO physics in browser, all pre-computed")
