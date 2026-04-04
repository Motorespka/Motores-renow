import re

# =====================================
# CONSTANTES TÉCNICAS (PADRÃO ENGENHARIA)
# =====================================
CV_PARA_KW = 0.735499
KW_PARA_CV = 1.35962
RAIZ_3 = 1.73205

# =====================================
# AUXILIARES DE LIMPEZA
# =====================================

def extrair_primeiro_valor(valor):
    """
    Extrai o primeiro número de uma string (ex: '127/220V' -> 127.0).
    Essencial para motores que listam múltiplas tensões/correntes.
    """
    if valor is None: return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    
    # Remove unidades e pega o que vem antes da barra ou espaço
    string_limpa = str(valor).replace(",", ".").split('/')[0].split(' ')[0]
    # Mantém apenas números e pontos decimais
    apenas_numeros = re.sub(r'[^0-9.]', '', string_limpa)
    
    try:
        return float(apenas_numeros)
    except:
        return 0.0

# =====================================
# VALIDAÇÃO DO PROJETO (REVISADA)
# =====================================

def alertas_validacao_projeto(dados: dict):
    alertas = []
    if not dados:
        return ["⚠️ Dados ausentes."]

    # Extração inteligente para não dar erro em "127/220"
    potencia_val = extrair_primeiro_valor(dados.get("potencia"))
    tensao_val = extrair_primeiro_valor(dados.get("tensao"))
    corrente_val = extrair_primeiro_valor(dados.get("corrente"))
    rpm_val = extrair_primeiro_valor(dados.get("rpm"))

    # 1. Validação de Campos Obrigatórios
    if potencia_val <= 0: alertas.append("⚠️ Potência não informada ou zero.")
    if tensao_val <= 0: alertas.append("⚠️ Tensão inválida.")
    if corrente_val <= 0: alertas.append("⚠️ Corrente não informada.")
    if rpm_val <= 0: alertas.append("⚠️ RPM não informado.")

    # 2. Validação de Sincronismo (Pólos)
    # Engenharia: Frequência 60Hz -> RPMs padrão: 3600, 1800, 1200, 900
    if rpm_val > 0:
        if not (700 <= rpm_val <= 3650):
            alertas.append("⚠️ RPM fora da faixa industrial comum (60Hz).")
        elif rpm_val > 3550 and rpm_val < 3650:
            pass # 2 pólos OK
        elif rpm_val > 1700 and rpm_val < 1850:
            pass # 4 pólos OK
        else:
             alertas.append("ℹ️ RPM sugere escorregamento elevado ou motor especial.")

    # 3. Consistência Tensão/Corrente
    if tensao_val > 1000:
        alertas.append("🔴 Risco: Tensão de Alta Voltagem detectada.")

    return alertas

# =====================================
# CÁLCULO ELÉTRICO PROFISSIONAL
# =====================================

def calcular_parametros(dados: dict):
    """
    Calcula Rendimento e Potência baseada na placa.
    Diferencia Monofásico de Trifásico pela string de tensão.
    """
    p_nom_kw = extrair_primeiro_valor(dados.get("potencia"))
    # Se o usuário digitou "CV" na string, convertemos para kW internamente
    if "cv" in str(dados.get("potencia")).lower():
        p_nom_kw = p_nom_kw * CV_PARA_KW

    tensao = extrair_primeiro_valor(dados.get("tensao"))
    corrente = extrair_primeiro_valor(dados.get("corrente"))
    
    # Estimativa de Fator de Potência (cos phi) padrão WEG para cálculos
    cos_phi = 0.85 
    
    resultado = {}

    if tensao > 0 and corrente > 0:
        # Lógica Trifásico vs Monofásico
        # Se houver "220/380" ou "380/660" costuma ser trifásico
        e_trifasico = "/" in str(dados.get("tensao")) or tensao >= 220
        
        if e_trifasico:
            # P(kW) = (V * I * 1.732 * cos_phi) / 1000
            p_calc = (tensao * corrente * RAIZ_3 * cos_phi) / 1000
        else:
            # Monofásico: P(kW) = (V * I * cos_phi) / 1000
            p_calc = (tensao * corrente * cos_phi) / 1000
            
        resultado["potencia_calculada_kw"] = round(p_calc, 2)
        resultado["potencia_calculada_cv"] = round(p_calc * KW_PARA_CV, 2)

    return resultado

# =====================================
# SUGESTÃO DE LIGAÇÃO (PADRÃO WEG/EBERLE)
# =====================================

def sugerir_ligacao(dados: dict):
    tensao_str = str(dados.get("tensao"))
    
    if "127/220" in tensao_str:
        return "Conexão: Série (220V) ou Paralelo (127V). Comum em Monofásicos."
    if "220/380" in tensao_str:
        return "Conexão: Triângulo (220V) ou Estrela (380V). Padrão Trifásico."
    if "380/660" in tensao_str:
        return "Conexão: Triângulo (380V) ou Estrela (660V). Partida Estrela-Triângulo."
    
    return "Verificar placa de bornes para ligação específica."
