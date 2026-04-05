"""
Consultas ao Supabase com cache (st.cache_data) para reduzir idas ao servidor.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from supabase import Client

MotorRow = Dict[str, Any]


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs={Client: lambda _c: "supabase-client"},
)
def fetch_motores_cached(supabase: Client) -> List[MotorRow]:
    res = supabase.table("motores").select("*").order("id", desc=True).execute()
    return res.data or []


def clear_motores_cache() -> None:
    try:
        fetch_motores_cached.clear()
    except Exception:
        pass
def obter_configuracoes_ligacao(motor_data: dict) -> str:
    """
    Retorna uma string descrevendo as configurações de ligação de cabos
    com base nos dados do motor (tipo, tensões), focando na lógica de ligação.
    """
    fases = motor_data.get('fases') # Espera 1 ou 3
    tensao_v_str = motor_data.get('tensao_v', '') # String com as tensões (ex: "220/380V", "127V", "220/380/440V")
    
    configs = []
    
    # --- Lógica para Motores Monofásicos (fases == 1) ---
    if fases == 1:
        tensões_suportadas = sorted([t.strip().replace('v', '').replace('V', '') 
                                     for t in tensao_v_str.replace('/', ' ').replace(',', ' ').split() 
                                     if t.strip().isdigit()])
        
        if not tensões_suportadas:
            configs.append(f"Motor Monofásico. Tensão não especificada ('{tensao_v_str}'). Consulte o manual.")
        elif len(tensões_suportadas) == 1:
            configs.append(f"Tensão única {tensões_suportadas[0]}V. A ligação interna já está configurada para esta tensão.")
        elif len(tensões_suportadas) >= 2:
            configs.append(f"**Para {tensões_suportadas[0]}V:** Ligar enrolamentos em série (consulte o diagrama específico).")
            configs.append(f"**Para {tensões_suportadas[1]}V:** Ligar enrolamentos em paralelo (consulte o diagrama específico).")
            if len(tensões_suportadas) > 2:
                configs.append(f"Tensões adicionais encontradas: {', '.join(tensões_suportadas[2:])}. Verifique o diagrama.")
        else:
            configs.append(f"Motor Monofásico com tensões não especificadas ('{tensao_v_str}'). Consulte o manual.")

    # --- Lógica para Motores Trifásicos (fases == 3) ---
    elif fases == 3:
        tensões_suportadas = sorted([t.strip().replace('v', '').replace('V', '') 
                                     for t in tensao_v_str.replace('/', ' ').replace(',', ' ').split() 
                                     if t.strip().isdigit()])

        if not tensões_suportadas:
             configs.append(f"Motor Trifásico. Tensão não especificada ('{tensao_v_str}'). Consulte o manual do fabricante.")
        else:
            tensões_ordenadas = sorted(tensões_suportadas, key=int)

            if "220" in tensões_ordenadas and "380" in tensões_ordenadas:
                configs.append(f"Para 220V: Ligar em **Triângulo (Δ)**.")
                configs.append(f"Para 380V: Ligar em **Estrela (Y)**.")
            
            if "380" in tensões_ordenadas and "660" in tensões_ordenadas:
                configs.append(f"Para 380V: Ligar em **Triângulo (Δ)**.")
                configs.append(f"Para 660V: Ligar em **Estrela (Y)**.")

            if "220" in tensões_ordenadas and "380" in tensões_ordenadas and "440" in tensões_ordenadas:
                configs.append(f"Para 220V: Ligar em **Triângulo (Δ)**.")
                configs.append(f"Para 380V: Ligar em **Estrela (Y)**.")
                configs.append(f"Para 440V: Ligar em **Estrela (Y)** (configuração específica para 440V).")
            
            tensões_mapadas = set()
            if "220" in tensões_ordenadas: tensões_mapadas.add("220")
            if "380" in tensões_ordenadas: tensões_mapadas.add("380")
            if "440" in tensões_ordenadas: tensões_mapadas.add("440")
            if "660" in tensões_ordenadas: tensões_mapadas.add("660")
            
            tensões_nao_mapeadas = [t for t in tensões_suportadas if t not in tensões_mapadas]
            if tensões_nao_mapeadas:
                 configs.append(f"Outras tensões suportadas: {', '.join(tensões_nao_mapeadas)}. Consulte o diagrama para ligações específicas.")

            if len(tensões_suportadas) == 1:
                tensao = tensões_suportadas[0]
                if tensao == "220": configs.append(f"Tensão única 220V: Geralmente ligado em **Triângulo (Δ)**.")
                elif tensao == "380": configs.append(f"Tensão única 380V: Geralmente ligado em **Estrela (Y)**.")
                elif tensao == "440": configs.append(f"Tensão única 440V: Geralmente ligado em **Estrela (Y)**.")
                elif tensao == "660": configs.append(f"Tensão única 660V: Geralmente ligado em **Estrela (Y)**.")
                else: configs.append(f"Tensão única {tensao}V. Consulte o diagrama de ligação.")

    else:
        configs.append(f"Tipo de motor não especificado ou desconhecido (Fases: {fases}). Consulte o manual.")

    return "\n".join(configs)
import streamlit as st
import re

# Importar a função de obter configurações de ligação
from utils.configuracoes_motor import obter_configuracoes_ligacao 

# Importar funções de serviço para buscar dados
from services.supabase_data import get_motores_resumidos, get_detalhes_motor, clear_motores_cache

# --- Funções Auxiliares ---
def format_label(text):
    """Formata um label para exibição mais amigável."""
    return text.replace('_', ' ').title()

def show_motor_details_modal(motor_data, supabase_client):
    """Exibe os detalhes completos do motor em um diálogo modal."""
    detalhes_motor = get_detalhes_motor(supabase_client, motor_data.get('id'))

    if not detalhes_motor:
        st.error("Não foi possível carregar os detalhes deste motor.")
        return

    # Obtém a string de configuração de ligação
    config_ligacao = obter_configuracoes_ligacao(detalhes_motor)

    with st.dialog(f"Detalhes do Motor: {detalhes_motor.get('modelo', 'Desconhecido')} (ID: {detalhes_motor.get('id', 'N/A')})"):
        st.header("Informações Gerais e Elétricas")
        st.write(f"**Fabricante:** {detalhes_motor.get('fabricante', 'N/A')}")
        st.write(f"**Marca:** {detalhes_motor.get('marca', 'N/A')}")
        st.write(f"**Modelo:** {detalhes_motor.get('modelo', 'N/A')}")
        st.write(f"**Número de Série:** {detalhes_motor.get('num_serie', 'N/A')}")
        st.write(f"**Norma:** {detalhes_motor.get('norma', 'N/A')}")
        
        fases = detalhes_motor.get('fases')
        tipo_motor_str = "Desconhecido"
        if fases == 1: tipo_motor_str = "Monofásico"
        elif fases == 3: tipo_motor_str = "Trifásico"
        st.write(f"**Fases:** {fases} ({tipo_motor_str})")
        
        st.write(f"**Potência:** {detalhes_motor.get('potencia_hp_cv', 'N/A')} CV ({detalhes_motor.get('potencia_kw', 'N/A')} kW)")
        st.write(f"**Tensão Nominal:** {detalhes_motor.get('tensao_v', 'N/A')} V")
        st.write(f"**Corrente Nominal:** {detalhes_motor.get('corrente_nominal_a', 'N/A')} A")
        st.write(f"**RPM Nominal:** {detalhes_motor.get('rpm_nominal', 'N/A')}")
        st.write(f"**Frequência:** {detalhes_motor.get('frequencia_hz', 'N/A')} Hz")
        st.write(f"**Polos:** {detalhes_motor.get('polos', 'N/A')}")
        st.write(f"**Fator de Serviço:** {detalhes_motor.get('fator_servico', 'N/A')}")
        st.write(f"**Fator de Potência (cos φ):** {detalhes_motor.get('fator_potencia_cos_phi', 'N/A')}")
        st.write(f"**Rendimento:** {detalhes_motor.get('rendimento_perc', 'N/A')}% ({detalhes_motor.get('classe_isolacao', 'N/A')})") # Adicionado Classe Isolamento aqui

        st.divider()

        st.header("Configurações de Ligação de Cabos")
        st.markdown(f"_{config_ligacao}_") # Exibe a string retornada pela função utilitária

        st.divider()

        # Abas para Detalhes Técnicos
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Bobinagem",
            "Fios (Principal/Aux.)",
            "Componentes",
            "Mecânica",
            "Operação",
            "Extras e Links"
        ])

        with tab1: # Bobinagem
            st.subheader("Dados de Bobinagem")
            st.write(f"**Número de Ranhuras:** {detalhes_motor.get('numero_ranhuras', 'N/A')}")
            st.write(f"**Tipo de Enrolamento:** {detalhes_motor.get('tipo_enrolamento', 'N/A')}")
            st.write(f"**Fios em Paralelo:** {detalhes_motor.get('fios_paralelos', 'N/A')}")
            st.write(f"**Ligação Interna:** {detalhes_motor.get('ligacao_interna', 'N/A')}") 
            st.write(f"**Resistência (Ohm/Fase):** {detalhes_motor.get('resistencia_ohm_fase', 'N/A')}")
            st.write(f"**Tipo de Fio:** {detalhes_motor.get('tipo_fio', 'N/A')}")

        with tab2: # Fios (Principal/Auxiliar)
            st.subheader("Detalhes dos Fios")
            st.write(f"**Passo Principal:** {detalhes_motor.get('passo_principal', 'N/A')}")
            st.write(f"**Espiras Principal:** {detalhes_motor.get('espiras_principal', 'N/A')}")
            st.write(f"**Bitola Fio Principal:** {detalhes_motor.get('bitola_fio_principal', 'N/A')} mm")
            st.write(f"**Peso Cobre Principal:** {detalhes_motor.get('peso_cobre_principal_kg', 'N/A')} kg")
            
            st.write(f"**Passo Auxiliar:** {detalhes_motor.get('passo_auxiliar', 'N/A')}")
            st.write(f"**Espiras Auxiliar:** {detalhes_motor.get('espiras_auxiliar', 'N/A')}")
            st.write(f"**Bitola Fio Auxiliar:** {detalhes_motor.get('bitola_fio_auxiliar', 'N/A')} mm")
            st.write(f"**Peso Cobre Auxiliar:** {detalhes_motor.get('peso_cobre_auxiliar_kg', 'N/A')} kg")

        with tab3: # Componentes
            st.subheader("Componentes Adicionais")
            st.write(f"**Capacitor de Partida:** {detalhes_motor.get('capacitor_partida', 'N/A')}")
            st.write(f"**Capacitor Permanente:** {detalhes_motor.get('capacitor_permanente', 'N/A')}")
            st.write(f"**Chave Centrifuga/Platinado:** {detalhes_motor.get('tipo_centrifugo_platinado', 'N/A')}")
            st.write(f"**Proteção Térmica:** {detalhes_motor.get('protecao_termica', 'N/A')}")

        with tab4: # Mecânica/Carcaça
            st.subheader("Carcaça e Mecânica")
            st.write(f"**Carcaça:** {detalhes_motor.get('carcaca', 'N/A')}")
            st.write(f"**Diâmetro Interno Estator:** {detalhes_motor.get('diametro_interno_estator_mm', 'N/A')} mm")
            st.write(f"**Diâmetro Externo Estator:** {detalhes_motor.get('diametro_externo_estator_mm', 'N/A')} mm")
            st.write(f"**Comprimento do Pacote do Núcleo:** {detalhes_motor.get('comprimento_pacote_mm', 'N/A')} mm")
            st.write(f"**Material do Núcleo:** {detalhes_motor.get('material_nucleo', 'N/A')}")
            st.write(f"**Rolamento Dianteiro:** {detalhes_motor.get('rolamento_dianteiro', 'N/A')}")
            st.write(f"**Rolamento Traseiro:** {detalhes_motor.get('rolamento_traseiro', 'N/A')}")
            st.write(f"**Tipo de Graxa:** {detalhes_motor.get('tipo_graxa', 'N/A')}")

        with tab5: # Operação
            st.subheader("Condições de Operação")
            st.write(f"**Grau de Proteção (IP):** {detalhes_motor.get('grau_protecao_ip', 'N/A')}")
            # Classe de isolamento já foi mostrado na seção Elétrica/Potência para evitar repetição
            st.write(f"**Regime de Serviço:** {detalhes_motor.get('regime_servico', 'N/A')}")
            st.write(f"**Sentido de Rotação:** {detalhes_motor.get('sentido_rotacao', 'N/A')}")
            st.write(f"**Peso Total:** {detalhes_motor.get('peso_total_kg', 'N/A')} kg")
            
            st.subheader("Parâmetros de Performance")
            st.write(f"**Categoria de Torque:** {detalhes_motor.get('categoria_torque', 'N/A')}")
            st.write(f"**Relação IP/IR:** {detalhes_motor.get('ip_in_ratio', 'N/A')}")
            st.write(f"**Relação IS/IR:** {detalhes_motor.get('is_in_ratio', 'N/A')}")
            st.write(f"**Relação TP/TN:** {detalhes_motor.get('tp_tn_ratio', 'N/A')}")
            st.write(f"**Relação Tmax/Tn:** {detalhes_motor.get('tmax_tn_ratio', 'N/A')}")
            st.write(f"**Tempo Rotor Bloqueado (s):** {detalhes_motor.get('tempo_rotor_bloqueado_s', 'N/A')}")
            st.write(f"**Escorregamento (%):** {detalhes_motor.get('escorregamento_perc', 'N/A')}")

        with tab6: # Extras e Links
            st.subheader("Informações Adicionais e Links")
            st.write(f"**Especificações Extras:** {detalhes_motor.get('especificacoes_extra', 'N/A')}")
            
            link_foto = detalhes_motor.get('url_foto_placa')
            if link_foto and link_foto != 'N/A':
                st.markdown(f"**Foto da Placa:** [Ver Foto]({link_foto})")
            else:
                st.info("Foto da placa não disponível.")
            
            link_desenho = detalhes_motor.get('url_desenho_tecnico')
            if link_desenho and link_desenho != 'N/A':
                st.markdown(f"**Desenho Técnico:** [Ver Desenho]({link_desenho})")
            else:
                st.info("Desenho técnico não disponível.")

        st.divider()

        # Campo geral de observações
        if detalhes_motor.get('observacoes_adicionais') and detalhes_motor.get('observacoes_adicionais') != 'N/A':
            st.subheader("Observações Gerais")
            st.write(detalhes_motor['observacoes_adicionais'])


def show(supabase):
    st.title("🔍 Consulta de Motores")
    
    # --- Busca de Motores ---
    motores_resumidos = get_motores_resumidos(supabase) 

    if motores_resumidos is None: 
        st.error("Não foi possível carregar os dados dos motores. Tente novamente mais tarde.")
        return
    if not motores_resumidos:
        st.info("Nenhum motor encontrado no banco de dados.")
        return

    # --- Organização da Tela ---
    try:
        cols = st.columns(3) 
        num_cols_layout = 3
    except Exception:
        cols = [st] 
        num_cols_layout = 1

    col_idx = 0

    # --- Renderização dos Cards ---
    for motor in motores_resumidos:
        card = MotorCard(
            motor_data=motor,
            supabase_client=supabase,
            col=cols[col_idx % num_cols_layout] 
        )
        # Substitui a chamada direta por uma que usa a função modal
        if card.col.button(f"Ver Detalhes - {motor.get('modelo', 'Motor')}", key=f"detalhes_{motor.get('id')}"):
             show_motor_details_modal(motor, supabase)
        
        col_idx += 1

    # NOTA: Esta implementação assume que o MotorCard.display() original está sendo modificado 
    # para apenas mostrar as informações resumidas e o botão.
    # Se o seu MotorCard.display() já tem a lógica de modal, ajuste esta parte.
    # Para este exemplo, estamos controlando o modal diretamente aqui na página de consulta.
# services/supabase_data.py

from __future__ import annotations
from typing import Any, Dict, List

import streamlit as st
from supabase import Client

# Mapeamento dos nomes das colunas da sua tabela para facilitar o uso
NOME_TABELA_MOTORES = "motores" 

# Campos essenciais para o resumo do card
CAMPOS_RESUMO_CARD = "id, marca, modelo, potencia_hp_cv, potencia_kw, rpm_nominal, fases, tensao_v, polos"

# String com TODOS os campos para detalhes completos (AJUSTE CONFORME SEU BANCO DE DADOS)
CAMPOS_DETALHES_COMPLETOS = """
id, fabricante, marca, modelo, num_serie, norma, fases, data_fabricacao, 
potencia_hp_cv, potencia_kw, tensao_v, corrente_nominal_a, rpm_nominal, frequencia_hz, polos, rendimento_perc, fator_potencia_cos_phi, fator_servico, 
categoria_torque, ip_in_ratio, is_in_ratio, tp_tn_ratio, tmax_tn_ratio, tempo_rotor_bloqueado_s, escorregamento_perc, 
numero_ranhuras, tipo_enrolamento, fios_paralelos, ligacao_interna, resistencia_ohm_fase, tipo_fio, 
passo_principal, espiras_principal, bitola_fio_principal, peso_cobre_principal_kg, passo_auxiliar, espiras_auxiliar, bitola_fio_auxiliar, peso_cobre_auxiliar_kg, 
capacitor_partida, capacitor_permanente, tipo_centrifugo_platinado, protecao_termica, 
carcaca, diametro_interno_estator_mm, diametro_externo_estator_mm, comprimento_pacote_mm, material_nucleo, rolamento_dianteiro, rolamento_traseiro, tipo_graxa, 
grau_protecao_ip, classe_isolacao, regime_servico, sentido_rotacao, peso_total_kg, 
especificacoes_extra, url_foto_placa, url_desenho_tecnico, observacoes_adicionais
"""

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={'Client': lambda _c: "supabase-client"})
def get_motores_resumidos(supabase: Client) -> List[MotorRow] | None:
    """Busca os dados resumidos dos motores para a lista de cards."""
    try:
        res = supabase.table(NOME_TABELA_MOTORES).select(CAMPOS_RESUMO_CARD).order("id", desc=True).execute()
        
        if res.data:
            dados_limpos = []
            for motor in res.data:
                motor_limpo = {}
                for key_resumo in CAMPOS_RESUMO_CARD.split(','):
                    key = key_resumo.strip()
                    value = motor.get(key)
                    if value is None:
                        motor_limpo[key] = 'N/A'
                    else:
                        motor_limpo[key] = value
                dados_limpos.append(motor_limpo)
            return dados_limpos
        else:
            return []
    except Exception as e:
        st.error(f"Erro ao buscar motores resumidos: {e}")
        return None

def clear_motores_cache() -> None:
    """Limpa o cache das funções de busca de motores."""
    try:
        get_motores_resumidos.clear()
        # get_detalhes_motor.clear() # Descomente se get_detalhes_motor também usar @st.cache_data
    except Exception:
        pass

@st.cache_data(ttl=3600, show_spinner=False, hash_funcs={'Client': lambda _c: "supabase-client"})
def get_detalhes_motor(supabase: Client, motor_id: int) -> MotorRow | None:
    """Busca TODOS os detalhes de um motor específico pelo seu ID."""
    try:
        res = supabase.table(NOME_TABELA_MOTORES).select(CAMPOS_DETALHES_COMPLETOS).eq("id", motor_id).execute()
        
        if res.data and len(res.data) > 0:
            detalhes = res.data[0]
            for key, value in detalhes.items():
                if value is None:
                    detalhes[key] = 'N/A'
            return detalhes
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao buscar detalhes do motor ID {motor_id}: {e}")
        return None
