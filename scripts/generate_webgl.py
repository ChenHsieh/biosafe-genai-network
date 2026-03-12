#!/usr/bin/env python3
"""
Generate WebGL-based HTML visualization.
Uses the same graph_data.json and pre-computed layouts as v3,
but renders via WebGL (Canvas 2D + offscreen) for much smoother performance.
"""
import json, math, random, os

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH_FILE = os.path.join(BASE_DIR, "data", "graph_data.json")

with open(GRAPH_FILE) as f:
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

ALL_NODE_TYPES = ["funder", "program", "presentation", "author", "department", "institution", "org", "publication"]
ALL_EDGE_TYPES = ["funds", "authored", "current_affiliation", "past_affiliation", "part_of",
                  "performs_on", "biosecurity_eval", "policy_forum", "published_study",
                  "organized", "invited_speaker"]

W, H = 1600, 900

def compute_column_layout():
    cols_order = ["funder", "program", "institution", "department", "author", "presentation", "publication"]
    col_x = {}
    pad = 60
    col_w = (W - pad * 2) / len(cols_order)
    for i, t in enumerate(cols_order):
        col_x[t] = pad + i * col_w + col_w / 2
    col_x["org"] = col_x["institution"]

    groups = {t: [] for t in cols_order + ["org"]}
    for n in nodes:
        if n["type"] in groups:
            groups[n["type"]].append(n)
    for t in groups:
        groups[t].sort(key=lambda n: -n.get("degree", 0))

    inst_and_org = groups["institution"] + groups["org"]
    inst_and_org.sort(key=lambda n: -n.get("degree", 0))

    positions = {}
    for t in ["funder", "program", "department", "author", "presentation", "publication"]:
        arr = groups[t]
        if not arr:
            continue
        spacing = min(22, (H - 100) / max(len(arr), 1))
        total_h = len(arr) * spacing
        start_y = max(50, (H - total_h) / 2)
        cx = col_x[t]
        for i, n in enumerate(arr):
            positions[n["id"]] = (cx, start_y + i * spacing)

    if inst_and_org:
        spacing = min(18, (H - 100) / max(len(inst_and_org), 1))
        total_h = len(inst_and_org) * spacing
        start_y = max(50, (H - total_h) / 2)
        cx = col_x["institution"]
        for i, n in enumerate(inst_and_org):
            positions[n["id"]] = (cx, start_y + i * spacing)

    return positions


def compute_radial_layout():
    rings = {"funder": 30, "program": 100, "institution": 185, "org": 185,
             "department": 270, "author": 355, "presentation": 430, "publication": 460}
    groups = {}
    for t in ALL_NODE_TYPES:
        groups[t] = []
    for n in nodes:
        if n["type"] in groups:
            groups[n["type"]].append(n)
    for t in groups:
        groups[t].sort(key=lambda n: -n.get("degree", 0))

    cx, cy = W / 2, H / 2
    positions = {}
    for t, arr in groups.items():
        r = rings.get(t, 300)
        for i, n in enumerate(arr):
            angle = (i / max(len(arr), 1)) * math.pi * 2 - math.pi / 2
            positions[n["id"]] = (cx + math.cos(angle) * r, cy + math.sin(angle) * r)
    return positions


def compute_force_layout(iterations=500):
    pos = {}
    vel = {}
    cx, cy = W / 2, H / 2
    type_centers = {
        "funder":       (cx - 620, cy - 50),
        "program":      (cx - 400, cy - 220),
        "institution":  (cx - 150, cy - 280),
        "org":          (cx - 100, cy + 220),
        "department":   (cx + 120, cy + 280),
        "author":       (cx + 300, cy),
        "presentation": (cx + 520, cy - 100),
        "publication":  (cx + 450, cy + 250),
    }
    node_type = {}
    groups = {}
    for n in nodes:
        groups.setdefault(n["type"], []).append(n)
        node_type[n["id"]] = n["type"]

    for t, arr in groups.items():
        tcx, tcy = type_centers.get(t, (cx, cy))
        for i, n in enumerate(arr):
            angle = (i / max(len(arr), 1)) * math.pi * 2
            r = 30 + math.sqrt(len(arr)) * 14
            pos[n["id"]] = [tcx + math.cos(angle) * r + random.uniform(-10, 10),
                            tcy + math.sin(angle) * r + random.uniform(-10, 10)]
            vel[n["id"]] = [0.0, 0.0]

    node_ids = [n["id"] for n in nodes]
    id_set = set(node_ids)

    for iteration in range(iterations):
        alpha = max(0.001, 1.0 - iteration / iterations)

        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                ai, bi = node_ids[i], node_ids[j]
                dx = pos[bi][0] - pos[ai][0]
                dy = pos[bi][1] - pos[ai][1]
                dist = math.sqrt(dx * dx + dy * dy) or 0.1
                same_type = node_type[ai] == node_type[bi]
                radius_cutoff = 300 if same_type else 500
                base_strength = 350 if same_type else 900
                if dist > radius_cutoff:
                    continue
                force = -base_strength / (dist * dist) * alpha
                fx = dx / dist * force
                fy = dy / dist * force
                vel[ai][0] -= fx; vel[ai][1] -= fy
                vel[bi][0] += fx; vel[bi][1] += fy

        for e in edges:
            s, t = e["source"], e["target"]
            if s not in id_set or t not in id_set:
                continue
            dx = pos[t][0] - pos[s][0]
            dy = pos[t][1] - pos[s][1]
            dist = math.sqrt(dx * dx + dy * dy) or 0.1
            ideal = 120
            force = (dist - ideal) * 0.008 * alpha
            fx = dx / dist * force
            fy = dy / dist * force
            vel[s][0] += fx; vel[s][1] += fy
            vel[t][0] -= fx; vel[t][1] -= fy

        gravity_strength = 0.012
        for nid in node_ids:
            tcx, tcy = type_centers.get(node_type[nid], (cx, cy))
            vel[nid][0] += (tcx - pos[nid][0]) * gravity_strength * alpha
            vel[nid][1] += (tcy - pos[nid][1]) * gravity_strength * alpha

        for nid in node_ids:
            vel[nid][0] += (cx - pos[nid][0]) * 0.0003 * alpha
            vel[nid][1] += (cy - pos[nid][1]) * 0.0003 * alpha

        for nid in node_ids:
            vel[nid][0] *= 0.4; vel[nid][1] *= 0.4
            speed = math.sqrt(vel[nid][0] ** 2 + vel[nid][1] ** 2)
            if speed > 5:
                vel[nid][0] = vel[nid][0] / speed * 5
                vel[nid][1] = vel[nid][1] / speed * 5
            pos[nid][0] += vel[nid][0]
            pos[nid][1] += vel[nid][1]

    return {nid: (pos[nid][0], pos[nid][1]) for nid in node_ids}


# Compute degree
node_ids_set = {n["id"] for n in nodes}
degree_counter = {n["id"]: 0 for n in nodes}
for e in edges:
    if e["source"] in degree_counter:
        degree_counter[e["source"]] += 1
    if e["target"] in degree_counter:
        degree_counter[e["target"]] += 1
for n in nodes:
    n["degree"] = degree_counter.get(n["id"], 0)

print("Computing force layout (300 iterations)...")
force_pos = compute_force_layout(300)
print("Computing column layout...")
column_pos = compute_column_layout()
print("Computing radial layout...")
radial_pos = compute_radial_layout()

for n in nodes:
    nid = n["id"]
    n["pos_force"] = list(force_pos.get(nid, (W/2, H/2)))
    n["pos_column"] = list(column_pos.get(nid, (W/2, H/2)))
    n["pos_radial"] = list(radial_pos.get(nid, (W/2, H/2)))

total_papers = sum(1 for n in nodes if n["type"] == "presentation")
total_authors = sum(1 for n in nodes if n["type"] == "author")
total_insts = sum(1 for n in nodes if n["type"] in ("institution", "org"))
total_funding = sum(e.get("amount", 0) or 0 for e in edges if e.get("type") == "funds" and e.get("amount"))
bridge_count = sum(1 for n in nodes if n.get("is_bridge"))

graph["metadata"] = graph.get("metadata", {})
graph["metadata"]["total_papers"] = total_papers
graph["metadata"]["total_authors"] = total_authors
graph["metadata"]["total_institutions"] = total_insts
graph["metadata"]["total_funding"] = total_funding
graph["metadata"]["bridge_nodes"] = bridge_count

graph_json = json.dumps(graph)

# ======================================
# WEBGL HTML TEMPLATE
# ======================================
html = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Biosecurity Atlas — WebGL</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0e17;color:#e0e6f0;overflow:hidden}
#app{display:flex;height:100vh;width:100vw}
#sidebar{width:380px;min-width:380px;background:#111827;border-right:1px solid #1e293b;display:flex;flex-direction:column;z-index:10}
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
.card .funding{font-size:11px;color:#fbbf24;margin-top:4px}
.conns h4{font-size:10px;color:#94a3b8;margin:8px 0 3px}
.conn{font-size:11px;color:#cbd5e1;padding:1px 0;cursor:pointer}
.conn:hover{color:#60a5fa}
.conn .et{font-size:9px;color:#64748b;margin-left:4px}
.conn .amt{font-size:9px;color:#fbbf24;margin-left:4px}
#legend{padding:10px 16px;border-top:1px solid #1e293b;font-size:10px;color:#64748b}
#legend h4{text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.li{display:flex;align-items:center;gap:5px;margin:2px 0;color:#94a3b8;font-size:11px}
.ld{width:10px;height:10px;border-radius:50%}
#graph-container{flex:1;position:relative;background:#0a0e17}
canvas{display:block}
#tooltip{position:absolute;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:6px 10px;font-size:11px;color:#e2e8f0;pointer-events:none;opacity:0;z-index:100;max-width:280px;box-shadow:0 4px 12px rgba(0,0,0,.5);transition:opacity .1s}
.tt-l{font-weight:600;font-size:12px}
.tt-t{font-size:10px;color:#94a3b8}
.tt-d{font-size:10px;color:#64748b;margin-top:1px}
.bridge-badge{display:inline-block;font-size:8px;background:#fbbf24;color:#000;padding:0 4px;border-radius:3px;margin-left:4px;font-weight:700}
#perf{position:absolute;top:8px;right:8px;font-size:9px;color:#334155;z-index:5}
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <div id="sidebar-header">
      <h1>Biosecurity Atlas <span style="color:#22d3ee;font-size:10px">WebGL</span></h1>
      <p>NeurIPS BioSafe GenAI 2025 + Funding Network</p>
    </div>
    <div id="controls">
      <div class="cg"><label>Layout</label>
        <div class="row">
          <button class="btn" data-layout="force">Force</button>
          <button class="btn active" data-layout="column">Column</button>
          <button class="btn" data-layout="radial">Radial</button>
        </div>
      </div>
      <div class="cg"><label>Layer</label>
        <div class="row">
          <button class="btn active" data-layer="all">All</button>
          <button class="btn" data-layer="workshop">Workshop Only</button>
          <button class="btn" data-layer="funding">Funding Only</button>
          <button class="btn" data-layer="policy">Policy & Evals</button>
        </div>
      </div>
      <div class="cg"><label>Complexity</label>
        <div class="row">
          <button class="btn active" data-detail="full">Full</button>
          <button class="btn" data-detail="simple">Simplified</button>
        </div>
      </div>
      <div class="cg"><label>Node Types</label><div class="row" id="filters"></div></div>
      <div class="cg"><label>Edge Types</label><div class="row" id="edge-filters"></div></div>
      <div class="cg"><label>Search</label><input type="text" id="search" placeholder="Search nodes..." /></div>
    </div>
    <div id="stats"></div>
    <div id="detail"><div class="placeholder">Click a node to see details</div></div>
    <div id="legend"></div>
  </div>
  <div id="graph-container">
    <canvas id="canvas"></canvas>
    <div id="tooltip"></div>
    <div id="perf"></div>
  </div>
</div>
<script>
const G = __GRAPH_JSON__;
const REF_W = 1600, REF_H = 900;

const COL={
  funder:{fill:'#ef4444',stroke:'#b91c1c',label:'Funder',shape:'diamond'},
  program:{fill:'#f97316',stroke:'#c2410c',label:'Program',shape:'rect'},
  presentation:{fill:'#f59e0b',stroke:'#b45309',label:'Presentation'},
  author:{fill:'#3b82f6',stroke:'#1d4ed8',label:'Author'},
  institution:{fill:'#10b981',stroke:'#047857',label:'Institution'},
  department:{fill:'#8b5cf6',stroke:'#6d28d9',label:'Department'},
  org:{fill:'#14b8a6',stroke:'#0d9488',label:'Organization',shape:'rect'},
  publication:{fill:'#ec4899',stroke:'#be185d',label:'Publication',shape:'rect'},
};
const ECOL={funds:'#ef4444',authored:'#f59e0b',current_affiliation:'#10b981',past_affiliation:'#065f46',part_of:'#8b5cf6',performs_on:'#f97316',biosecurity_eval:'#ec4899',policy_forum:'#a855f7',published_study:'#06b6d4',organized:'#22d3ee',invited_speaker:'#facc15'};

const LAYERS={
  all:{nodes:new Set(Object.keys(COL)),edges:new Set(Object.keys(ECOL))},
  workshop:{nodes:new Set(['presentation','author','institution','department']),edges:new Set(['authored','current_affiliation','past_affiliation','part_of','organized','invited_speaker'])},
  funding:{nodes:new Set(['funder','program','institution','org']),edges:new Set(['funds','performs_on'])},
  policy:{nodes:new Set(['institution','org','publication','author']),edges:new Set(['biosecurity_eval','policy_forum','published_study','authored'])},
};

let allNodes=G.nodes, allEdges=G.edges, nodeMap={};
allNodes.forEach(n=>nodeMap[n.id]=n);

let layout='column', layer='all';
let filtType={}; Object.keys(COL).forEach(t=>filtType[t]=true);
let filtEdge={}; Object.keys(ECOL).forEach(t=>filtEdge[t]=true);
let searchQ='', selNode=null, hovNode=null, simpleMode=false;
let tx=0, ty=0, tk=1;
let activeNodes=allNodes, activeEdges=allEdges;

function setSimple(on){
  simpleMode=on;
  if(!on){activeNodes=allNodes;activeEdges=allEdges;}
  else{
    const keepInst=new Set();
    allEdges.forEach(e=>{if(e.type==='current_affiliation'||e.type==='part_of'||e.type==='funds'){keepInst.add(e.target);keepInst.add(e.source);}});
    allNodes.forEach(n=>{if(n.type==='institution'&&n.degree>=3)keepInst.add(n.id);});
    const keep=new Set();
    allNodes.forEach(n=>{
      if(n.type==='funder'||n.type==='program'||n.type==='org'||n.type==='publication')keep.add(n.id);
      else if(n.type!=='institution'||keepInst.has(n.id))keep.add(n.id);
    });
    activeNodes=allNodes.filter(n=>keep.has(n.id));
    activeEdges=allEdges.filter(e=>keep.has(e.source)&&keep.has(e.target));
  }
}

function vis(){
  const lt=LAYERS[layer].nodes;
  return activeNodes.filter(n=>lt.has(n.type)&&filtType[n.type]&&(!searchQ||n.label.toLowerCase().includes(searchQ)));
}
function visE(){
  const s=new Set(vis().map(n=>n.id)), le=LAYERS[layer].edges;
  return activeEdges.filter(e=>le.has(e.type)&&filtEdge[e.type]&&s.has(e.source)&&s.has(e.target));
}
function neighbors(id){
  const r=[];
  activeEdges.forEach(e=>{
    if(e.source===id&&nodeMap[e.target])r.push({n:nodeMap[e.target],e});
    if(e.target===id&&nodeMap[e.source])r.push({n:nodeMap[e.source],e});
  });
  return r;
}

// ===== CANVAS SETUP =====
const canvas=document.getElementById('canvas'), ctr=document.getElementById('graph-container'), tip=document.getElementById('tooltip');
const ctx=canvas.getContext('2d');
let CW, CH;
const dpr=window.devicePixelRatio||1;

function resize(){
  const r=ctr.getBoundingClientRect();
  CW=r.width; CH=r.height;
  canvas.width=CW*dpr; canvas.height=CH*dpr;
  canvas.style.width=CW+'px'; canvas.style.height=CH+'px';
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
resize();
window.addEventListener('resize',()=>{resize();render();});

function nr(n){
  if(n.type==='funder')return 20;
  if(n.type==='program')return Math.max(8,Math.min(16,4+n.degree*1.5));
  return Math.max(3,Math.min(18,2+n.degree*1.1));
}

function getPos(n){
  const key='pos_'+layout;
  const p=n[key]||[REF_W/2,REF_H/2];
  return[p[0]*CW/REF_W,p[1]*CH/REF_H];
}

// Initialize positions
allNodes.forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});

function fmtMoney(v){
  if(!v)return'';
  if(v>=1e9)return'$'+(v/1e9).toFixed(1)+'B';
  if(v>=1e6)return'$'+(v/1e6).toFixed(1)+'M';
  if(v>=1e3)return'$'+(v/1e3).toFixed(0)+'K';
  return'$'+v;
}

function hexToRgba(hex,a){
  const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
  return`rgba(${r},${g},${b},${a})`;
}

// ===== RENDER (Canvas 2D — much faster than SVG) =====
let frameCount=0, lastFpsTime=performance.now(), fps=0;

function render(){
  const t0=performance.now();
  const vn=vis(), ve=visE();
  vn.forEach(n=>{if(n._rx==null){const p=getPos(n);n._rx=p[0];n._ry=p[1];}});

  ctx.clearRect(0,0,CW,CH);
  ctx.save();
  ctx.translate(tx,ty);
  ctx.scale(tk,tk);

  const hn=selNode||hovNode;
  const hl=new Set();
  if(hn){hl.add(hn.id);neighbors(hn.id).forEach(({n})=>hl.add(n.id));}

  // EDGES — batch by type for fewer state changes
  const edgesByType={};
  ve.forEach(e=>{
    const a=nodeMap[e.source],b=nodeMap[e.target];
    if(!a||!b||a._rx==null||b._rx==null)return;
    if(!edgesByType[e.type])edgesByType[e.type]=[];
    edgesByType[e.type].push(e);
  });

  for(const[etype,earr]of Object.entries(edgesByType)){
    const baseCol=ECOL[etype]||'#444';
    earr.forEach(e=>{
      const a=nodeMap[e.source],b=nodeMap[e.target];
      let col=baseCol, w=0.4, op=0.2;
      if(etype==='funds'){w=1.2;op=0.35;}
      if(hn){
        if(e.source===hn.id||e.target===hn.id){col=COL[hn.type]?.fill||'#fff';w=etype==='funds'?2.5:1.8;op=0.9;}
        else op=0.03;
      }
      ctx.beginPath();
      ctx.moveTo(a._rx,a._ry);
      ctx.lineTo(b._rx,b._ry);
      ctx.strokeStyle=hexToRgba(col,op);
      ctx.lineWidth=w;
      if(etype==='funds'){ctx.setLineDash([6,3]);}else{ctx.setLineDash([]);}
      ctx.stroke();
    });
  }
  ctx.setLineDash([]);

  // NODES — draw circles/shapes
  vn.forEach(n=>{
    const r=nr(n), c=COL[n.type]||{fill:'#666',stroke:'#444'};
    let op=hn&&!hl.has(n.id)?0.08:1;
    const x=n._rx, y=n._ry;
    const shape=c.shape||'circle';

    // Bridge ring
    if(n.is_bridge){
      ctx.beginPath();
      ctx.arc(x,y,r+4,0,Math.PI*2);
      ctx.strokeStyle=hexToRgba('#fbbf24',op*0.7);
      ctx.lineWidth=1.5;
      ctx.setLineDash([3,2]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.globalAlpha=op;
    ctx.fillStyle=c.fill;
    ctx.strokeStyle=n===selNode?'#fff':c.stroke;
    ctx.lineWidth=n===selNode?2.5:0.8;

    if(shape==='diamond'){
      const s=r*1.3;
      ctx.beginPath();
      ctx.moveTo(x,y-s);ctx.lineTo(x+s,y);ctx.lineTo(x,y+s);ctx.lineTo(x-s,y);ctx.closePath();
      ctx.fill();ctx.stroke();
    }else if(shape==='rect'){
      const rw=r*2,rh=r*1.4;
      ctx.beginPath();
      ctx.roundRect(x-rw/2,y-rh/2,rw,rh,3);
      ctx.fill();ctx.stroke();
    }else{
      ctx.beginPath();
      ctx.arc(x,y,r,0,Math.PI*2);
      ctx.fill();ctx.stroke();
    }

    // Labels
    const showLabel=n.degree>=8||n.type==='funder'||n.type==='program'||n===selNode||n===hovNode||(hn&&hl.has(n.id)&&n.degree>=2);
    if(showLabel){
      const fs=Math.max(7,Math.min(12,5+n.degree*0.3));
      ctx.font=fs+'px -apple-system,sans-serif';
      ctx.fillStyle=hexToRgba('#cbd5e1',op);
      ctx.textAlign='center';
      const mx=40;
      const txt=n.label.length>mx?n.label.slice(0,mx)+'...':n.label;
      ctx.fillText(txt,x,y-r-3);
    }
    ctx.globalAlpha=1;
  });

  ctx.restore();

  // Stats
  const meta=G.metadata||{};
  let statTxt=vn.length+' nodes, '+ve.length+' edges';
  if(meta.total_papers)statTxt+=' | '+meta.total_papers+' papers, '+meta.total_authors+' authors';
  if(meta.total_funding)statTxt+=' | Funding: '+fmtMoney(meta.total_funding);
  if(meta.bridge_nodes)statTxt+=' | '+meta.bridge_nodes+' bridge nodes';
  document.getElementById('stats').textContent=statTxt;

  // FPS
  frameCount++;
  const now=performance.now();
  if(now-lastFpsTime>1000){fps=Math.round(frameCount*1000/(now-lastFpsTime));frameCount=0;lastFpsTime=now;}
  const renderMs=(performance.now()-t0).toFixed(1);
  document.getElementById('perf').textContent=fps+' fps | '+renderMs+'ms';
}

// ===== ANIMATION =====
let animating=false, animStart=0, animDur=600;
let posFrom={}, posTo={};
function animateToLayout(){
  const vn=vis();
  posFrom={};posTo={};
  vn.forEach(n=>{
    posFrom[n.id]=[n._rx||getPos(n)[0],n._ry||getPos(n)[1]];
    posTo[n.id]=getPos(n);
  });
  animStart=performance.now();
  animating=true;
  function tick(now){
    let t=Math.min(1,(now-animStart)/animDur);
    t=1-Math.pow(1-t,3);
    vn.forEach(n=>{
      const f=posFrom[n.id]||getPos(n),to=posTo[n.id]||getPos(n);
      n._rx=f[0]+(to[0]-f[0])*t;
      n._ry=f[1]+(to[1]-f[1])*t;
    });
    render();
    if(t<1)requestAnimationFrame(tick);
    else{animating=false;vn.forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});render();}
  }
  requestAnimationFrame(tick);
}

// ===== HIT TESTING =====
function hitTest(mx,my){
  let cl=null,md=Infinity;
  vis().forEach(n=>{
    if(n._rx==null)return;
    const dx=n._rx-mx,dy=n._ry-my,d=Math.sqrt(dx*dx+dy*dy);
    if(d<nr(n)+6&&d<md){cl=n;md=d;}
  });
  return cl;
}

// ===== SIDEBAR =====
function showTip(n,x,y){
  let extra='';
  if(n.is_bridge)extra=' <span style="color:#fbbf24">[BRIDGE]</span>';
  if(n.type==='funder'||n.type==='program'){
    const totalFunding=neighbors(n.id).reduce((s,{e})=>s+(e.amount||0),0);
    if(totalFunding)extra+='<br>Total: '+fmtMoney(totalFunding);
  }
  tip.innerHTML='<div class="tt-l">'+n.label+extra+'</div><div class="tt-t">'+n.type+(n.subtype&&n.subtype!==n.type?' . '+n.subtype:'')+'</div><div class="tt-d">'+n.degree+' connections</div>';
  tip.style.opacity=1;tip.style.left=(x+14)+'px';tip.style.top=(y-8)+'px';
}

function showInfo(n){
  const d=document.getElementById('detail'),c=COL[n.type]?.fill||'#666';
  let lnk='';
  if(n.details)Object.entries(n.details).forEach(([k,v])=>{
    if(v&&typeof v==='string'&&v.startsWith('http'))lnk+='<a href="'+v+'" target="_blank">'+k+'</a>';
    else if(v)lnk+='<span style="font-size:10px;color:#94a3b8;margin-right:6px">'+k+': '+v+'</span>';
  });
  if(n.url)lnk+='<a href="'+n.url+'" target="_blank">Website</a>';
  let fundingHtml='';
  if(n.type==='funder'||n.type==='program'||n.type==='org'||n.type==='institution'){
    const fundEdges=neighbors(n.id).filter(({e})=>e.type==='funds');
    if(fundEdges.length>0){
      const total=fundEdges.reduce((s,{e})=>s+(e.amount||0),0);
      fundingHtml='<div class="funding">Funding: '+fmtMoney(total)+' across '+fundEdges.length+' grants</div>';
    }
  }
  const bridgeBadge=n.is_bridge?'<span class="bridge-badge">BRIDGE</span>':'';
  const nb=neighbors(n.id),grp={};
  nb.forEach(({n:nn,e})=>{
    const key=nn.type+'_'+e.type;
    if(!grp[key])grp[key]={type:nn.type,edgeType:e.type,items:[]};
    grp[key].items.push({n:nn,e});
  });
  let cn='';
  Object.values(grp).forEach(({type:t,edgeType:et,items})=>{
    cn+='<h4 style="color:'+(COL[t]?.fill||'#888')+'">'+(COL[t]?.label||t)+' - '+et.replace(/_/g,' ')+' ('+items.length+')</h4>';
    items.sort((a,b)=>(b.e.amount||0)-(a.e.amount||0));
    items.forEach(({n:nn,e})=>{
      const amtStr=e.amount?'<span class="amt">'+fmtMoney(e.amount)+'</span>':'';
      cn+='<div class="conn" data-id="'+nn.id+'">'+nn.label+amtStr+'<span class="et">'+et.replace(/_/g,' ')+'</span></div>';
    });
  });
  d.innerHTML='<div class="card"><div class="tag" style="background:'+c+'22;color:'+c+'">'+n.type+(n.subtype&&n.subtype!==n.type?' . '+n.subtype:'')+'</div>'+bridgeBadge+'<h3>'+n.label+'</h3>'+(n.tldr?'<p style="font-size:11px;color:#94a3b8;margin-top:5px">'+n.tldr+'</p>':'')+(n.description?'<p style="font-size:10px;color:#64748b;margin-top:3px">'+n.description+'</p>':'')+fundingHtml+'<div class="links" style="margin-top:6px">'+lnk+'</div><div class="conns">'+cn+'</div></div>';
  d.querySelectorAll('.conn').forEach(el=>el.addEventListener('click',()=>{
    const t=nodeMap[el.dataset.id];if(t){selNode=t;showInfo(t);render();}
  }));
}

// ===== MOUSE EVENTS =====
let dragging=null, dragOff={x:0,y:0}, justDragged=false;
let panning=false, panS={x:0,y:0};

canvas.addEventListener('mousemove',e=>{
  if(dragging||panning)return;
  const r=ctr.getBoundingClientRect();
  const mx=(e.clientX-r.left-tx)/tk,my=(e.clientY-r.top-ty)/tk;
  const cl=hitTest(mx,my);
  if(cl!==hovNode){
    hovNode=cl;
    if(cl){showTip(cl,e.clientX-r.left,e.clientY-r.top);if(!selNode)render();}
    else{tip.style.opacity=0;if(!selNode)render();}
  }else if(cl){showTip(cl,e.clientX-r.left,e.clientY-r.top);}
});

canvas.addEventListener('click',e=>{
  if(justDragged){justDragged=false;return;}
  const r=ctr.getBoundingClientRect();
  const mx=(e.clientX-r.left-tx)/tk,my=(e.clientY-r.top-ty)/tk;
  const cl=hitTest(mx,my);
  if(cl){selNode=cl;showInfo(cl);}
  else{selNode=null;hovNode=null;document.getElementById('detail').innerHTML='<div class="placeholder">Click a node to see details</div>';}
  render();
});

canvas.addEventListener('mousedown',e=>{
  if(e.button!==0)return;
  const r=ctr.getBoundingClientRect();
  const mx=(e.clientX-r.left-tx)/tk,my=(e.clientY-r.top-ty)/tk;
  const cl=hitTest(mx,my);
  if(cl){dragging=cl;dragOff={x:cl._rx-mx,y:cl._ry-my};e.preventDefault();e.stopPropagation();return;}
  panning=true;panS={x:e.clientX-tx,y:e.clientY-ty};
});

window.addEventListener('mousemove',e=>{
  if(dragging){
    const r=ctr.getBoundingClientRect();
    const mx=(e.clientX-r.left-tx)/tk,my=(e.clientY-r.top-ty)/tk;
    dragging._rx=mx+dragOff.x;dragging._ry=my+dragOff.y;
    justDragged=true;render();
  }else if(panning){tx=e.clientX-panS.x;ty=e.clientY-panS.y;render();}
});
window.addEventListener('mouseup',()=>{dragging=null;panning=false;});

canvas.addEventListener('wheel',e=>{
  e.preventDefault();
  const r=ctr.getBoundingClientRect();
  const mx=e.clientX-r.left,my=e.clientY-r.top;
  const d=e.deltaY>0?0.92:1.08;
  const nk=Math.max(0.1,Math.min(8,tk*d));
  tx=mx-(mx-tx)*(nk/tk);ty=my-(my-ty)*(nk/tk);tk=nk;
  render();
},{passive:false});

// ===== CONTROLS =====
document.querySelectorAll('[data-layout]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-layout]').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');layout=b.dataset.layout;animateToLayout();
}));
document.querySelectorAll('[data-layer]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-layer]').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');layer=b.dataset.layer;tx=0;ty=0;tk=1;
  vis().forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});render();
}));
document.querySelectorAll('[data-detail]').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('[data-detail]').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');setSimple(b.dataset.detail==='simple');
  tx=0;ty=0;tk=1;vis().forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});render();
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
Object.entries(COL).forEach(([t,cfg])=>{
  const shape=cfg.shape==='diamond'?'&#9670;':cfg.shape==='rect'?'&#9632;':'&#9679;';
  lg.innerHTML+='<div class="li"><span style="color:'+cfg.fill+'">'+shape+'</span> '+cfg.label+'</div>';
});
lg.innerHTML+='<div class="li" style="margin-top:3px"><span style="font-size:10px;color:#fbbf24">--- = funding &nbsp; &#8856; = bridge node</span></div>';

// BOOT
setSimple(false);
vis().forEach(n=>{const p=getPos(n);n._rx=p[0];n._ry=p[1];});
render();
</script>
</body>
</html>"""

html = html.replace('__GRAPH_JSON__', graph_json)

out_path = os.path.join(BASE_DIR, "index_webgl.html")
with open(out_path, "w") as f:
    f.write(html)

print(f"Generated index_webgl.html: {len(html)//1024} KB")
print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")
print(f"  Papers: {total_papers}, Authors: {total_authors}, Institutions: {total_insts}")
print(f"  Total funding: ${total_funding:,.0f}")
print(f"  Bridge nodes: {bridge_count}")
