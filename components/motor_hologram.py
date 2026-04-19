"""
Holograma: GLB via <model-viewer> quando houver URL resolvida.
Na listagem (consulta): URL http(s) a ``.glb`` usa ``model-viewer`` por defeito; ``HOLOGRAM_LIST_HIDE_REMOTE_GLB=1`` desliga
esse viewer nos cards (mostra silhueta CSS / Three.js procedural). ``HOLOGRAM_LIST_SHOW_GLB=1`` força tambem ``data:`` / pack.
``HOLOGRAM_LIST_NO_STATIC_GLB=1`` esconde ``/app/static/glb/``. ``HOLOGRAM_LIST_NO_GLB=1`` força só silhueta (sem ``model-viewer``).

Na consulta, a silhueta generica fica **desligada** por defeito; `HOLOGRAM_LISTA_SILHUETA_TODOS=1` volta
ao bloco de silhueta em todos. `HOLOGRAM_CARCACA_NEMA56_STRICT=1` controla a cadeia de resolucao GLB.

GLB (detalhe, nao list): hotspots 3D + `hologram_hotspot_overrides` no JSON; ajuste global
`hologram_hotspot_scale` / `hologram_hotspot_offset` (motor) em cima dos defaults. `hologram_capacitor_hotspot: false` ou `HOLOGRAM_NO_GLB_HOTSPOTS=1`.
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
    consulta_lista_motor_tem_familia_glb_dedicada_na_ficha,
    consulta_lista_somente_familia_56_activa,
    hologram_carcaca_context,
    hologram_nema56_glb_secret_configurado,
    mecanica_nema56_modo_restrito,
    motor_has_hologram_motor_id_secret,
    motor_has_json_hologram_glb_url,
    nema_56_somente_ficha_mecanica,
    nema42_glb_url_efectiva,
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
const isNema48 = /NEMA(?:\\s*[-_]?\\s*)?48\\b/i.test(carU);
const isNema42 = /NEMA(?:\\s*[-_]?\\s*)?42\\b/i.test(carU);
const nemaLiso = /^(liso_56|nema_mono|nema_footless|cface_56|pump_56j)$/.test(preset);
const isNemaFamily = nemaLiso || carU.includes('NEMA');

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
  if (isNema42) {
    r = 0.078;
    len = 0.14;
  } else if (isNema48) {
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

  if (isNema48 || preset === 'liso_56' || preset === 'nema_mono' || preset === 'cface_56' || preset === 'pump_56j') {
    const cap = new THREE.Mesh(new THREE.BoxGeometry(r * 1.25, 0.075, r * 0.95), wf(0xfbbf24));
    cap.position.set(0.04, r + 0.048, 0);
    g.add(cap);
  }

  if ((isNema48 || isNemaFamily) && preset !== 'nema_footless') {
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
        "liso_56": 6,
        "cface_56": 6,
        "pump_56j": 6,
        "nema_footless": 4,
        "iec_w22": 12,
        "trif_grande": 13,
        "servo_compacto": 7,
        "generico": 8,
    }.get(preset, 8)


def _host_id(key: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", key or "motor")[:48]
    return f"holoeng_{safe}"


def _holo_motor_json(m: Any) -> Dict[str, Any]:
    d = m.get("dados_tecnicos_json") if isinstance(m, dict) and isinstance(m.get("dados_tecnicos_json"), dict) else {}
    mo = d.get("motor")
    return mo if isinstance(mo, dict) else {}


def _holo_mecanica_json(m: Any) -> Dict[str, Any]:
    d = m.get("dados_tecnicos_json") if isinstance(m, dict) and isinstance(m.get("dados_tecnicos_json"), dict) else {}
    mec = d.get("mecanica")
    return mec if isinstance(mec, dict) else {}


def _holo_pick(*vals: Any) -> str:
    for v in vals:
        t = _to_text(v)
        if t:
            return t
    return ""


def _holo_glb_kpi_pairs(m: dict | None, rpm: str, tensao: str, corrente: str) -> list[tuple[str, str]]:
    m = m or {}
    mot, mec = _holo_motor_json(m), _holo_mecanica_json(m)
    cv = _holo_pick(
        m.get("potencia"),
        m.get("potencia_cv"),
        mot.get("potencia"),
        mot.get("cv"),
        m.get("cv"),
    )
    fases = _holo_pick(m.get("fases"), mot.get("fases"), mot.get("fase"))
    if not fases and _holo_pick(mot.get("tipo_motor"), m.get("tipo_motor")):
        fases = str(_holo_pick(mot.get("tipo_motor"), m.get("tipo_motor")))[:22]
    pol = _holo_pick(m.get("polos"), mot.get("polos"), mec.get("polos"), mot.get("num_polos"), mec.get("num_polos"))
    if pol and re.match(r"^\d{1,2}$", str(pol).strip().replace(" ", "")):
        pol = f"{str(pol).strip()}P"
    hz = _holo_pick(
        m.get("frequencia"),
        mot.get("frequencia"),
        mec.get("frequencia"),
        mot.get("frequencia_hz"),
        m.get("freq"),
    )
    if (
        hz
        and re.match(r"^[\d.,]+(?:/[\d.,]+)?$", str(hz).replace(" ", ""))
        and "Hz" not in str(hz)
        and "H" not in str(hz)
    ):
        hz = f"{hz} Hz" if re.search(r"\d", str(hz)) else hz
    carc = _holo_pick(m.get("carcaca"), m.get("Carcaca"), mec.get("carcaca"), mot.get("carcaca"))
    qd = _holo_pick(
        m.get("quadro_nema"),
        m.get("quadro"),
        m.get("nema"),
        mec.get("quadro"),
        mec.get("nema"),
        mec.get("nema_frame"),
        mec.get("frame"),
        mec.get("envelope"),
        mot.get("quadro"),
        mot.get("nema"),
        mot.get("nema_frame"),
        mot.get("frame"),
    )
    ipx = _holo_pick(
        m.get("ip"),
        m.get("classe"),
        mec.get("ip"),
        mec.get("classe_de_isolamento"),
        mec.get("classe_de_isolacao"),
        mec.get("classe_de_isolacao_motor"),
        mec.get("is_ip"),
        mot.get("ip"),
    )
    rpm_d = _to_text(rpm) or "—"
    v_d = _to_text(tensao) or "—"
    a_d = _to_text(corrente) or "—"
    rows: list[tuple[str, str]] = [
        ("CV", cv or "—"),
        ("RPM", rpm_d),
        ("V", v_d),
        ("A", a_d if a_d else "—"),
        ("Fases", fases or "—"),
        ("Pólos", pol or "—"),
        ("Freq.", hz or "—"),
        ("Carc.", carc or "—"),
        ("Quadro/NEMA", qd or "—"),
    ]
    if str(ipx or "").strip() and not str(ipx or "").lower() in ("0", "false", "n/a"):
        rows.append(("IP/iso.", str(ipx)[:20]))
    return rows


def _holo_glb_kpi_block(m: dict | None, rpm: str, tensao: str, corrente: str, *, compact: bool) -> str:
    prs = _holo_glb_kpi_pairs(m, rpm, tensao, corrente)
    if compact and len(prs) > 6:
        prs = prs[:6]
    lines: list[str] = []
    for lb, v in prs:
        vs = "—" if (v is None or str(v).strip() in ("", "—", "-")) else str(v)
        tip = html.escape(f"{lb}: {vs}"[:200])
        one = f'<div class="kpi" title="{tip}">{html.escape(lb)} <b>{html.escape(vs)}</b></div>'
        lines.append(one)
    return "\n    ".join(lines)


def _holo_show_capacitor_hotspot(m: dict | None) -> bool:
    """Motor JSON `hologram_capacitor_hotspot`: 0 / false / hide oculta o ponto do capacitor."""
    mot = _holo_motor_json(m)
    v = mot.get("hologram_capacitor_hotspot", mot.get("HologramCapacitorHotspot"))
    if v is None:
        return True
    if v is False or (isinstance(v, (int, float)) and v == 0):
        return False
    s = str(v).strip().lower()
    if s in ("0", "false", "no", "off", "hide", "hidden", "não", "nao"):
        return False
    return True


def _holo_vec3_tostring(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, str) and re.match(r"^\s*[-+0-9.]+", v):
        parts = re.split(r"[\s,;]+", v.strip())
        nums = [p for p in parts if p]
        if len(nums) >= 3:
            return f"{float(nums[0]):.4f} {float(nums[1]):.4f} {float(nums[2]):.4f}"
    if isinstance(v, (list, tuple)) and len(v) >= 3:
        return f"{float(v[0]):.4f} {float(v[1]):.4f} {float(v[2]):.4f}"
    if isinstance(v, dict) and "x" in v and "y" in v and "z" in v:
        return f"{float(v['x']):.4f} {float(v['y']):.4f} {float(v['z']):.4f}"
    return None


def _holo_hotspot_tuning_get(m: dict | None, key: str) -> Any:
    """Lê de `dados_tecnicos_json.motor` ou, se a chave nao existir, do dict do motor (raiz)."""
    m = m or {}
    mot = _holo_motor_json(m)
    if key in mot:
        return mot[key]
    if isinstance(m, dict) and key in m:
        return m[key]
    return None


def _holo_parse_hotspot_scale(m: dict | None) -> tuple[float, float, float]:
    r = _holo_hotspot_tuning_get(m, "hologram_hotspot_scale")
    if r is None or (isinstance(r, str) and r.strip() == ""):
        r = _holo_hotspot_tuning_get(m, "HologramHotspotScale")
    if r is None or (isinstance(r, str) and r.strip() == ""):
        return (1.0, 1.0, 1.0)
    if isinstance(r, (int, float)) and not isinstance(r, bool):
        s = float(r)
        return (s, s, s)
    if isinstance(r, (list, tuple)) and r:
        if len(r) == 1 and isinstance((r[0] if r else 0.0), (int, float)) and not isinstance(r[0], bool):
            s = float(r[0])
            return (s, s, s)
        if len(r) >= 3:
            return (float(r[0]), float(r[1]), float(r[2]))
    if isinstance(r, dict) and "x" in r:
        return (float(r["x"]), float(r.get("y", 1.0)), float(r.get("z", 1.0)))
    if isinstance(r, str) and re.match(r"^\s*[-+0-9.]+", r):
        parts = re.split(r"[\s,;]+", r.strip())
        if len(parts) == 1:
            s = float(parts[0])
            return (s, s, s)
        if len(parts) >= 3:
            return (float(parts[0]), float(parts[1]), float(parts[2]))
    return (1.0, 1.0, 1.0)


def _holo_parse_hotspot_offset(m: dict | None) -> tuple[float, float, float]:
    r = _holo_hotspot_tuning_get(m, "hologram_hotspot_offset")
    if r is None or (isinstance(r, str) and r.strip() == ""):
        r = _holo_hotspot_tuning_get(m, "HologramHotspotOffset")
    if r is None or (isinstance(r, str) and r.strip() == ""):
        return (0.0, 0.0, 0.0)
    t = _holo_vec3_tostring(r)
    if t is not None:
        p0, p1, p2 = t.split()
        return (float(p0), float(p1), float(p2))
    if isinstance(r, (list, tuple)) and len(r) >= 3:
        return (float(r[0]), float(r[1]), float(r[2]))
    if isinstance(r, dict) and "x" in r and "y" in r and "z" in r:
        return (float(r["x"]), float(r["y"]), float(r["z"]))
    return (0.0, 0.0, 0.0)


def _holo_annotations_merged(m: dict | None) -> list[dict[str, Any]]:
    """
    Pontos 3D: defaults + `motor.hologram_hotspot_overrides`.
    Ajuste global: `hologram_hotspot_scale` (1 número ou "sx sy sz", ou {{x,y,z}}) e
    `hologram_hotspot_offset` (vetor "x y z"); aplica a cada ponto: p' = p * s + o.
    """
    mot = _holo_motor_json(m or {})
    ov = mot.get("hologram_hotspot_overrides") or mot.get("HologramHotspotOverrides")
    ovd: dict[str, Any] = {}
    if isinstance(ov, dict):
        ovd = dict(ov)
    elif isinstance(ov, str) and ov.strip():
        try:
            t = json.loads(ov)
            ovd = t if isinstance(t, dict) else {}
        except Exception:
            ovd = {}
    # Normais: frente = +X, trás = -X, cima = +Y (eixo, placa, cap no topo aproximado)
    sp: list[dict[str, Any]] = [
        {
            "id": 0,
            "key": "rolamento_frente",
            "p": (0.22, 0.0, 0.0),
            "n": (1.0, 0.0, 0.0),
            "l": "Rolamento (frente - eixo)",
        },
        {
            "id": 1,
            "key": "rolamento_tras",
            "p": (-0.2, 0.0, 0.0),
            "n": (-1.0, 0.0, 0.0),
            "l": "Rolamento (trás - eixo)",
        },
        {
            "id": 2,
            "key": "placa",
            "p": (0.0, 0.11, 0.09),
            "n": (0.0, 0.0, 1.0),
            "l": "Placa de dados",
        },
        {
            "id": 3,
            "key": "capacitor",
            "p": (0.12, 0.13, 0.0),
            "n": (0.0, 1.0, 0.0),
            "l": "Capacitor (se houver)",
        },
    ]
    if not _holo_show_capacitor_hotspot(m or {}):
        sp = [x for x in sp if x["key"] != "capacitor"]
    for idx, it in enumerate(sp):
        it["id"] = idx
    for it in sp:
        key = it["key"]
        sub = ovd.get(key) or ovd.get(key.replace("_", ""))
        if sub is not None and isinstance(sub, dict):
            ps = _holo_vec3_tostring(
                sub.get("p") or sub.get("pos") or sub.get("data-position") or sub.get("data_position")
            )
            if ps is not None:
                parts = [float(x) for x in ps.split()]
                it["p"] = (parts[0], parts[1], parts[2])
            ns = _holo_vec3_tostring(
                sub.get("n") or sub.get("normal") or sub.get("data-normal")
            )
            if ns is not None:
                np = [float(x) for x in ns.split()]
                it["n"] = (np[0], np[1], np[2])
            tlab = sub.get("label") or sub.get("l") or sub.get("text")
            if tlab is not None and str(tlab).strip() != "":
                it["l"] = str(tlab).strip()
    sx, sy, sz = _holo_parse_hotspot_scale(m)
    ox, oy, oz = _holo_parse_hotspot_offset(m)
    for it in sp:
        p = it["p"]
        it["p"] = (p[0] * sx + ox, p[1] * sy + oy, p[2] * sz + oz)
    return sp


def _build_model_viewer_hotspots_html(m: dict | None) -> str:
    rows = _holo_annotations_merged(m)
    if not rows:
        return ""
    out: list[str] = []
    for it in rows:
        i = int(it["id"])
        px, py, pz = it["p"]
        nx, ny, nz = it["n"]
        p_s = f"{px:.4f} {py:.4f} {pz:.4f}"
        n_s = f"{nx:.4f} {ny:.4f} {nz:.4f}"
        lbl = html.escape(str(it.get("l") or ""))
        out.append(
            f'''<button type="button" class="holo-hs" slot="hotspot-{i}" data-position="{p_s}" data-normal="{n_s}">
  <span class="holo-hs-pt" aria-hidden="true"></span>
  <span class="holo-hs-rod" aria-hidden="true"></span>
  <span class="holo-hs-txt">{lbl}</span>
</button>'''
        )
    return "\n".join(out)


def _build_model_viewer_html(
    preset: str,
    glb_url: str,
    rpm: str,
    tensao: str,
    corrente: str,
    plabel: str,
    *,
    compact: bool = False,
    motor: dict | None = None,
) -> str:
    src = json.dumps(glb_url)
    mv_h = 160 if compact else 240
    kpi_block = _holo_glb_kpi_block(motor, rpm, tensao, corrente, compact=compact)
    sp_html = _build_model_viewer_hotspots_html(motor) if (not compact and not _flag_truthy("HOLOGRAM_NO_GLB_HOTSPOTS")) else ""
    hint_block = (
        ""
        if compact
        else (
            '<div class="hint">Malha 3D com camada holográfica (scanline + brilho). Gire com o rato ou um dedo. '
            "Anotacoes: rolamentos, placa, capacitor. Ajuste com "
            "<code>hologram_hotspot_overrides</code>, e global "
            "<code>hologram_hotspot_scale</code> (1 nr ou sx sy sz) e "
            "<code>hologram_hotspot_offset</code> (x y z) — p' = p*scale+offset.</div>"
        )
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
    z-index: 4;
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
  .holo-hs {{
    display: flex; flex-direction: row; flex-wrap: nowrap; align-items: center; gap: 0;
    background: none; border: 0; margin: 0; padding: 0; min-width: 0; min-height: 0; cursor: pointer;
  }}
  .holo-hs-pt {{
    display: block; width: 8px; height: 8px; border-radius: 50%;
    background: #22d3ee; box-shadow: 0 0 9px 2px rgba(34,211,238,0.95);
    border: 1px solid #ecfeff; flex: 0 0 auto; transform: translate(0, 0);
  }}
  .holo-hs-rod {{
    display: block; width: 32px; height: 1px; flex: 0 0 auto; align-self: center;
    background: linear-gradient(90deg, #67e8f9, rgba(103,232,249,0.25), rgba(6,20,32,0));
  }}
  .holo-hs-txt {{
    display: block; max-width: 7.2em; font: 8px/1.15 system-ui, sans-serif; text-align: left; color: #a5f3fc;
    text-shadow: 0 0 4px #000, 0 1px 2px #000; flex: 0 1 auto;
  }}
  .kpis.holo-glb-kpis {{
    display:grid;
    grid-template-columns: repeat(auto-fit, minmax(76px, 1fr));
    gap:5px; padding:8px 8px 10px;
  }}
  .holo-glb-kpis .kpi {{
    font-size:8px; line-height:1.2; padding:4px 6px; text-align:left;
    min-height:2.1em; word-break:break-word;
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
      crossorigin="anonymous"
      camera-controls
      touch-action="pan-y"
      shadow-intensity="0.35"
      exposure="0.72"
      interaction-prompt="none"
    >{sp_html}
    </model-viewer>
    </div>
    <div class="kpis holo-glb-kpis">
      {kpi_block}
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
  .holo-preset--nema_mono .scene,
  .holo-preset--liso_56 .scene,
  .holo-preset--cface_56 .scene,
  .holo-preset--pump_56j .scene
    {{ transform: perspective(640px) rotateX(10deg) rotateY(-18deg) scale(0.92); }}
  .holo-preset--nema_footless .scene {{ transform: perspective(640px) rotateX(8deg) rotateY(-14deg) scale(0.9); }}
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
          {"<div class='cap'></div>" if preset in ("liso_56", "nema_mono", "cface_56", "pump_56j", "ip21_aberto") else ""}
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

    # V200 consulta: o mesmo `resolve_model_glb_url` que no detalhe; se ja ha URL,
    # nao esconder o cartao por lacuna em `consulta_lista_motor_tem_familia_glb_dedicada_na_ficha`
    # (ex.: WEG/DEFAULT/preset por secret, ou heuristica alinhada ao detalhe).
    lista_56 = consulta_lista_somente_familia_56_activa()
    if list_mode and lista_56:
        if not (
            consulta_lista_motor_tem_familia_glb_dedicada_na_ficha(m)
            or motor_has_json_hologram_glb_url(m)
            or motor_has_hologram_motor_id_secret(m)
            or bool(glb_url)
        ):
            st.caption(
                f"3D: {NEMA_56_CARCACA_LEGENDA_COMPLETA} (NEMA 56); IEC63 / catálogo TEFC B3 (GLB `105 a.glb`); "
                "IEC 132 (GLB dedicado); IEC 100L; bomba / Ex — ou `motor.holograma_glb_url` / secret `HOLOGRAM_GLB_MOTOR_<id>`."
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
    hide_remote_glb = _flag_truthy("HOLOGRAM_LIST_HIDE_REMOTE_GLB")
    json_list_glb = motor_has_json_hologram_glb_url(m)
    remote_list_glb = _glb_url_ok_for_list_remote_viewer(glb_url or "")
    use_model_viewer = bool(glb_url) and (
        not list_mode
        or (
            not no_list_glb
            and (
                force_list_glb
                or json_list_glb
                or (remote_list_glb and not hide_remote_glb)
            )
        )
    )
    # Lista + GLB publico em https://… .glb (ex.: Supabase): activar viewer por defeito.
    # Opt-out: HOLOGRAM_LIST_NO_GLB=1 ou HOLOGRAM_LIST_HIDE_REMOTE_GLB=1 nos secrets.
    if list_mode and bool(glb_url) and not no_list_glb and not hide_remote_glb:
        u0 = str(glb_url).strip().lower()
        if u0.startswith("https://"):
            base = u0.split("?", 1)[0].split("#", 1)[0].rstrip("/")
            if base.endswith(".glb"):
                use_model_viewer = True

    # Three.js tambem usa WebGL: N iframes na consulta esgotam contextos (ecra branco / vazio).
    force_list_three = _flag_truthy("HOLOGRAM_LIST_THREEJS")
    list_glb_hint = ""
    if list_mode and glb_url and not use_model_viewer:
        list_glb_hint = (
            " GLB resolvido, mas o viewer 3D na lista esta desligado (veja secrets: "
            "`HOLOGRAM_LIST_NO_GLB` / `HOLOGRAM_LIST_HIDE_REMOTE_GLB`). "
            "Silhueta abaixo; malha completa em **Detalhes**."
        )

    if use_model_viewer:
        compact = bool(list_mode)
        doc = _build_model_viewer_html(
            preset, glb_url, rpm, tensao, corrente, plabel, compact=compact, motor=m
        )
        h = 300 if compact else 420
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
        n42_url = bool(nema42_glb_url_efectiva())
        cctx = (hologram_carcaca_context(m) or "")[:100]
        st.caption(
            f"[HOLO_DEBUG] list={list_mode} use_mv={use_model_viewer} ficha_56={ficha56} "
            f"nema_familia_glb_ok={s56} nema42_url_ok={n42_url} glb={udbg!r} carcaca={cctx!r} preset={preset}. "
            "Ligue no Cloud (secrets): HOLOGRAM_HOLO_DEBUG; reinicie a app se alterou o GLB."
        )
