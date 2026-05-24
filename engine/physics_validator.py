#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador físico central — B, J, ff e equivalência de área de cobre (Regra dos 5%).

Referências:
- B ≤ 1,5 T (saturação aço-silício)
- J = I / A_total (A/mm²); faixa 3–7, ideal ~4
- ff = A_cobre / A_ranhura; faixa 0,25–0,45
- ΔA ≤ 5% ao trocar bitola sem compensar espiras
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from services.motor_rebobinagem.wire_gauge import AWG_SOLID_CU_MM2, awg_integer_to_mm2


class PhysicsValidator:
    """Limites inegociáveis do gêmeo digital — fonte única para o motor de cálculo."""

    LIMITE_B: float = 1.5
    # Hard stop alinhado a physics_audit (J_MAX=7); reprovação severa em 6 para auditoria estrita.
    LIMITE_J_MAX: float = 7.0
    LIMITE_J_SEVERE: float = 6.0
    LIMITE_J_MIN: float = 3.0
    LIMITE_J_IDEAL: float = 4.0
    LIMITE_FF_MAX: float = 0.45
    LIMITE_FF_MIN: float = 0.25
    LIMITE_FF_IDEAL_LO: float = 0.30
    LIMITE_FF_IDEAL_HI: float = 0.40
    TOLERANCIA_AREA: float = 0.05

    # Lookup AWG 10–30 (mm² cobre nu) — alinhado a wire_gauge.py
    AWG_AREA_MM2: dict[int, float] = {
        k: v for k, v in AWG_SOLID_CU_MM2.items() if 10 <= k <= 30
    }

    @staticmethod
    def calculate_wire_area(awg: int | float) -> float:
        """Área de um condutor (mm²) a partir do AWG inteiro."""
        awg_i = int(round(float(awg)))
        area = awg_integer_to_mm2(awg_i)
        if area is not None and area > 0:
            return float(area)
        return float(PhysicsValidator.AWG_AREA_MM2.get(awg_i, 0.0))

    @staticmethod
    def total_copper_area_mm2(
        *,
        awg: int | float,
        parallel_count: int = 1,
    ) -> float:
        """A_total de um condutor equivalente (um “pacote” paralelo)."""
        return PhysicsValidator.calculate_wire_area(awg) * max(1, int(parallel_count))

    @staticmethod
    def validate_wire_replacement(
        area_original: float,
        area_nova: float,
    ) -> tuple[bool, str]:
        """
        Regra dos 5%: |A_nova - A_orig| / A_orig ≤ 5%.
        Retorna (aprovado, mensagem).
        """
        if area_original <= 0:
            return True, ""
        delta_pct = abs(float(area_nova) - float(area_original)) / float(area_original)
        if delta_pct > PhysicsValidator.TOLERANCIA_AREA + 1e-9:
            return (
                False,
                "REPROVADO POR INCOERÊNCIA FÍSICA: variação de área "
                f">{PhysicsValidator.TOLERANCIA_AREA:.0%} sem ajuste proporcional de espiras.",
            )
        return True, ""

    @staticmethod
    def calculate_fill_factor(total_copper_area: float, slot_area: float) -> float:
        """ff = A_cobre / A_ranhura (fração 0–1)."""
        if slot_area <= 0 or total_copper_area <= 0:
            return 0.0
        return round(min(1.0, float(total_copper_area) / float(slot_area)), 4)

    @staticmethod
    def validate_j_density(
        current_a: float,
        total_copper_area_mm2: float,
    ) -> tuple[bool, str, Optional[float]]:
        """
        J = I / A_total (A/mm²).
        Retorna (aprovado, mensagem, J calculado).
        """
        if total_copper_area_mm2 <= 0:
            return False, "REPROVADO: área de cobre inválida para cálculo de J.", None
        if current_a <= 0:
            return True, "", None
        j_val = round(float(current_a) / float(total_copper_area_mm2), 3)
        if j_val > PhysicsValidator.LIMITE_J_MAX + 1e-6:
            return (
                False,
                f"REPROVADO: J={j_val} A/mm² > {PhysicsValidator.LIMITE_J_MAX} A/mm² "
                "(fora da faixa segura 3–7 A/mm²).",
                j_val,
            )
        if j_val < PhysicsValidator.LIMITE_J_MIN - 1e-6:
            return (
                False,
                f"REPROVADO: J={j_val} A/mm² < {PhysicsValidator.LIMITE_J_MIN} A/mm² "
                "(cobre ocioso / bitola excessiva).",
                j_val,
            )
        return True, "", j_val

    @staticmethod
    def validate_fill_factor(ff: float) -> tuple[bool, str]:
        """ff em fração 0–1 (não percentual inteiro)."""
        ff_n = float(ff)
        if ff_n > PhysicsValidator.LIMITE_FF_MAX + 1e-6:
            return (
                False,
                f"REPROVADO: ff={ff_n:.1%} > {PhysicsValidator.LIMITE_FF_MAX:.0%} "
                "(fio não cabe na ranhura).",
            )
        if ff_n > 0 and ff_n < PhysicsValidator.LIMITE_FF_MIN - 1e-6:
            return (
                False,
                f"REPROVADO: ff={ff_n:.1%} < {PhysicsValidator.LIMITE_FF_MIN:.0%} "
                "(motor subdimensionado).",
            )
        return True, ""

    @staticmethod
    def validate_b_tesla(b_t: Optional[float]) -> tuple[bool, str]:
        if b_t is None:
            return True, ""
        if float(b_t) > PhysicsValidator.LIMITE_B + 1e-6:
            return (
                False,
                f"REPROVADO: B≈{float(b_t):.2f} T > {PhysicsValidator.LIMITE_B} T (saturação magnética).",
            )
        return True, ""

    @classmethod
    def ff_in_excellence_zone(cls, ff: float) -> bool:
        return cls.LIMITE_FF_IDEAL_LO <= float(ff) <= cls.LIMITE_FF_IDEAL_HI + 1e-6

    @classmethod
    def validate_winding_swap(
        cls,
        *,
        awg_original: int | float,
        awg_novo: int | float,
        parallel_original: int = 1,
        parallel_novo: int = 1,
        espiras_original: Optional[float] = None,
        espiras_novo: Optional[float] = None,
    ) -> tuple[bool, str]:
        """
        Caso de estudo: troca de bitola mantendo espiras.
        Se espiras mudaram proporcionalmente à área, pode aprovar.
        """
        a_orig = cls.total_copper_area_mm2(awg=awg_original, parallel_count=parallel_original)
        a_new = cls.total_copper_area_mm2(awg=awg_novo, parallel_count=parallel_novo)
        if (
            espiras_original is not None
            and espiras_novo is not None
            and espiras_original > 0
            and abs(float(espiras_novo) - float(espiras_original)) > 0.05
        ):
            # Compensação de espiras: validar área por espira
            a_orig_pe = a_orig * float(espiras_original)
            a_new_pe = a_new * float(espiras_novo)
            return cls.validate_wire_replacement(a_orig_pe, a_new_pe)
        return cls.validate_wire_replacement(a_orig, a_new)


@dataclass
class PhysicsValidationVerdict:
    aprovado: bool
    status: str
    diagnostico: str
    j_a_mm2: Optional[float] = None
    ff: Optional[float] = None
    delta_area_pct: Optional[float] = None
    b_tesla: Optional[float] = None
    elegivel_estrela: bool = False
    reprovado_fisicamente: bool = False
    mensagens: list[str] = field(default_factory=list)
    acao: str = ""


class PhysicsValidatorEngine(PhysicsValidator):
    """Pipeline completo para cenários antes da renderização."""

    @classmethod
    def validate_scenario_render(
        cls,
        *,
        espiras: float,
        awg: float,
        parallel_count: int = 1,
        fill_factor_ff: Optional[float] = None,
        current_density_j: Optional[float] = None,
        current_a: Optional[float] = None,
        b_tesla: Optional[float] = None,
        awg_referencia: Optional[float] = None,
        parallel_referencia: int = 1,
        espiras_referencia: Optional[float] = None,
        strict_j: bool = False,
        validate_j: bool = False,
    ) -> PhysicsValidationVerdict:
        msgs: list[str] = []
        reprovado = False

        if awg_referencia is not None:
            ok_area, msg_area = cls.validate_winding_swap(
                awg_original=awg_referencia,
                awg_novo=awg,
                parallel_original=parallel_referencia,
                parallel_novo=parallel_count,
                espiras_original=espiras_referencia,
                espiras_novo=espiras,
            )
            if not ok_area:
                reprovado = True
                msgs.append(msg_area)

        a_total = cls.total_copper_area_mm2(awg=awg, parallel_count=parallel_count)
        if validate_j and current_density_j is not None:
            j_val = float(current_density_j)
            j_lim = cls.LIMITE_J_SEVERE if strict_j else cls.LIMITE_J_MAX
            if j_val > j_lim + 1e-6:
                reprovado = True
                msgs.append(
                    f"REPROVADO: J={j_val} A/mm² > {j_lim} A/mm² "
                    "(subdimensionamento térmico / fio fino demais)."
                )
            elif j_val < cls.LIMITE_J_MIN - 1e-6:
                reprovado = True
                msgs.append(
                    f"REPROVADO: J={j_val} A/mm² < {cls.LIMITE_J_MIN} A/mm²."
                )
        elif current_a is not None and current_a > 0:
            ok_j, msg_j, j_val = cls.validate_j_density(current_a, a_total)
            if not ok_j:
                reprovado = True
                msgs.append(msg_j)
            else:
                current_density_j = j_val

        ff_val = float(fill_factor_ff) if fill_factor_ff is not None else None
        if ff_val is not None:
            ok_ff, msg_ff = cls.validate_fill_factor(ff_val)
            if not ok_ff:
                reprovado = True
                msgs.append(msg_ff)

        ok_b, msg_b = cls.validate_b_tesla(b_tesla)
        if not ok_b:
            reprovado = True
            msgs.append(msg_b)

        delta_area_pct: Optional[float] = None
        if awg_referencia is not None:
            a_ref = cls.total_copper_area_mm2(awg=awg_referencia, parallel_count=parallel_referencia)
            if a_ref > 0:
                delta_area_pct = round(abs(a_total - a_ref) / a_ref * 100, 1)

        elegivel_estrela = (
            not reprovado
            and ff_val is not None
            and cls.ff_in_excellence_zone(ff_val)
        )

        if reprovado:
            status = "REPROVADO"
            diagnostico = msgs[0] if msgs else "Violação de limite físico."
            acao = "Ajuste bitola, espiras ou paralelos até J, ff e B ficarem na faixa."
        else:
            status = "APROVADO"
            diagnostico = "Parâmetros dentro dos limites WEG/IEC."
            acao = "Pode seguir para bobina após conferência na bancada."

        return PhysicsValidationVerdict(
            aprovado=not reprovado,
            status=status,
            diagnostico=diagnostico,
            j_a_mm2=current_density_j,
            ff=ff_val,
            delta_area_pct=delta_area_pct,
            b_tesla=b_tesla,
            elegivel_estrela=elegivel_estrela,
            reprovado_fisicamente=reprovado,
            mensagens=msgs,
            acao=acao,
        )

    @classmethod
    def format_output_block(cls, verdict: PhysicsValidationVerdict) -> str:
        """Formato obrigatório de saída (texto)."""
        j_txt = f"{verdict.j_a_mm2:.3f}" if verdict.j_a_mm2 is not None else "—"
        ff_txt = (
            f"{verdict.ff * 100:.1f}%"
            if verdict.ff is not None
            else "—"
        )
        da_txt = (
            f"{verdict.delta_area_pct:.1f}%"
            if verdict.delta_area_pct is not None
            else "—"
        )
        return (
            f"STATUS: {verdict.status}\n\n"
            f"DIAGNÓSTICO TÉCNICO: {verdict.diagnostico}\n\n"
            f"MÉTRICAS:\n"
            f"- Densidade de Corrente (J): {j_txt} A/mm²\n"
            f"- Fator de Enchimento (ff): {ff_txt}\n"
            f"- Variação de Área (ΔA): {da_txt}\n\n"
            f"AÇÃO/RECOMENDAÇÃO: {verdict.acao}"
        )
