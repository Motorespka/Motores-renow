import re

CV_PARA_KW = 0.735499
KW_PARA_CV = 1.35962
RAIZ_3 = 1.73205

def extrair_primeiro_valor(valor):
    """
    Extrai o primeiro número de uma string ou lista suja.
    Suporta formatos como: '[220, 380]', '1750 / 1450', '0.85 (60Hz)', '10hp'.
    """
    if valor is None:
        return 0.0
    
    # Se já for número, retorna direto
    if isinstance(valor, (int, float)):
        return float(valor)
    
    # Converte para string e limpa caracteres de lista/JSON que podem vir do OCR
    s = str(valor).replace("[", "").replace("]", "").replace("'", "").replace('"', "")
    
    # Substitui vírgula por ponto para padrão decimal americano
    s = s.replace(",", ".")
    
    # Divide a string em delimitadores comuns de dupla voltagem ou frequência
    # Pega apenas a primeira parte (ex: "220 / 380" vira "220")
    s = re.split(r'[/|;]|\s+vs\s+|\s+e\s+', s, flags=re.IGNORECASE)[0].strip()
    
    # Busca o primeiro padrão numérico (pode incluir sinal e ponto decimal)
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
    Compatível com as novas colunas do banco de dados.
    """
    alertas = []
    if not dados: 
        return ["⚠️ Dados ausentes."]

    # Mapeamento de chaves (Suporta o dicionário antigo e o novo padrão do banco)
    # Tenta a chave nova do banco primeiro, depois a chave simplificada do formulário
    potencia_val = extrair_primeiro_valor(dados.get("potencia_hp_cv") or dados.get("potencia"))
    tensao_val = extrair_primeiro_valor(dados.get("tensao_v") or dados.get("tensao"))
    corrente_val = extrair_primeiro_valor(dados.get("corrente_nominal_a") or dados.get("corrente"))
    rpm_val = extrair_primeiro_valor(dados.get("rpm_nominal") or dados.get("rpm"))
    frequencia_val = extrair_primeiro_valor(dados.get("frequencia_hz") or dados.get("frequencia"))

    # Validações Básicas
    if potencia_val <= 0: alertas.append("⚠️ Potência não informada ou zero.")
    if tensao_val <= 0: alertas.append("⚠️ Tensão inválida.")
    if corrente_val <= 0: alertas.append("⚠️ Corrente não informada.")
    if rpm_val <= 0: alertas.append("⚠️ RPM não informado.")

    # Validação de Frequência e RPM
    if rpm_val > 0:
        # Se for 60Hz (padrão Brasil)
        if frequencia_val == 60 or frequencia_val == 0: # 0 se não informado
            if not (700 <= rpm_val <= 3650):
                alertas.append("⚠️ RPM fora da faixa industrial comum (60Hz).")
            elif (3450 <= rpm_val <= 3650) or (1650 <= rpm_val <= 1850) or (1100 <= rpm_val <= 1250) or (800 <= rpm_val <= 950):
                pass # Faixas normais para 2, 4, 6 e 8 polos
            else:
                alertas.append("ℹ️ RPM sugere escorregamento elevado ou motor especial.")
        
        # Se for 50Hz
        elif frequencia_val == 50:
            if not (650 <= rpm_val <= 3050):
                alertas.append("⚠️ RPM fora da faixa industrial comum (50Hz).")

    # Alerta de Alta Tensão
    if tensao_val > 1000:
        alertas.append("🔴 Risco: Tensão de Alta Voltagem detectada (>1000V).")

    return alertas

def sugerir_equivalentes_paralelos(fio_awg):
    """
    Mantida para compatibilidade com o cadastro.py
    (Você deve ter a lógica original de cálculo AWG aqui)
    """
    # Exemplo simples de retorno se a lógica estiver em outro lugar
    return ["2x fios de bitola maior", "Cálculo baseado em seção mm²"]
