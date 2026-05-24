#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Formulário de bobinagem — monofásico vs trifásico (Gêmeo Digital)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st

from page.demo_calculo_components import render_form_block_close, render_form_block_open

MotorTipo = Literal["TRIFASICO", "MONOFASICO"]

MOTOR_TIPO_LABELS = {
    "TRIFASICO": "Trifásico",
    "MONOFASICO": "Monofásico",
}

LIGACAO_TRIFASICO_OPTS = {
    "(Informar)": "",
    "Estrela (Y)": "Estrela",
    "Triângulo (Δ)": "Triângulo",
    "Estrela / Triângulo": "Estrela-Triângulo",
}


@dataclass
class MotorWindingForm:
    tipo_motor: MotorTipo
    tensao: str
    ligacao: str
    passo_principal: str
    passo_auxiliar: str
    fio_principal: str
    espiras_principal: str
    fio_auxiliar: str
    espiras_auxiliar: str
    capacitor_uf: str

    @property
    def fio_engenheiro(self) -> str:
        return self.fio_principal

    @property
    def espiras_engenheiro(self) -> str:
        return self.espiras_principal

    def as_entrada_extra(self) -> dict[str, str]:
        return {
            "tipo_motor": self.tipo_motor,
            "passo_principal": self.passo_principal.strip(),
            "passo_auxiliar": self.passo_auxiliar.strip(),
            "passo": self.passo_principal.strip(),
            "ligacao": self.ligacao.strip(),
            "fio_engenheiro": self.fio_principal.strip(),
            "espiras_engenheiro": self.espiras_principal.strip(),
            "fio_principal": self.fio_principal.strip(),
            "espiras_principal": self.espiras_principal.strip(),
            "fio_auxiliar": self.fio_auxiliar.strip(),
            "espiras_auxiliar": self.espiras_auxiliar.strip(),
            "capacitor_uf": self.capacitor_uf.strip(),
        }


def render_motor_type_selector() -> MotorTipo:
    st.markdown('<div class="dt-motor-type">', unsafe_allow_html=True)
    choice = st.radio(
        "Tipo de motor",
        options=list(MOTOR_TIPO_LABELS.values()),
        key="demo_tipo_motor",
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return "MONOFASICO" if choice == MOTOR_TIPO_LABELS["MONOFASICO"] else "TRIFASICO"


def render_motor_winding_form() -> MotorWindingForm:
    """Seção elétrica + bobinagem conforme tipo de motor."""
    tipo = render_motor_type_selector()

    render_form_block_open("DADOS ELÉTRICOS")
    tensao = st.text_input(
        "Tensão rede (V) *",
        placeholder="—",
        key="demo_tensao",
        help="Obrigatório para FEM, densidade J e execução do gêmeo digital.",
    )
    render_form_block_close()

    ligacao = ""
    pp = pa = fio = esp = fio_a = esp_a = cap = ""

    if tipo == "TRIFASICO":
        render_form_block_open("BOBINAGEM TRIFÁSICA")
        lig_key = st.selectbox(
            "Ligação",
            list(LIGACAO_TRIFASICO_OPTS.keys()),
            key="demo_ligacao_trif",
            help="Estrela, triângulo ou dupla tensão Y/Δ.",
        )
        ligacao = LIGACAO_TRIFASICO_OPTS[lig_key]
        pp = st.text_input(
            "Passo da bobina",
            placeholder="—",
            key="demo_passo_principal",
            help="Ex.: 1-7, 10-12, 4-6-8",
        )
        c1, c2 = st.columns(2)
        with c1:
            fio = st.text_input("Fio AWG (referência)", placeholder="—", key="demo_fio")
        with c2:
            esp = st.text_input("Espiras / bobina (referência)", placeholder="—", key="demo_esp")
        render_form_block_close()
    else:
        ligacao = "Monofásico"
        st.caption("Bobina principal (trabalho) + auxiliar (partida/capacitor).")

        render_form_block_open("BOBINA PRINCIPAL")
        pp = st.text_input("Passo principal", placeholder="—", key="demo_passo_principal")
        c1, c2 = st.columns(2)
        with c1:
            fio = st.text_input("Fio AWG", placeholder="—", key="demo_fio")
        with c2:
            esp = st.text_input("Espiras", placeholder="—", key="demo_esp")
        render_form_block_close()

        render_form_block_open("BOBINA AUXILIAR · CAPACITOR")
        pa = st.text_input("Passo auxiliar", placeholder="—", key="demo_passo_auxiliar")
        c3, c4 = st.columns(2)
        with c3:
            fio_a = st.text_input("Fio AWG auxiliar", placeholder="—", key="demo_fio_aux")
        with c4:
            esp_a = st.text_input("Espiras auxiliar", placeholder="—", key="demo_esp_aux")
        cap = st.text_input(
            "Capacitor (µF)",
            placeholder="—",
            key="demo_capacitor_uf",
            help="Capacitor de partida ou permanente, se conhecido.",
        )
        render_form_block_close()

    return MotorWindingForm(
        tipo_motor=tipo,
        tensao=str(tensao or ""),
        ligacao=str(ligacao or ""),
        passo_principal=str(pp or ""),
        passo_auxiliar=str(pa or ""),
        fio_principal=str(fio or ""),
        espiras_principal=str(esp or ""),
        fio_auxiliar=str(fio_a or ""),
        espiras_auxiliar=str(esp_a or ""),
        capacitor_uf=str(cap or ""),
    )
