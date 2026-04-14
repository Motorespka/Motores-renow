from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from utils.motor_view import display_subtitle, display_title, friendly, pick_value


def render_motor_card(motor: Dict[str, Any]) -> str | None:
    motor_id = motor.get("id")
    title = display_title(motor)
    subtitle = display_subtitle(motor)
    power = friendly(pick_value(motor, ["potencia_hp_cv", "potencia", "potencia_kw"]))
    rpm = friendly(pick_value(motor, ["rpm_nominal", "rpm"]))

    st.markdown("---")
    st.markdown(f"### {title}")
    st.caption(subtitle)
    c1, c2 = st.columns(2)
    c1.write(f"**Potência:** {power}")
    c2.write(f"**RPM:** {rpm}")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Detalhes", key=f"detail_{motor_id}", use_container_width=True):
            return "detail"
    with b2:
        if st.button("Editar", key=f"edit_{motor_id}", use_container_width=True):
            return "edit"
    return None
