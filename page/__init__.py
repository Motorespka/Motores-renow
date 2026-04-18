"""
Streamlit pages package.

Explicit submodules so `from page import cadastro, hub_comercial` works on
Streamlit Cloud (Linux) where implicit namespace packages can fail.
"""

from . import admin_panel
from . import atualizacoes
from . import biblioteca_calculos
from . import cadastro
from . import consulta
from . import diagnostico
from . import edit
from . import hub_comercial
from . import motor_detail
from . import ordens_servico
from . import visao_geral

__all__ = [
    "admin_panel",
    "atualizacoes",
    "biblioteca_calculos",
    "cadastro",
    "consulta",
    "diagnostico",
    "edit",
    "hub_comercial",
    "motor_detail",
    "ordens_servico",
    "visao_geral",
]
