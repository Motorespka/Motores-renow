"""
Streamlit pages package.

Explicit submodules so `from page import cadastro, hub_comercial` works on
Streamlit Cloud (Linux) where implicit namespace packages can fail.
"""

from . import admin_panel
from . import atualizacoes
from . import cadastro
from . import consulta
from . import diagnostico
from . import edit
from . import hub_comercial
from . import motor_detail
from . import visao_geral

__all__ = [
    "admin_panel",
    "atualizacoes",
    "cadastro",
    "consulta",
    "diagnostico",
    "edit",
    "hub_comercial",
    "motor_detail",
    "visao_geral",
]
