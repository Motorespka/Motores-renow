from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
LEGACY_FILE = ROOT_DIR / "legacy_streamlit_app.py"

API_PORT = int(os.getenv("API_PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))

API_URL = f"http://127.0.0.1:{API_PORT}"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
API_DOCS_URL = f"{API_URL}/docs"


def _require_path(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{description} não encontrado: {path}")


def _find_python() -> str:
    win_venv = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    unix_venv = ROOT_DIR / ".venv" / "bin" / "python"
    if win_venv.exists():
        return str(win_venv)
    if unix_venv.exists():
        return str(unix_venv)
    return sys.executable


def _find_npm() -> str:
    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_cmd:
        return npm_cmd

    known_paths = [
        Path(r"C:\Program Files\nodejs\npm.cmd"),
        Path(r"C:\Program Files (x86)\nodejs\npm.cmd"),
    ]
    for candidate in known_paths:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError("npm não encontrado. Instale Node.js e adicione ao PATH.")


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def _wait_port(host: str, port: int, seconds: int = 30) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.5)
    return False


def _spawn(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.Popen:
    return subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def _start_backend() -> dict:
    _require_path(BACKEND_DIR / "app" / "main.py", "Backend FastAPI")

    if _port_open("127.0.0.1", API_PORT):
        return {"name": "backend", "running": True, "spawned": False, "url": API_URL}

    python_cmd = _find_python()
    cmd = [
        python_cmd,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(API_PORT),
    ]

    proc = _spawn(cmd, BACKEND_DIR)
    ok = _wait_port("127.0.0.1", API_PORT, seconds=30)

    return {
        "name": "backend",
        "running": ok,
        "spawned": True,
        "proc": proc,
        "url": API_URL,
        "cmd": " ".join(cmd),
    }


def _start_frontend() -> dict:
    _require_path(FRONTEND_DIR / "package.json", "Frontend Next.js")

    if _port_open("127.0.0.1", FRONTEND_PORT):
        return {"name": "frontend", "running": True, "spawned": False, "url": FRONTEND_URL}

    npm_cmd = _find_npm()
    env = os.environ.copy()
    env["NEXT_PUBLIC_API_BASE_URL"] = f"{API_URL}/api"
    env["PORT"] = str(FRONTEND_PORT)

    cmd = [npm_cmd, "run", "dev", "--", "-p", str(FRONTEND_PORT)]

    proc = _spawn(cmd, FRONTEND_DIR, env=env)
    ok = _wait_port("127.0.0.1", FRONTEND_PORT, seconds=60)

    return {
        "name": "frontend",
        "running": ok,
        "spawned": True,
        "proc": proc,
        "url": FRONTEND_URL,
        "cmd": " ".join(cmd),
    }


@st.cache_resource(show_spinner=False)
def ensure_stack() -> dict:
    backend = _start_backend()
    frontend = _start_frontend()
    return {"backend": backend, "frontend": frontend}


def _status_line(label: str, running: bool, url: str) -> None:
    icon = "🟢" if running else "🔴"
    st.write(f"{icon} **{label}** — {url}")


st.set_page_config(page_title="Moto-Renow Bridge", layout="wide")
st.title("Moto-Renow — Streamlit puxando Next.js + FastAPI")

st.caption("Casca Streamlit para iniciar o backend e o frontend e exibir o site novo dentro do app.")

error = None
stack = None

try:
    with st.spinner("Iniciando backend e frontend..."):
        stack = ensure_stack()
except Exception as exc:
    error = exc

with st.sidebar:
    st.header("Status")

    if error:
        st.error(str(error))
    else:
        _status_line("FastAPI", stack["backend"]["running"], API_URL)
        _status_line("Next.js", stack["frontend"]["running"], FRONTEND_URL)

        st.markdown(f"[Abrir frontend]({FRONTEND_URL})")
        st.markdown(f"[Abrir docs da API]({API_DOCS_URL})")

        if LEGACY_FILE.exists():
            st.info("legacy_streamlit_app.py encontrado no projeto.")

        if st.button("Reiniciar verificação"):
            ensure_stack.clear()
            st.rerun()

if error:
    st.error("Falha ao iniciar a stack.")
    st.code(str(error))
    st.stop()

backend_ok = stack["backend"]["running"]
frontend_ok = stack["frontend"]["running"]

if not backend_ok:
    st.error("O FastAPI não subiu.")
    if "cmd" in stack["backend"]:
        st.code(stack["backend"]["cmd"])
if not frontend_ok:
    st.error("O Next.js não subiu.")
    if "cmd" in stack["frontend"]:
        st.code(stack["frontend"]["cmd"])

if backend_ok and frontend_ok:
    st.success("Stack iniciada com sucesso.")
    components.iframe(FRONTEND_URL, height=900, scrolling=True)
else:
    st.warning("Algum serviço não abriu. Veja o status na barra lateral.")
    st.markdown(f"- Frontend esperado: `{FRONTEND_URL}`")
    st.markdown(f"- Backend esperado: `{API_URL}`")
    st.markdown(f"- Docs da API: `{API_DOCS_URL}`")
