import re

# Constantes mantidas
CV_PARA_KW = 0.735499
KW_PARA_CV = 1.35962
RAIZ_3 = 1.73205

def extrair_primeiro_valor(valor):
    """
    Extrai o primeiro número de uma string ou lista suja.
    MELHORIA: Agora remove colchetes e aspas de forma agressiva para evitar erros de OCR.
    """
    if valor is None or str(valor).strip() in ["", "None", "null", "[]"]:
        return 0.0
    
    if isinstance(valor, (int, float)):
        return float(valor)
    
    # 1. Limpeza de caracteres de lista e formatação JSON/Python
    s = str(valor).replace("[", "").replace("]", "").replace("'", "").replace('"', "").replace("(", "").replace(")", "")
    
    # 2. Padronização de decimal (vírgula para ponto)
    s = s.replace(",", ".")
    
    # 3. Divide em delimitadores comuns para pegar apenas o primeiro valor (ex: 220/380 vira 220)
    # Acrescentado delimitadores extras para segurança
    s = re.split(r'[/|;]|\s+vs\s+|\s+e\s+|\s+-\s+', s, flags=re.IGNORECASE)[0].strip()
    
    # 4. Busca o padrão numérico (inteiro ou decimal)
    match = re.search(r"[-+]?\d*\.\d+|\d+", s)
    
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0

def alertas_validacao_projeto(dados: dict):
    """
    Analisa os dados do motor e retorna uma lista de avisos técnicos.
    ACRESCENTADO: Mapeamento completo para sincronizar com seu SQL Editor do Supabase.
    """
    alertas = []
    if not dados: 
        return ["⚠️ Dados ausentes."]

    # MAPEAMENTO REFORÇADO (Tenta nome do Banco, depois nome do Form, depois fallback)
    # Isso garante que os alertas amarelos sumam na tela de Consulta e Cadastro.
    potencia_val = extrair_primeiro_valor(
        dados.get("potencia_hp_cv") or dados.get("potencia") or dados.get("potencia_kw")
    )
    tensao_val = extrair_primeiro_valor(
        dados.get("tensao_v") or dados.get("tensao")
    )
    corrente_val = extrair_primeiro_valor(
        dados.get("corrente_nominal_a") or dados.get("corrente") or dados.get("amperagem")
    )
    rpm_val = extrair_primeiro_valor(
        dados.get("rpm_nominal") or dados.get("rpm")
    )
    frequencia_val = extrair_primeiro_valor(
        dados.get("frequencia_hz") or dados.get("frequencia")
    )

    # --- VALIDAÇÕES BÁSICAS ---
    if potencia_val <= 0: 
        alertas.append("⚠️ Potência não informada ou zero.")
    if tensao_val <= 0: 
        alertas.append("⚠️ Tensão inválida.")
    if corrente_val <= 0: 
        alertas.append("⚠️ Corrente não informada.")
    if rpm_val <= 0: 
        alertas.append("⚠️ RPM não informado.")

    # --- VALIDAÇÃO DE FREQUÊNCIA E RPM ---
    if rpm_val > 0:
        # Se for 60Hz (padrão Brasil) ou não informado (assume 60)
        if frequencia_val == 60 or frequencia_val == 0:
            if not (700 <= rpm_val <= 3650):
                alertas.append("⚠️ RPM fora da faixa industrial comum (60Hz).")
            # Faixas normais para 2, 4, 6 e 8 polos com escorregamento aceitável
            elif (3400 <= rpm_val <= 3650) or (1650 <= rpm_val <= 1850) or (1100 <= rpm_val <= 1250) or (800 <= rpm_val <= 950):
                pass 
            else:
                alertas.append("ℹ️ RPM sugere escorregamento elevado ou motor especial.")
        
        # Se for 50Hz
        elif frequencia_val == 50:
            if not (650 <= rpm_val <= 3050):
                alertas.append("⚠️ RPM fora da faixa industrial comum (50Hz).")

    # --- ALERTA DE ALTA TENSÃO ---
    if tensao_val > 1000:
        alertas.append("🔴 Risco: Tensão de Alta Voltagem detectada (>1000V).")

    return alertas

def sugerir_equivalentes_paralelos(fio_awg):
    """
    Mantida para compatibilidade com o cadastro.py.
    DICA: Você pode acrescentar sua tabela AWG aqui futuramente.
    """
    try:
        # Tenta converter para int para garantir que é um AWG válido
        awg = int(extrair_primeiro_valor(fio_awg))
        if awg <= 0: return []
        
        # Exemplo de sugestão genérica (pode ser expandido com lógica mm²)
        return [f"Sugestão: 2x fios AWG {awg + 3}", f"Cálculo baseado na seção de {awg} AWG"]
    except:
        return ["⚠️ Digite um calibre AWG válido."]
