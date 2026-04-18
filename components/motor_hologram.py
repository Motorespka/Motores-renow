"""
Holograma: GLB via <model-viewer> quando houver URL resolvida.
Na listagem (consulta): http(s) inclui Supabase e pack /app/static/glb/ no Streamlit Cloud;
data: so com HOLOGRAM_LIST_SHOW_GLB=1. HOLOGRAM_LIST_NO_STATIC_GLB=1 esconde pack na lista.
HOLOGRAM_LIST_NO_GLB=1 força só silhueta na lista.

Na consulta, a silhueta generica fica **desligada** por defeito; `HOLOGRAM_LISTA_SILHUETA_TODOS=1` volta
ao bloco de silhueta em todos. `HOLOGRAM_CARCACA_NEMA56_STRICT=1` controla a cadeia de resolucao GLB.
"""

from __future__ import annotations

import html
import json
import os
import re
from typing import Any, Dict

import streamlit as st

from utils.motor_hologram import hologram_choice_label, resolve_hologram_preset
from utils.motor_hologram_glb import (
    NEMA_56_CARCACA_LEGENDA_COMPLETA,
    consulta_lista_somente_familia_56_activa,
    hologram_carcaca_context,
    hologram_nema56_glb_secret_configurado,
    mecanica_nema56_modo_restrito,
    motor_has_hologram_motor_id_secret,
    motor_has_json_hologram_glb_url,
    nema_56_somente_ficha_mecanica,
    resolve_model_glb_url,
)

# Three.js (ESM) — malha procedural aproximada; nao substitui CAD nem GLB tecnico.
_THREE_IMPORTMAP = """
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.168.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.168.0/examples/jsm/"
  }
}
</script>
"""

_THREE_MAIN = """
<script type="module">
const HOLO_CTX = JSON.parse(document.getElementById('holo-ctx-json').textContent);
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const preset = HOLO_CTX.preset || 'generico';
const car = String(HOLO_CTX.carcaca || '');
const carU = car.toUpperCase();
const isNema48 = /NEMA\\s*[-_]?\\s*48\\b/i.test(car) || (carU.includes('NEMA') && carU.includes('48'));
const isNemaFamily = preset === 'nema_mono' || carU.includes('NEMA');

function wf(color) {
  return new THREE.MeshBasicMaterial({
    color,
    wireframe: true,
    transparent: true,
    opacity: 0.93,
  });
}

function buildMotor() {
  const g = new THREE.Group();
  const sh = new THREE.Mesh(new THREE.CylinderGeometry(0.038, 0.038, 0.26, 12, 1), wf(0x7dd3fc));
  sh.rotation.z = Math.PI / 2;
  sh.position.set(-0.2, 0, 0);
  g.add(sh);

  let r = 0.125;
  let len = 0.34;
  if (isNema48) {
    r = 0.092;
    len = 0.19;
  } else if (isNemaFamily) {
    r = 0.105;
    len = 0.26;
  }
  if (preset === 'trif_grande') {
    r = 0.16;
    len = 0.48;
  }
  if (preset === 'servo_compacto') {
    r = 0.088;
    len = 0.15;
  }

  const bodyGeo = new THREE.CylinderGeometry(r, r, len, 26, 1);
  bodyGeo.rotateZ(Math.PI / 2);
  const body = new THREE.Mesh(bodyGeo, wf(0x5eead4));
  body.position.set(0.04, 0, 0);
  g.add(body);

  const ribDense = preset === 'iec_w22' || preset === 'ip55_iso';
  const ribCount = ribDense ? 8 : 5;
  const span = len * 0.82;
  for (let i = 0; i < ribCount; i++) {
    const t = new THREE.Mesh(new THREE.TorusGeometry(r + 0.006, 0.011, 5, 28), wf(0x22d3ee));
    t.rotation.y = Math.PI / 2;
    const u = ribCount <= 1 ? 0.5 : i / (ribCount - 1);
    t.position.x = 0.04 - span / 2 + u * span;
    g.add(t);
  }

  const bellR = r * 1.02;
  for (const sx of [-len * 0.48 + 0.04, len * 0.48 + 0.04]) {
    const disc = new THREE.Mesh(
      new THREE.CylinderGeometry(bellR * 0.9, bellR * 0.9, 0.042, 18, 1),
      wf(0x67e8f9),
    );
    disc.rotation.z = Math.PI / 2;
    disc.position.set(sx, 0, 0);
    g.add(disc);
  }

  if (isNema48 || preset === 'nema_mono') {
    const cap = new THREE.Mesh(new THREE.BoxGeometry(r * 1.25, 0.075, r * 0.95), wf(0xfbbf24));
    cap.position.set(0.04, r + 0.048, 0);
    g.add(cap);
  }

  if (isNema48 || isNemaFamily) {
    for (const z of [-r * 0.52, r * 0.52]) {
      const foot = new THREE.Mesh(new THREE.BoxGeometry(len * 0.52, 0.022, 0.075), wf(0x5eead4));
      foot.position.set(0.04, -r - 0.018, z);
      g.add(foot);
    }
  }

  const ring = new THREE.Mesh(new THREE.RingGeometry(0.32, 0.4, 36), wf(0x22d3ee));
  ring.rotation.x = -Math.PI / 2;
  ring.position.set(0.04, -r - 0.075, 0);
  g.add(ring);

  return g;
}

function main() {
  const root = document.getElementById('three-holo-root');
  if (!root) return;
  const w0 = Math.max(120, root.clientWidth || 300);
  const h0 = 200;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, w0 / h0, 0.06, 24);
  camera.position.set(0.52, 0.2, 0.58);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(w0, h0);
  renderer.setClearColor(0x000000, 0);
  root.appendChild(renderer.domElement);

  const group = buildMotor();
  scene.add(group);

  const amb = new THREE.AmbientLight(0xa5f3fc, 0.35);
  scene.add(amb);
  const pt = new THREE.PointLight(0x67e8f9, 1.1, 8);
  pt.position.set(1.2, 0.8, 0.6);
  scene.add(pt);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 0, 0);
  controls.maxPolarAngle = Math.PI * 0.55;
  controls.minDistance = 0.35;
  controls.maxDistance = 1.8;

  const ro = new ResizeObserver(() => {
    const r = root.getBoundingClientRect();
    const nw = Math.max(120, r.width);
    const nh = 200;
    camera.aspect = nw / nh;
    camera.updateProjectionMatrix();
    renderer.setSize(nw, nh);
  });
  ro.observe(root);

  let t0 = performance.now();
  function tick(t) {
    const dt = (t - t0) * 0.001;
    t0 = t;
    group.rotation.y += 0.15 * dt;
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

main();
</script>
"""


def _glb_url_ok_for_list_remote_viewer(url: str) -> bool:
    """
    Na consulta, usar model-viewer para http(s), incl. pack em /app/static/glb/ no Cloud.
    data: (base64 embutido) fica de fora salvo HOLOGRAM_LIST_SHOW_GLB=1 (muitos cards esgotam GPU).
    Para voltar a esconder o pack na lista: HOLOGRAM_LIST_NO_STATIC_GLB=1.
    """
    u = (url or "").strip().lower()
    if not u.startswith(("http://", "https://")):
        return False
    if "/app/static/glb/" in u and _flag_truthy("HOLOGRAM_LIST_NO_STATIC_GLB"):
        return False
    return True


def _flag_truthy(name: str) -> bool:
    raw = str(os.environ.get(name, "") or "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    try:
        sec = str(st.secrets.get(name, "") or "").strip().lower()
        return sec in ("1", "true", "yes", "on")
    except Exception:
        return False


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(x).strip() for x in value if str(x).strip())
    return str(value).strip()


def _fins_html(count: int) -> str:
    return "".join('<i class="holo-fin"></i>' for _ in range(max(4, min(count, 14))))


def _preset_fins_count(preset: str) -> int:
    return {
        "ip55_iso": 10,
        "ip21_aberto": 5,
        "nema_mono": 6,
        "iec_w22": 12,
        "trif_grande": 13,
        "servo_compacto": 7,
        "generico": 8,
    }.get(preset, 8)


def _host_id(key: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", key or "motor")[:48]
    return f"holoeng_{safe}"


def _build_model_viewer_html(
    preset: str,
    glb_url: str,
    rpm: str,
    tensao: str,
    corrente: str,
    plabel: str,
    *,
    compact: bool = False,
) -> str:
    src = json.dumps(glb_url)
    mv_h = 160 if compact else 240
    hint_block = (
        ""
        if compact
        else '<div class="hint">Malha 3D com camada holográfica (scanline + brilho). Gire com o rato ou um dedo.</div>'
    )
    return f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script type="module" src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js"></script>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: system-ui, sans-serif; background: transparent; color:#b8e6ff; }}
  .wrap {{
    border:1px solid rgba(34,211,238,0.38);
    border-radius:14px;
    overflow:hidden;
    background: linear-gradient(165deg, rgba(6,12,22,0.98), rgba(4,10,18,0.96));
  }}
  .head {{
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 10px; font-size:10px; letter-spacing:0.14em; color:#67e8f9;
    border-bottom:1px solid rgba(34,211,238,0.2);
  }}
  .hint {{ font-size:9px; color:#7dd3fc; opacity:0.88; padding:6px 10px 4px; line-height:1.35; }}
  .mv-holo {{
    position: relative;
    width: 100%;
    height: {mv_h}px;
    overflow: hidden;
    background: radial-gradient(ellipse 80% 70% at 50% 38%, rgba(34,211,238,0.14), rgba(2,10,22,0.98));
  }}
  .mv-holo model-viewer {{
    position: relative;
    z-index: 2;
    width: 100%;
    height: 100%;
    --poster-color: transparent;
    filter: contrast(1.12) saturate(0.92) brightness(1.06)
      drop-shadow(0 0 18px rgba(34,211,238,0.42));
  }}
  .mv-holo::before {{
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 1;
    border-radius: 0;
    box-shadow: inset 0 0 32px rgba(6,182,212,0.18), inset 0 0 2px rgba(103,232,249,0.35);
  }}
  .mv-holo::after {{
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 3;
    background:
      repeating-linear-gradient(0deg, transparent 0 3px, rgba(34,211,238,0.05) 3px 4px),
      linear-gradient(115deg, rgba(125,252,255,0.07) 0%, transparent 45%, rgba(34,211,238,0.05) 100%);
    mix-blend-mode: soft-light;
    opacity: 0.95;
  }}
  .kpis {{
    display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; padding:8px 10px 10px;
  }}
  .kpi {{
    font-size:10px; padding:5px 8px; border-radius:8px;
    border:1px solid rgba(34,211,238,0.32); background: rgba(6,50,70,0.35); color:#a5f3fc;
  }}
  .kpi b {{ color:#ecfeff; font-weight:700; }}
</style></head>
<body>
  <div class="wrap holo-glb--{html.escape(preset)}">
    <div class="head">
      <span>HOLOGRAMA · GLB</span>
      <span>{plabel}</span>
    </div>
    {hint_block}
    <div class="mv-holo">
    <model-viewer
      src={src}
      alt="Motor 3D"
      camera-controls
      touch-action="pan-y"
      shadow-intensity="0.35"
      exposure="0.72"
      interaction-prompt="none"
    ></model-viewer>
    </div>
    <div class="kpis">
      <div class="kpi">RPM <b>{rpm}</b></div>
      <div class="kpi">V <b>{tensao}</b></div>
      <div class="kpi">A <b>{corrente}</b></div>
    </div>
  </div>
</body></html>
"""


def _build_threejs_procedural_html(
    preset: str,
    rpm: str,
    tensao: str,
    corrente: str,
    plabel: str,
    hid_attr: str,
    hid_plain: str,
    carcaca_raw: str,
    hint_suffix: str = "",
) -> str:
    ctx = {"preset": preset, "carcaca": carcaca_raw}
    ctx_json = json.dumps(ctx, ensure_ascii=False).replace("</", "<\\/")
    three_block = _THREE_IMPORTMAP + (
        f'<script type="application/json" id="holo-ctx-json">{ctx_json}</script>' + _THREE_MAIN
    )
    return f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: system-ui, sans-serif; background: transparent; color:#b8e6ff; }}
  .wrap {{
    border:1px solid rgba(34,211,238,0.38);
    border-radius:14px;
    overflow:hidden;
    background: linear-gradient(165deg, rgba(6,12,22,0.98), rgba(4,10,18,0.96));
    box-shadow: inset 0 0 24px rgba(34,211,238,0.08);
  }}
  .head {{
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 10px; font-size:10px; letter-spacing:0.14em; color:#67e8f9;
    border-bottom:1px solid rgba(34,211,238,0.2);
  }}
  .three-stage {{
    position:relative;
    min-height:200px;
    background:
      radial-gradient(circle at 22% 18%, rgba(34,211,238,0.14), transparent 42%),
      repeating-linear-gradient(0deg, rgba(34,211,238,0.05) 0 1px, transparent 1px 8px);
  }}
  .three-stage::after {{
    content:"";
    position:absolute; inset:0; pointer-events:none; z-index:1;
    background: repeating-linear-gradient(0deg, transparent 0 3px, rgba(34,211,238,0.04) 3px 4px);
    mix-blend-mode: soft-light;
  }}
  #three-holo-root {{ position:relative; z-index:2; width:100%; height:200px; }}
  .kpis {{
    display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; padding:8px 10px 10px;
  }}
  .kpi {{
    font-size:10px; padding:5px 8px; border-radius:8px;
    border:1px solid rgba(34,211,238,0.32); background: rgba(6,50,70,0.35); color:#a5f3fc;
  }}
  .kpi b {{ color:#ecfeff; font-weight:700; }}
  .hint {{ font-size:9px; color:#7dd3fc; opacity:0.82; padding:6px 10px 4px; line-height:1.35; }}
</style></head>
<body>
  <div class="wrap holo-preset--{html.escape(preset)}" id="{hid_attr}">
    <div class="head">
      <span>HOLOGRAMA · THREE.JS</span>
      <span>{plabel}</span>
    </div>
    <div class="hint">
      Malha procedural aproximada no browser (Three.js): nao e modelo CAD nem desenho de fabrica.
      Com URL de .glb real no cadastro, substitui por malha tecnica. Orbita: arraste; zoom: roda.
      {html.escape(hint_suffix) if hint_suffix else ""}
    </div>
    <div class="three-stage" data-host="{hid_attr}">
      <div id="three-holo-root"></div>
    </div>
    <div class="kpis">
      <div class="kpi">RPM <b>{rpm}</b></div>
      <div class="kpi">V <b>{tensao}</b></div>
      <div class="kpi">A <b>{corrente}</b></div>
    </div>
  </div>
  {three_block}
</body></html>
"""


def _build_css_fallback_html_legacy(
    preset: str,
    fins_n: str,
    rpm: str,
    tensao: str,
    corrente: str,
    plabel: str,
    hid_attr: str,
    hid_plain: str,
) -> str:
    return f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: system-ui, sans-serif; background: transparent; color:#b8e6ff; }}
  .wrap {{
    border:1px solid rgba(34,211,238,0.38);
    border-radius:14px;
    overflow:hidden;
    background: linear-gradient(165deg, rgba(6,12,22,0.98), rgba(4,10,18,0.96));
    box-shadow: inset 0 0 24px rgba(34,211,238,0.08);
  }}
  .head {{
    display:flex; justify-content:space-between; align-items:center;
    padding:8px 10px; font-size:10px; letter-spacing:0.14em; color:#67e8f9;
    border-bottom:1px solid rgba(34,211,238,0.2);
  }}
  .stage {{
    position:relative; height:168px; cursor: grab; touch-action:none;
    background:
      radial-gradient(circle at 20% 20%, rgba(34,211,238,0.12), transparent 45%),
      repeating-linear-gradient(0deg, rgba(34,211,238,0.05) 0 1px, transparent 1px 8px);
  }}
  .stage:active {{ cursor: grabbing; }}
  .grid {{
    position:absolute; inset:0; opacity:0.2;
    background: linear-gradient(90deg, rgba(34,211,238,0.08) 1px, transparent 1px);
    background-size: 22px 22px;
  }}
  .shadow {{
    position:absolute; left:50%; bottom:18px; transform:translateX(-50%);
    width:160px; height:18px; border-radius:50%;
    background: radial-gradient(ellipse, rgba(6,182,212,0.45), transparent 70%);
    filter: blur(4px);
  }}
  .scene {{
    position:absolute; left:50%; top:52%; width:200px; height:80px;
    margin-left:-100px; margin-top:-40px;
    transform-style: preserve-3d;
    transform: perspective(640px) rotateX(8deg) rotateY(-22deg);
  }}
  .motor {{ position:relative; width:100%; height:100%; }}
  .shaft {{
    position:absolute; left:-14px; top:34px; width:36px; height:12px;
    border-radius:6px; border:1px solid rgba(125,252,255,0.85);
    background: linear-gradient(90deg, rgba(125,252,255,0.55), rgba(8,80,120,0.2));
    box-shadow: 0 0 10px rgba(34,211,238,0.4);
  }}
  .body {{
    position:absolute; left:26px; top:14px; width:132px; height:52px;
    border-radius:26px; border:1px solid rgba(103,232,249,0.9);
    background: linear-gradient(180deg, rgba(34,211,238,0.28), rgba(8,60,90,0.15));
    box-shadow: inset 0 0 14px rgba(125,252,255,0.2), 0 0 14px rgba(34,211,238,0.25);
  }}
  .fins {{ position:absolute; inset:9px 12px; display:flex; gap:4px; }}
  .holo-fin {{
    flex:1; border-radius:999px;
    background: linear-gradient(180deg, rgba(103,232,249,0.55), rgba(12,74,110,0.1));
    box-shadow: 0 0 6px rgba(34,211,238,0.35);
    opacity:0.82;
  }}
  .endf, .endb {{
    position:absolute; top:15px; width:40px; height:48px; border-radius:50%;
    border:1px solid rgba(103,232,249,0.88);
    background: radial-gradient(circle at 35% 35%, rgba(125,252,255,0.35), rgba(8,40,60,0.25));
  }}
  .endf {{ left:4px; }}
  .endb {{ left:146px; opacity:0.92; }}
  .jbox {{
    position:absolute; left:78px; top:-8px; width:52px; height:22px;
    border-radius:6px; border:1px solid rgba(103,232,249,0.85);
    background: linear-gradient(180deg, rgba(125,252,255,0.3), rgba(6,60,80,0.2));
  }}
  .cap {{
    position:absolute; left:142px; top:-6px; width:26px; height:16px;
    border-radius:8px; border:1px solid rgba(250,204,21,0.7);
    background: linear-gradient(180deg, rgba(250,204,21,0.35), rgba(80,60,10,0.2));
  }}
  .kpis {{
    display:grid; grid-template-columns: repeat(3, 1fr); gap:6px; padding:8px 10px 10px;
  }}
  .kpi {{
    font-size:10px; padding:5px 8px; border-radius:8px;
    border:1px solid rgba(34,211,238,0.32); background: rgba(6,50,70,0.35); color:#a5f3fc;
  }}
  .kpi b {{ color:#ecfeff; font-weight:700; }}
  .hint {{ font-size:9px; color:#7dd3fc; opacity:0.75; padding:0 10px 8px; }}
  .holo-preset--ip55_iso .body {{ border-color: rgba(34,211,238,1); box-shadow: inset 0 0 18px rgba(125,252,255,0.35), 0 0 20px rgba(34,211,238,0.45); }}
  .holo-preset--ip21_aberto .body {{ border-style: dashed; opacity: 0.88; filter: saturate(0.85); }}
  .holo-preset--nema_mono .scene {{ transform: perspective(640px) rotateX(10deg) rotateY(-18deg) scale(0.92); }}
  .holo-preset--iec_w22 .holo-fin {{ opacity: 0.95; }}
  .holo-preset--trif_grande .body {{ width:148px; height:58px; top:10px; border-radius:29px; }}
  .holo-preset--servo_compacto .body {{ width:118px; height:46px; border-radius:12px; left:36px; }}
  .holo-preset--servo_compacto .endb {{ left: 132px; }}
</style></head>
<body>
  <div class="wrap holo-preset--{html.escape(preset)}" id="{hid_attr}">
    <div class="head">
      <span>HOLOGRAMA · SILHUETA</span>
      <span>{plabel}</span>
    </div>
    <div class="hint">Silhueta (sem WebGL) na consulta. NEMA 56: so ficha
      (Mecânica, quadro) — {html.escape(NEMA_56_CARCACA_LEGENDA_COMPLETA)}. GLB: JSON/Detalhes/viewer 3D.</div>
    <div class="stage" data-host="{hid_attr}">
      <div class="grid"></div>
      <div class="shadow"></div>
      <div class="scene">
        <div class="motor">
          <div class="endf"></div>
          <div class="shaft"></div>
          <div class="body">
            <div class="fins">{fins_n}</div>
          </div>
          <div class="endb"></div>
          <div class="jbox"></div>
          {"<div class='cap'></div>" if preset in ("nema_mono", "ip21_aberto") else ""}
        </div>
      </div>
    </div>
    <div class="kpis">
      <div class="kpi">RPM <b>{rpm}</b></div>
      <div class="kpi">V <b>{tensao}</b></div>
      <div class="kpi">A <b>{corrente}</b></div>
    </div>
  </div>
  <script>
    (function() {{
      const host = document.getElementById({json.dumps(hid_plain)});
      if (!host) return;
      const stage = host.querySelector('.stage');
      const scene = host.querySelector('.scene');
      if (!stage || !scene) return;
      let rx = 8, ry = -22, drag = false, lx = 0, ly = 0;
      function apply() {{
        scene.style.transform = 'perspective(640px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg)';
      }}
      apply();
      stage.addEventListener('pointerdown', function(e) {{
        drag = true; lx = e.clientX; ly = e.clientY;
        try {{ stage.setPointerCapture(e.pointerId); }} catch(_) {{}}
      }});
      stage.addEventListener('pointermove', function(e) {{
        if (!drag) return;
        ry += (e.clientX - lx) * 0.45;
        rx += (e.clientY - ly) * 0.28;
        lx = e.clientX; ly = e.clientY;
        rx = Math.max(-35, Math.min(40, rx));
        apply();
      }});
      function end() {{ drag = false; }}
      stage.addEventListener('pointerup', end);
      stage.addEventListener('pointercancel', end);
    }})();
  </script>
</body></html>
"""


def render_engine_hologram(
    m: Dict[str, Any],
    key: str = "",
    *,
    list_mode: bool = False,
) -> None:
    preset = resolve_hologram_preset(m)
    glb_url = resolve_model_glb_url(m, preset)
    if mecanica_nema56_modo_restrito() and not glb_url and not motor_has_json_hologram_glb_url(m):
        if nema_56_somente_ficha_mecanica(m):
            st.caption(
                "Holograma 3D: NEMA 56 (ficha) sem URL. Use `holograma_glb_url` no JSON, o secret `HOLOGRAM_GLB_NEMA56`, "
                "ou o GLB predefinido no repositorio (ou `HOLOGRAM_BAKED_NEMA56_GLB=0` se o desligou a proposito)."
            )
        else:
            st.caption(
                "Holograma 3D: modo restrito. Familia NEMA 56 (Mecânica) ou `holograma_glb_url` / "
                "`HOLOGRAM_GLB_MOTOR_<id>`. Fora de 56, sem placeholder genérico."
            )
        return

    lista_56 = consulta_lista_somente_familia_56_activa()
    if list_mode and lista_56:
        if not (
            nema_56_somente_ficha_mecanica(m)
            or motor_has_json_hologram_glb_url(m)
            or motor_has_hologram_motor_id_secret(m)
        ):
            st.caption(
                f"3D: {NEMA_56_CARCACA_LEGENDA_COMPLETA} (Mecânica / quadro) — "
                "ou GLB no JSON / `HOLOGRAM_GLB_MOTOR_<id>`."
            )
            return

    fins_n = _fins_html(_preset_fins_count(preset))
    rpm = html.escape(_to_text(m.get("rpm")) or "-")
    tensao = html.escape(_to_text(m.get("tensao")) or "-")
    corrente = html.escape(_to_text(m.get("corrente")) or "-")
    plabel = html.escape(hologram_choice_label(preset))
    hid_plain = _host_id(key)
    hid_attr = html.escape(hid_plain)

    # Varias instancias de model-viewer (WebGL) na mesma pagina esgotam contextos GPU → modelo some.
    force_list_glb = _flag_truthy("HOLOGRAM_LIST_SHOW_GLB")
    no_list_glb = _flag_truthy("HOLOGRAM_LIST_NO_GLB")
    json_list_glb = motor_has_json_hologram_glb_url(m)
    remote_list_glb = _glb_url_ok_for_list_remote_viewer(glb_url or "")
    use_model_viewer = bool(glb_url) and (
        not list_mode
        or (
            not no_list_glb
            and (force_list_glb or json_list_glb or remote_list_glb)
        )
    )

    # Three.js tambem usa WebGL: N iframes na consulta esgotam contextos (ecra branco / vazio).
    force_list_three = _flag_truthy("HOLOGRAM_LIST_THREEJS")
    list_glb_hint = ""
    if list_mode and glb_url and not use_model_viewer:
        list_glb_hint = (
            " Malha GLB: Abrir Detalhes; HOLOGRAM_LIST_SHOW_GLB=1 força GLB na lista (incl. starter); "
            "HOLOGRAM_LIST_THREEJS=1 força Three.js."
        )

    if use_model_viewer:
        compact = bool(list_mode)
        doc = _build_model_viewer_html(
            preset, glb_url, rpm, tensao, corrente, plabel, compact=compact
        )
        h = 288 if compact else 360
    elif list_mode and lista_56 and glb_url and not _flag_truthy("HOLOGRAM_LIST_NO_GLB"):
        st.caption(
            "3D: malha resolvida, mas a consulta nao abre varios WebGL. Abra **Detalhes**; ou "
            "`HOLOGRAM_LIST_SHOW_GLB=1` (GPU)."
        )
        return
    else:
        carcaca_ctx = hologram_carcaca_context(m)
        legacy_css = _flag_truthy("HOLOGRAM_LEGACY_CSS")
        use_css_not_three = legacy_css or (list_mode and not force_list_three)
        if use_css_not_three:
            doc = _build_css_fallback_html_legacy(
                preset, fins_n, rpm, tensao, corrente, plabel, hid_attr, hid_plain
            )
            h = 310
        else:
            doc = _build_threejs_procedural_html(
                preset,
                rpm,
                tensao,
                corrente,
                plabel,
                hid_attr,
                hid_plain,
                carcaca_ctx,
                hint_suffix=list_glb_hint,
            )
            h = 340

    try:
        import streamlit.components.v1 as components

        # components.html costuma ser mais fiável que st.iframe para WebGL + model-viewer no Cloud.
        components.html(doc, height=h, scrolling=False)
    except Exception:
        try:
            if hasattr(st, "iframe"):
                st.iframe(src=doc, height=h, width="stretch")
            else:
                raise RuntimeError("no iframe") from None
        except Exception:
            st.caption(
                f"Holograma: {hologram_choice_label(preset)} ({preset}). RPM {rpm} | V {tensao} | A {corrente}"
            )

    if _flag_truthy("HOLOGRAM_HOLO_DEBUG"):
        udbg = (glb_url or "")[:120]
        ficha56 = nema_56_somente_ficha_mecanica(m)
        s56 = hologram_nema56_glb_secret_configurado()
        cctx = (hologram_carcaca_context(m) or "")[:100]
        st.caption(
            f"[HOLO_DEBUG] list={list_mode} use_mv={use_model_viewer} ficha_56={ficha56} "
            f"secret_nema56_ok={s56} glb={udbg!r} carcaca={cctx!r} preset={preset}. "
            "Ligue no Cloud (secrets): HOLOGRAM_HOLO_DEBUG; reinicie a app se alterou o GLB."
        )
