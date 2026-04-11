import os
import importlib
import streamlit as st

PASTA = "services"

def executar_modulos(dados, engenharia, fabrica):

    for arquivo in os.listdir(PASTA):

        if arquivo.startswith("mod_") and arquivo.endswith(".py"):

            nome = arquivo[:-3]

            modulo = importlib.import_module(f"services.{nome}")

            if hasattr(modulo, "executar"):

                st.divider()
                st.write(f"Executando módulo: {nome}")

                modulo.executar(
                    dados,
                    engenharia,
                    fabrica
                )
