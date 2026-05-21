"""Base de conhecimento da oficina — prioridade sobre constantes IEC teóricas."""

from knowledge.oficina_kb import (
    OficinaKnowledge,
    get_oficina_knowledge,
    reload_oficina_knowledge,
)

__all__ = [
    "OficinaKnowledge",
    "get_oficina_knowledge",
    "reload_oficina_knowledge",
]
