"""
Holograma na consulta: GLB real via <model-viewer> quando houver URL; senao silhueta CSS com arrastar.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any, Dict

import streamlit as st

from utils.motor_hologram import hologram_choice_label, resolve_hologram_preset
from utils.motor_hologram_glb import resolve_model_glb_url


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
) -> str:
    src = json.dumps(glb_url)
    return f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js"></script>
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
  .hint {{ font-size:9px; color:#7dd3fc; opacity:0.85; padding:6px 10px 4px; }}
  model-viewer {{
    width: 100%;
    height: 240px;
    background: radial-gradient(circle at 50% 40%, rgba(34,211,238,0.12), rgba(2,8,16,0.95));
    --poster-color: transparent;
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
      <span>ENGINE 3D (GLB)</span>
      <span>{plabel}</span>
    </div>
    <div class="hint">Gire com o rato ou um dedo (camera integrada)</div>
    <model-viewer
      src={src}
      alt="Motor 3D"
      camera-controls
      touch-action="pan-y"
      shadow-intensity="0.85"
      exposure="1"
      interaction-prompt="none"
    ></model-viewer>
    <div class="kpis">
      <div class="kpi">RPM <b>{rpm}</b></div>
      <div class="kpi">V <b>{tensao}</b></div>
      <div class="kpi">A <b>{corrente}</b></div>
    </div>
  </div>
</body></html>
"""


def _build_css_fallback_html(
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
      <span>ENGINE HOLOGRAM</span>
      <span>{plabel}</span>
    </div>
    <div class="hint">Arraste na area para girar o modelo (sem GLB configurado)</div>
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


def render_engine_hologram(m: Dict[str, Any], key: str = "") -> None:
    preset = resolve_hologram_preset(m)
    glb_url = resolve_model_glb_url(m, preset)
    fins_n = _fins_html(_preset_fins_count(preset))
    rpm = html.escape(_to_text(m.get("rpm")) or "-")
    tensao = html.escape(_to_text(m.get("tensao")) or "-")
    corrente = html.escape(_to_text(m.get("corrente")) or "-")
    plabel = html.escape(hologram_choice_label(preset))
    hid_plain = _host_id(key)
    hid_attr = html.escape(hid_plain)

    if glb_url:
        doc = _build_model_viewer_html(preset, glb_url, rpm, tensao, corrente, plabel)
        h = 360
    else:
        doc = _build_css_fallback_html(
            preset, fins_n, rpm, tensao, corrente, plabel, hid_attr, hid_plain
        )
        h = 310

    try:
        import streamlit.components.v1 as components

        components.html(doc, height=h, scrolling=False)
    except Exception:
        st.caption(
            f"Holograma: {hologram_choice_label(preset)} ({preset}). RPM {rpm} | V {tensao} | A {corrente}"
        )
