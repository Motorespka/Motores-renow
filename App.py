from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
LOVABLE_REPO = "git@github.com:Motorespka/motor-nova-vision.git"
COMMON_NPM_PATHS = (
    Path(r"C:\Program Files\nodejs\npm.cmd"),
    Path(r"C:\Program Files (x86)\nodejs\npm.cmd"),
)


def _require_path(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{description} nao encontrado: {path}")


def _find_npm() -> str:
    npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_cmd:
        return npm_cmd

    for candidate in COMMON_NPM_PATHS:
        if candidate.exists():
            return str(candidate)

    raise RuntimeError(
        "npm nao encontrado. Instale Node.js LTS ou adicione npm ao PATH."
    )


def _find_python() -> str:
    venv_python = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _with_node_path(env: dict[str, str], npm_cmd: str) -> dict[str, str]:
    updated = env.copy()
    npm_path = Path(npm_cmd).parent
    current_path = updated.get("PATH", "")
    if str(npm_path) not in current_path.split(os.pathsep):
        updated["PATH"] = f"{npm_path}{os.pathsep}{current_path}"
    return updated


def _startup_tasks(api_port: int, frontend_port: int) -> list[str]:
    api_base = f"http://127.0.0.1:{api_port}/api"
    return [
        "Configurar backend/.env com SUPABASE_URL e SUPABASE_ANON_KEY.",
        f"Configurar frontend/.env.local com NEXT_PUBLIC_API_BASE_URL={api_base}.",
        f"Subir FastAPI em http://127.0.0.1:{api_port}.",
        f"Subir Next.js em http://127.0.0.1:{frontend_port}.",
        f"Integracao final com repositorio Lovable: {LOVABLE_REPO}.",
    ]


def _print_tasks(api_port: int, frontend_port: int) -> None:
    print("\n[TAREFAS]")
    for idx, task in enumerate(_startup_tasks(api_port, frontend_port), start=1):
        print(f"{idx}. {task}")
    print("")


def _spawn_process(
    command: list[str], cwd: Path, env: dict[str, str] | None = None
) -> subprocess.Popen:
    return subprocess.Popen(command, cwd=str(cwd), env=env)


def _stop_process(proc: subprocess.Popen, name: str) -> int:
    if proc.poll() is not None:
        return int(proc.returncode or 0)

    print(f"[stop] Encerrando {name}...")
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    return int(proc.returncode or 0)


def run_backend(api_port: int) -> int:
    _require_path(BACKEND_DIR / "app" / "main.py", "Backend FastAPI")
    python_cmd = _find_python()
    cmd = [
        python_cmd,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(api_port),
        "--reload",
    ]
    print(f"[backend] {' '.join(cmd)}")
    proc = _spawn_process(cmd, BACKEND_DIR)
    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        return _stop_process(proc, "backend")


def run_frontend(api_port: int, frontend_port: int) -> int:
    _require_path(FRONTEND_DIR / "package.json", "Frontend Next.js")
    npm_cmd = _find_npm()
    env = _with_node_path(os.environ.copy(), npm_cmd)
    env.setdefault("NEXT_PUBLIC_API_BASE_URL", f"http://127.0.0.1:{api_port}/api")
    env.setdefault("PORT", str(frontend_port))
    env.setdefault("npm_config_offline", "false")

    cmd = [npm_cmd, "run", "dev", "--", "-p", str(frontend_port)]
    print(f"[frontend] {' '.join(cmd)}")
    proc = _spawn_process(cmd, FRONTEND_DIR, env=env)
    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        return _stop_process(proc, "frontend")


def run_streamlit_legacy(streamlit_port: int) -> int:
    legacy_file = ROOT_DIR / "legacy_streamlit_app.py"
    _require_path(legacy_file, "Entrypoint legacy Streamlit")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(legacy_file),
        "--server.port",
        str(streamlit_port),
    ]
    print(f"[streamlit-legacy] {' '.join(cmd)}")
    proc = _spawn_process(cmd, ROOT_DIR)
    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        return _stop_process(proc, "streamlit-legacy")


def run_dev(api_port: int, frontend_port: int) -> int:
    _require_path(BACKEND_DIR / "app" / "main.py", "Backend FastAPI")
    _require_path(FRONTEND_DIR / "package.json", "Frontend Next.js")

    python_cmd = _find_python()
    npm_cmd = _find_npm()

    api_base = f"http://127.0.0.1:{api_port}/api"
    frontend_env = _with_node_path(os.environ.copy(), npm_cmd)
    frontend_env.setdefault("NEXT_PUBLIC_API_BASE_URL", api_base)
    frontend_env.setdefault("PORT", str(frontend_port))
    frontend_env.setdefault("npm_config_offline", "false")

    backend_cmd = [
        python_cmd,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(api_port),
        "--reload",
    ]
    frontend_cmd = [npm_cmd, "run", "dev", "--", "-p", str(frontend_port)]

    _print_tasks(api_port, frontend_port)
    print(f"[backend] {' '.join(backend_cmd)}")
    backend_proc = _spawn_process(backend_cmd, BACKEND_DIR)

    print(f"[frontend] {' '.join(frontend_cmd)}")
    frontend_proc = _spawn_process(frontend_cmd, FRONTEND_DIR, env=frontend_env)

    try:
        while True:
            backend_code = backend_proc.poll()
            frontend_code = frontend_proc.poll()

            if backend_code is not None:
                print(f"[erro] Backend finalizou com codigo {backend_code}.")
                _stop_process(frontend_proc, "frontend")
                return int(backend_code)

            if frontend_code is not None:
                print(f"[erro] Frontend finalizou com codigo {frontend_code}.")
                _stop_process(backend_proc, "backend")
                return int(frontend_code)

            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[stop] Interrupcao manual recebida.")
        backend_code = _stop_process(backend_proc, "backend")
        frontend_code = _stop_process(frontend_proc, "frontend")
        return backend_code if backend_code != 0 else frontend_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Entrypoint da aplicacao em arquitetura Next.js + FastAPI."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="dev",
        choices=["dev", "backend", "frontend", "tasks", "streamlit-legacy"],
        help=(
            "Modo de execucao: dev (backend+frontend), backend, frontend, "
            "tasks ou streamlit-legacy."
        ),
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=8000,
        help="Porta do backend FastAPI (default: 8000).",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=3000,
        help="Porta do frontend Next.js (default: 3000).",
    )
    parser.add_argument(
        "--streamlit-port",
        type=int,
        default=8501,
        help="Porta do Streamlit legacy (default: 8501).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "tasks":
            _print_tasks(api_port=args.api_port, frontend_port=args.frontend_port)
            return 0
        if args.mode == "backend":
            return run_backend(api_port=args.api_port)
        if args.mode == "frontend":
            return run_frontend(
                api_port=args.api_port,
                frontend_port=args.frontend_port,
            )
        if args.mode == "streamlit-legacy":
            return run_streamlit_legacy(streamlit_port=args.streamlit_port)
        return run_dev(api_port=args.api_port, frontend_port=args.frontend_port)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"[erro] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
