"""Deterministic graph risk propagation (no ML)."""
from collections import deque, defaultdict

GRAPH_WEIGHTS = {
    "DECAY": 0.5,
    "MAX_HOPS": 2,
    "PATH_DECAY": 0.8,
    "resolves_to": 1.0,
    "cname": 0.9,
    "same_ip": 0.8,
    "same_cert": 0.8,
    "has_vuln": 1.0,
    "has_port": 0.6,
    "high_port_risk": 0.3,
    "medium_port_risk": 0.15,
    "open_port_risk": 0.05,
    "exposed_risk": 0.15,
    "plaintext_risk": 0.1,
    "ssl_expired_risk": 0.2,
    "ssl_self_signed_risk": 0.1,
    "kev_factor": 0.5,
    "port_risk_kev": 1.0,
}
DECAY = GRAPH_WEIGHTS["DECAY"]
MAX_HOPS = GRAPH_WEIGHTS["MAX_HOPS"]
HIGH_PORTS = {21,22,23,25,110,143,445,1433,1521,3306,3389,5432,5900,6379,9200,27017}
MEDIUM_PORTS = {8080,8443,8888}
DEFAULT_CVSS = 0.0
DEFAULT_EPSS = 0.0
DEFAULT_KEV = False

def _num(v, default=0.0):
    try: return float(v) if v is not None else float(default)
    except (TypeError, ValueError): return float(default)

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(v)))

def noisy_or(risks):
    p = 1.0
    for r in risks: p *= 1.0 - clamp(r)
    return clamp(1.0 - p)

# Compatibility aliases
def combine_noisy_or(risks): return noisy_or(risks)

def finding_risk(vuln, intel=None):
    intel = intel or {}
    cvss = _num(vuln.get("cvss", DEFAULT_CVSS), DEFAULT_CVSS)
    epss = _num(vuln.get("epss", intel.get("epss", DEFAULT_EPSS)), DEFAULT_EPSS)
    kev = bool(vuln.get("kev", intel.get("kev", DEFAULT_KEV)))
    raw = (clamp(cvss/10.0)) * (1.0 + GRAPH_WEIGHTS["kev_factor"]*float(kev)) * (0.5 + clamp(epss))
    r = clamp(raw)
    return r, {"cvss": cvss, "epss": epss, "kev": kev, "finding_risk": r}

def _as_list(coll):
    if hasattr(coll, "to_list"):
        return coll.to_list(None)
    return coll  # if already list / mock

async def _fetch(db, collname, query):
    try:
        res = db[collname].find(query) if isinstance(db, dict) else getattr(db, collname).find(query)
        if hasattr(res, "to_list"): return await res.to_list(None)
        return list(res)
    except Exception:
        try:
            res = getattr(db, collname).find(query)
            if hasattr(res, "to_list"): return await res.to_list(None)
            return list(res)
        except Exception:
            return []

def _own_risk(asset, vulns, ports, ssl, intel_by_vid=None):
    intel_by_vid = intel_by_vid or {}
    contrib, explanation = [], []
    for v in vulns:
        r, det = finding_risk(v, intel_by_vid.get(str(v.get("_id","")), {}))
        if r > 0:
            contrib.append(r)
            explanation.append({"type":"vuln","id":str(v.get("_id","")),"cve":v.get("cve"),"cvss":det["cvss"],"epss":det["epss"],"kev":det["kev"],"risk":r,"explanation":f"finding {v.get('cve') or v.get('template_name') or v.get('_id')} cvss={det['cvss']} epss={det['epss']} kev={det['kev']} -> {r:.3f}"})
    for p in ports:
        pn = int(_num(p.get("port"), 0))
        r = GRAPH_WEIGHTS["high_port_risk"] if pn in HIGH_PORTS else GRAPH_WEIGHTS["medium_port_risk"] if pn in MEDIUM_PORTS else GRAPH_WEIGHTS["open_port_risk"]
        contrib.append(r)
        explanation.append({"type":"port","port":pn,"risk":r,"explanation":f"open port {pn} -> {r}"})
    if asset.get("is_live"):
        contrib.append(GRAPH_WEIGHTS["exposed_risk"])
        explanation.append({"type":"exposure","risk":GRAPH_WEIGHTS["exposed_risk"],"explanation":"internet-exposed live asset"})
        if not asset.get("https_enabled"):
            contrib.append(GRAPH_WEIGHTS["plaintext_risk"])
            explanation.append({"type":"plaintext","risk":GRAPH_WEIGHTS["plaintext_risk"],"explanation":"live asset without https"})
    if ssl:
        if ssl.get("expired"):
            contrib.append(GRAPH_WEIGHTS["ssl_expired_risk"]); explanation.append({"type":"ssl","risk":GRAPH_WEIGHTS["ssl_expired_risk"],"explanation":"expired ssl cert"})
        if ssl.get("self_signed"):
            contrib.append(GRAPH_WEIGHTS["ssl_self_signed_risk"]); explanation.append({"type":"ssl","risk":GRAPH_WEIGHTS["ssl_self_signed_risk"],"explanation":"self-signed ssl cert"})
    if asset.get("risk_score") is not None:
        r0 = clamp(_num(asset.get("risk_score"),0)/100.0)
        # blend stored score as one contribution if no vuln/port yet, else include
        contrib.append(r0); explanation.append({"type":"stored_risk_score","risk":r0,"explanation":f"stored risk_score {asset.get('risk_score')} -> {r0:.3f}"})
    own = noisy_or(contrib) if contrib else 0.0
    # If stored score present and no other signals, own is r0; noisy_or already handles
    return own, explanation

async def build_graph(db, project_id):
    assets = await _fetch(db, "assets", {"project_id": str(project_id)})
    ports = await _fetch(db, "ports", {"project_id": str(project_id), "state": "open"})
    vulns = await _fetch(db, "vulnerabilities", {"project_id": str(project_id)})
    ssls = await _fetch(db, "ssl_analysis", {"project_id": str(project_id)})
    dns = await _fetch(db, "dns_records", {"project_id": str(project_id)})
    intel = await _fetch(db, "threat_intelligence", {"project_id": str(project_id)})
    intel_by_vid = {str(d.get("vulnerability_id","")): d for d in intel if d.get("vulnerability_id")}
    nodes, edges, adj = {}, [], defaultdict(list)
    def add_node(nid, ntype, label, asset_id, extra=None):
        if nid not in nodes: nodes[nid] = {"id":nid,"type":ntype,"label":label,"asset_id":asset_id,"explanation":[f"{ntype} node {label}"]}
        if extra: nodes[nid].update(extra)
    def add_edge(src, dst, etype, expl):
        w = GRAPH_WEIGHTS.get(etype, 1.0)
        e = {"source":src,"target":dst,"type":etype,"weight":w,"explanation":[expl]}
        edges.append(e); adj[src].append(e); adj[dst].append({"source":dst,"target":src,"type":etype,"weight":w,"explanation":[expl],"via":src})
        return e
    asset_by_id, asset_by_host = {}, {}
    for a in assets:
        aid = str(a.get("_id","")); asset_by_id[aid]=a; h=(a.get("hostname") or "").lower()
        if h: asset_by_host[h]=a
        add_node(f"asset:{aid}","asset",a.get("hostname") or aid,aid)
    # IP edges
    ip_to_assets = defaultdict(list)
    for a in assets:
        aid=str(a.get("_id","")); ip=a.get("ip") or a.get("ip_address") or a.get("address")
        if ip:
            add_node(f"ip:{ip}","ip",str(ip),aid); add_edge(f"asset:{aid}",f"ip:{ip}","resolves_to",f"asset {a.get('hostname') or aid} resolves_to {ip}")
            ip_to_assets[str(ip)].append(aid)
    for ip, aids in ip_to_assets.items():
        for i in range(len(aids)):
            for j in range(i+1,len(aids)):
                add_edge(f"asset:{aids[i]}",f"asset:{aids[j]}","same_ip",f"share ip {ip}")
    # CNAME
    for d in dns:
        if str(d.get("record_type","")).upper()!="CNAME": continue
        aid=str(d.get("asset_id","") or "")
        if aid not in asset_by_id: continue
        target=str(d.get("record_value","") or "").rstrip(".").lower()
        if target in asset_by_host:
            tid=str(asset_by_host[target].get("_id",""))
            add_edge(f"asset:{aid}",f"asset:{tid}","cname",f"CNAME {d.get('hostname')} -> {target}")
    # SSL certs
    cert_to_assets = defaultdict(list)
    for s in ssls:
        fp=str(s.get("fingerprint") or s.get("certificate_fingerprint") or s.get("sha256") or "")
        if not fp: continue
        aid=str(s.get("asset_id","") or "")
        if aid not in asset_by_id: continue
        add_node(f"cert:{fp}","cert",fp,aid); cert_to_assets[fp].append(aid)
    for fp, aids in cert_to_assets.items():
        for i in range(len(aids)):
            for j in range(i+1,len(aids)):
                add_edge(f"asset:{aids[i]}",f"asset:{aids[j]}","same_cert",f"share cert fingerprint {fp[:12]}")
    # ports & vulns
    for p in ports:
        aid=str(p.get("asset_id","") or "")
        if aid not in asset_by_id: continue
        pid=f"port:{aid}:{p.get('port')}:{p.get('protocol','')}"
        add_node(pid,"port",f"{p.get('port')}/{p.get('protocol','')}",aid); add_edge(f"asset:{aid}",pid,"has_port",f"asset has open port {p.get('port')}")
    for v in vulns:
        aid=str(v.get("asset_id","") or "")
        if aid not in asset_by_id: continue
        vid=f"vuln:{v.get('_id','')}"
        add_node(vid,"vuln",v.get("cve") or v.get("template_name") or str(v.get("_id","")),aid); add_edge(f"asset:{aid}",vid,"has_vuln",f"asset has vuln {v.get('cve') or v.get('template_name') or ''}")
    # own risks
    vuln_by_asset=defaultdict(list); port_by_asset=defaultdict(list); ssl_by_asset={}
    for v in vulns: vuln_by_asset[str(v.get("asset_id","") or "")].append(v)
    for p in ports: port_by_asset[str(p.get("asset_id","") or "")].append(p)
    for s in ssls: ssl_by_asset[str(s.get("asset_id","") or "")]=s
    asset_risk, asset_expl = {}, {}
    for aid,a in asset_by_id.items():
        own, expl = _own_risk(a, vuln_by_asset[aid], port_by_asset[aid], ssl_by_asset.get(aid), intel_by_vid)
        asset_risk[aid]=own; asset_expl[aid]=expl
        nodes[f"asset:{aid}"]["risk"]=own; nodes[f"asset:{aid}"]["explanation"]=expl
    return {"nodes": list(nodes.values()), "node_map": nodes, "edges": edges, "adjacency": dict(adj), "asset_risk": asset_risk, "asset_explanation": asset_expl, "assets": assets, "explanation": ["graph built with noisy-OR, decay 0.5, max 2 hops"]}

def propagated_risk(graph, asset_id, max_hops=GRAPH_WEIGHTS["MAX_HOPS"]):
    # propagation helper: noisy-OR of own + neighbour decayed
    adj = graph.get("adjacency", {})
    asset_risk = graph.get("asset_risk", {})
    own = clamp(asset_risk.get(str(asset_id), 0.0))
    contribs=[own]; explanation=[{"type":"own","asset_id":str(asset_id),"risk":own,"explanation":f"own risk {own:.3f}"}]
    start=f"asset:{asset_id}"
    visited={start:0}; q=deque([(start,0,1.0)])
    while q:
        node, hop, path_weight = q.popleft()
        if hop>=max_hops: continue
        for e in adj.get(node, []):
            nb=e["target"]; nh=hop+1
            if visited.get(nb, 99)<=nh: continue
            visited[nb]=nh
            nb_asset = nb.split(":",1)[1] if nb.startswith("asset:") else None
            nr = asset_risk.get(nb_asset, 0.0) if nb_asset else nodes_risk(graph, nb)
            decayed = clamp(nr * (GRAPH_WEIGHTS["DECAY"]**nh) * e.get("weight",1.0))
            contribs.append(decayed)
            explanation.append({"type":"neighbour","hop":nh,"node":nb,"edge":e.get("type"),"neighbour_risk":nr,"decayed_risk":decayed,"explanation":f"hop {nh} via {e.get('type')} decayed {decayed:.3f}"})
            q.append((nb,nh,path_weight))
    return noisy_or(contribs), explanation

def nodes_risk(graph, nid):
    nm=graph.get("node_map",{})
    n=nm.get(nid, {})
    if "risk" in n: return clamp(n["risk"])
    # vuln node risk
    if n.get("type")=="vuln":
        return 0.3
    return 0.0

async def get_graph_risk(db, project_id):
    g = await build_graph(db, project_id)
    out=[]
    for a in g["assets"]:
        aid=str(a.get("_id",""))
        pr, expl = propagated_risk(g, aid)
        out.append({"asset_id":aid,"hostname":a.get("hostname"),"own_risk":g["asset_risk"].get(aid,0.0),"propagated_risk":pr,"explanation":expl})
    return {"project_id":str(project_id),"nodes":g["nodes"],"edges":g["edges"],"assets":out,"explanation":g["explanation"]}

async def attack_paths(db, project_id, limit=10):
    g = await build_graph(db, project_id)
    adj=g["adjacency"]; asset_risk=g["asset_risk"]; assets=g["assets"]
    by_id={str(a.get("_id","")):a for a in assets}
    starts=[a for a in assets if a.get("is_live")]
    # target predicate
    max_risk=max(asset_risk.values()) if asset_risk else 0
    def is_target(a):
        return _num(a.get("criticality"),0)>=4 or asset_risk.get(str(a.get("_id","")),0)==max_risk and max_risk>0
    paths=[]
    for s in starts:
        sid=str(s.get("_id","")); start=f"asset:{sid}"
        q=deque([(start,[start],[])])
        while q:
            node, path, edge_types = q.popleft()
            if len(edge_types)>3: continue
            if node!=start and node.startswith("asset:"):
                aid=node.split(":",1)[1]
                if is_target(by_id.get(aid,{})):
                    # build explanation per node
                    node_risks=[]; expl=[]
                    prev=None
                    for n in path:
                        if n.startswith("asset:"):
                            r=asset_risk.get(n.split(":",1)[1],0.0)
                        else:
                            r=nodes_risk(g,n)
                        node_risks.append(r)
                        expl.append({"node":n,"risk":r,"explanation":f"node {n} risk {r:.3f}" + (f" via {edge_types[path.index(n)-1]}" if path.index(n)>0 and prev else "")})
                        prev=n
                    score = noisy_or(node_risks) * (GRAPH_WEIGHTS["PATH_DECAY"]**len(edge_types))
                    paths.append({"path":path,"edges":edge_types,"score":clamp(score),"explanation":expl})
                    continue  # don't extend past target
            if len(edge_types)>=3: continue
            for e in adj.get(node, []):
                nb=e["target"]
                if nb in path: continue
                # only traverse asset neighbours for paths beyond first hop to keep concise, but allow vuln/port leaves? BFS over asset graph mainly.
                q.append((nb,path+[nb],edge_types+[e.get("type")]))
    paths.sort(key=lambda x: x["score"], reverse=True)
    return {"project_id":str(project_id),"paths":paths[:limit],"explanation":["BFS depth<=3 from exposed live assets, score=noisy-OR(node risks)*0.8^edges"]}
