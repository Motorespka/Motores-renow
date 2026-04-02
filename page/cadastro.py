import streamlit as st
import sqlite3
import os
from datetime import datetime

# ===============================
# FUNÇÃO PARA SALVAR MOTOR
# ===============================
def salvar_motor(motor):
    # Garantir que a pasta data exista
    os.makedirs("data", exist_ok=True)

    # Conectar ao banco na pasta data
    conn = sqlite3.connect("data/calculos.db")
    cursor = conn.cursor()

    # Criar tabela se não existir
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS motores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT,
        modelo TEXT,
        fabricante TEXT,
        potencia TEXT,
        tensao TEXT,
        corrente TEXT,
        rpm TEXT,
        frequencia TEXT,
        rendimento TEXT,
        polos TEXT,
        carcaca TEXT,
        montagem TEXT,
        isolacao TEXT,
        ip TEXT,
        regime TEXT,
        fator_servico TEXT,
        temperatura TEXT,
        altitude TEXT,
        rolamento_d TEXT,
        rolamento_t TEXT,
        eixo_diametro TEXT,
        comprimento_eixo TEXT,
        peso TEXT,
        ventilacao TEXT,
        tipo_enrolamento TEXT,
        passo_bobina TEXT,
        numero_ranhuras TEXT,
        fios_paralelos TEXT,
        diametro_fio TEXT,
        tipo_fio TEXT,
        ligacao TEXT,
        esquema TEXT,
        resistencia TEXT,
        diametro_interno TEXT,
        diametro_externo TEXT,
        comprimento_pacote TEXT,
        material_nucleo TEXT,
        tipo_chapa TEXT,
        empilhamento TEXT,
        observacoes TEXT,
        origem_calculo TEXT,
        data_cadastro TEXT
    )
    """)

    # Adicionar data de cadastro automaticamente
    motor["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Inserir motor
    cursor.execute("""
    INSERT INTO motores (
        marca, modelo, fabricante, potencia, tensao, corrente, rpm, frequencia, rendimento,
        polos, carcaca, montagem, isolacao, ip, regime, fator_servico, temperatura, altitude,
        rolamento_d, rolamento_t, eixo_diametro, comprimento_eixo, peso, ventilacao,
        tipo_enrolamento, passo_bobina, numero_ranhuras, fios_paralelos, diametro_fio, tipo_fio,
        ligacao, esquema, resistencia, diametro_interno, diametro_externo, comprimento_pacote,
        material_nucleo, tipo_chapa, empilhamento, observacoes, origem_calculo, data_cadastro
    ) VALUES (
        :marca, :modelo, :fabricante, :potencia, :tensao, :corrente, :rpm, :frequencia, :rendimento,
        :polos, :carcaca, :montagem, :isolacao, :ip, :regime, :fator_servico, :temperatura, :altitude,
        :rolamento_d, :rolamento_t, :eixo_diametro, :comprimento_eixo, :peso, :ventilacao,
        :tipo_enrolamento, :passo_bobina, :numero_ranhuras, :fios_paralelos, :diametro_fio, :tipo_fio,
        :ligacao, :esquema, :resistencia, :diametro_interno, :diametro_externo, :comprimento_pacote,
        :material_nucleo, :tipo_chapa, :empilhamento, :observacoes, :origem_calculo, :data_cadastro
    )
    """, motor)

    conn.commit()
    conn.close()
