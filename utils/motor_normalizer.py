"""
Normalização única de campos de motor vindos do Supabase (view/tabela + VariaveisSite).
Destinado ao Streamlit e a futura API/Next.js — sem efeitos colaterais de UI.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Sequence

ALIASES_PASSO_PRINCIPAL = (
    "PassoPrincipal",
    "passo_principal",
    "PassosPrincipais",
    "passos_principais",
)
ALIASES_PASSO_AUXILIAR = (
    "PassoAuxiliar",
    "passo_auxiliar",
    "PassosAuxiliares",
    "passos_auxiliares",
)
ALIASES_ESPIRAS_PRINCIPAL = (
    "EspirasPrincipal",
    "espiras_principal",
    "EspirasPrincipais",
    "espiras_principais",
)
ALIASES_ESPIRAS_AUXILIAR = (
    "EspirasAuxiliar",
    "espiras_auxiliar",
    "EspirasAuxiliares",
    "espiras_auxiliares",
)
ALIASES_FIO_PRINCIPAL = (
    "FioPrincipal",
    "fio_principal",
    "FiosPrincipais",
    "fios_principais",
)
ALIASES_FIO_AUXILIAR = (
    "FioAuxiliar",
    "fio_auxiliar",
    "FiosAuxiliares",
    "fios_auxiliares",
)
ALIASES_LIGACAO_PRINCIPAL = (
    "LigacaoPrincipal",
    "ligacao_principal",
    "LigacoesPrincipais",
    "ligacoes_principais",
)
ALIASES_LIGACAO_AUXILIAR = (
    "LigacaoAuxiliar",
    "ligacao_auxiliar",
    "LigacoesAuxiliares",
    "ligacoes_auxiliares",
)
ALIASES_EIXO_X = ("EixoX", "eixo_x")
ALIASES_EIXO_Y = ("EixoY", "eixo_y")
ALIASES_EIXO = ("Eixo", "eixo")
ALIASES_MEDIDAS = ("Medidas", "medidas")
ALIASES_POTENCIA = ("Potencia", "potencia")
ALIASES_RPM = ("Rpm", "rpm")
ALIASES_TENSAO = ("Tensao", "tensao")
ALIASES_CORRENTE = ("Corrente", "corrente")
ALIASES_FREQUENCIA = ("Frequencia", "frequencia")
ALIASES_POLOS = ("Polos", "polos")
ALIASES_TIPO_MOTOR = ("TipoMotor", "tipo_motor")
ALIASES_CARCACA = ("Carcaca", "carcaca")

ALIASES_PASSO_MULTI = ("Passo", "passo", "Passos", "passos")
ALIASES_ESPIRAS_MULTI = ("Espiras", "espiras")
ALIASES_FIO_MULTI = ("Fio", "fio", "Fios", "fios")
ALIASES_LIGACAO_MULTI = ("Ligacao", "ligacao", "Ligacoes", "ligacoes")


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        t = value.strip()
        if not t:
            return True
        low = t.lower()
        if low in ("-", "null", "none", "nan"):
            return True
    if value == [] or value == {}:
        return True
    return False


def _variaveis_site(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = row.get("VariaveisSite")
    if raw is None:
        raw = row.get("variaveis_site") or row.get("Variaveis_site")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def pick_value(row: Dict[str, Any], aliases: Sequence[str]) -> Any:
    """
    Para cada alias na ordem:
    1) row[alias] se não vazio
    2) VariaveisSite[alias] se existir e não vazio
    """
    vs = _variaveis_site(row)
    for alias in aliases:
        v = row.get(alias)
        if not is_empty(v):
            return v
        if isinstance(vs, dict) and alias in vs:
            v2 = vs.get(alias)
            if not is_empty(v2):
                return v2
    return None


def as_display_text(value: Any) -> str:
    """Texto para UI; listas viram ', '; vazios viram ''."""
    if is_empty(value):
        return ""
    if isinstance(value, list):
        parts = [str(x).strip() for x in value if not is_empty(x)]
        return ", ".join(parts)
    if isinstance(value, dict):
        if not value:
            return ""
        parts = [str(v).strip() for v in value.values() if not is_empty(v)]
        return ", ".join(parts)
    return str(value).strip()


def _items_from_multivalue(raw: Any) -> List[str]:
    """Extrai lista ordenada de itens (array, string CSV/SC)."""
    if is_empty(raw):
        return []
    if isinstance(raw, list):
        out: List[str] = []
        for x in raw:
            s = as_display_text(x)
            if s:
                out.append(s)
        return out
    if isinstance(raw, str):
        t = raw.strip()
        if not t:
            return []
        parts = [p.strip() for p in re.split(r"\s*[,;]\s*", t) if p.strip()]
        return parts if len(parts) > 1 else [t]
    s = as_display_text(raw)
    return [s] if s else []


def normalize_motor_row_for_ui(row: Dict[str, Any]) -> Dict[str, str]:
    """
    Camada única de normalização para exibição / JSON estável (ex.: Next).
    Todas as chaves em snake_case; valores sempre str (vazio = dado ausente).
    """
    r = row or {}

    passo_principal = as_display_text(pick_value(r, ALIASES_PASSO_PRINCIPAL))
    passo_auxiliar = as_display_text(pick_value(r, ALIASES_PASSO_AUXILIAR))
    espiras_principal = as_display_text(pick_value(r, ALIASES_ESPIRAS_PRINCIPAL))
    espiras_auxiliar = as_display_text(pick_value(r, ALIASES_ESPIRAS_AUXILIAR))
    fio_principal = as_display_text(pick_value(r, ALIASES_FIO_PRINCIPAL))
    fio_auxiliar = as_display_text(pick_value(r, ALIASES_FIO_AUXILIAR))
    ligacao_principal = as_display_text(pick_value(r, ALIASES_LIGACAO_PRINCIPAL))
    ligacao_auxiliar = as_display_text(pick_value(r, ALIASES_LIGACAO_AUXILIAR))

    eixo_x = as_display_text(pick_value(r, ALIASES_EIXO_X))
    eixo_y = as_display_text(pick_value(r, ALIASES_EIXO_Y))
    eixo = as_display_text(pick_value(r, ALIASES_EIXO))
    medidas = as_display_text(pick_value(r, ALIASES_MEDIDAS))

    potencia = as_display_text(pick_value(r, ALIASES_POTENCIA))
    rpm = as_display_text(pick_value(r, ALIASES_RPM))
    tensao = as_display_text(pick_value(r, ALIASES_TENSAO))
    corrente = as_display_text(pick_value(r, ALIASES_CORRENTE))
    frequencia = as_display_text(pick_value(r, ALIASES_FREQUENCIA))
    polos = as_display_text(pick_value(r, ALIASES_POLOS))
    tipo_motor = as_display_text(pick_value(r, ALIASES_TIPO_MOTOR))
    carcaca = as_display_text(pick_value(r, ALIASES_CARCACA))

    # Fallbacks inteligentes (Passo / Espiras / Fio / Ligacao)
    passo_items = _items_from_multivalue(pick_value(r, ALIASES_PASSO_MULTI))
    if not passo_principal and passo_items:
        passo_principal = passo_items[0]
    if not passo_auxiliar and len(passo_items) >= 2:
        passo_auxiliar = passo_items[1]

    esp_items = _items_from_multivalue(pick_value(r, ALIASES_ESPIRAS_MULTI))
    if not espiras_principal and esp_items:
        espiras_principal = esp_items[0]
    if not espiras_auxiliar and len(esp_items) >= 2:
        espiras_auxiliar = esp_items[1]

    fio_items = _items_from_multivalue(pick_value(r, ALIASES_FIO_MULTI))
    if not fio_principal and fio_items:
        fio_principal = fio_items[0]
    if not fio_auxiliar and len(fio_items) >= 2:
        fio_auxiliar = fio_items[1]

    lig_items = _items_from_multivalue(pick_value(r, ALIASES_LIGACAO_MULTI))
    if not ligacao_principal and lig_items:
        ligacao_principal = lig_items[0]
    if not ligacao_auxiliar and len(lig_items) >= 2:
        ligacao_auxiliar = lig_items[1]

    if not eixo and (eixo_x or eixo_y):
        eixo = f"X:{eixo_x or '-'} | Y:{eixo_y or '-'}"

    if not medidas and (eixo_x or eixo_y):
        if eixo_x and eixo_y:
            medidas = f"{eixo_x} x {eixo_y}"
        else:
            medidas = eixo_x or eixo_y

    return {
        "passo_principal": passo_principal,
        "passo_auxiliar": passo_auxiliar,
        "espiras_principal": espiras_principal,
        "espiras_auxiliar": espiras_auxiliar,
        "fio_principal": fio_principal,
        "fio_auxiliar": fio_auxiliar,
        "ligacao_principal": ligacao_principal,
        "ligacao_auxiliar": ligacao_auxiliar,
        "eixo_x": eixo_x,
        "eixo_y": eixo_y,
        "eixo": eixo,
        "medidas": medidas,
        "potencia": potencia,
        "rpm": rpm,
        "tensao": tensao,
        "corrente": corrente,
        "frequencia": frequencia,
        "polos": polos,
        "tipo_motor": tipo_motor,
        "carcaca": carcaca,
    }
