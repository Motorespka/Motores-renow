
import json
from pathlib import Path

ARQ = Path("core/memoria.json")

def _carregar():
    if ARQ.exists():
        return json.loads(ARQ.read_text(encoding="utf-8"))
    return {}

def _salvar(mem):
    ARQ.write_text(json.dumps(mem, indent=2, ensure_ascii=False), encoding="utf-8")

def aprender(busca, motor):
    mem = _carregar()
    lista = mem.get(busca, [])

    modelo = motor.get("modelo", "")
    if modelo not in lista:
        lista.append(modelo)

    mem[busca] = lista
    _salvar(mem)

def sugestao(busca):
    mem = _carregar()
    return mem.get(busca, [])
