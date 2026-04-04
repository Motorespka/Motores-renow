import re

CV_PARA_KW = 0.735499
KW_PARA_CV = 1.35962
RAIZ_3 = 1.73205

def extrair_primeiro_valor(valor):
    """Extrai o primeiro número de uma string ou lista suja (ex: '[127, 220]' -> 127.0)."""
    if valor is None or str(valor).strip() == "": 
        return 0.0
    if isinstance(valor, (int, float)): 
        return float(valor)
    
    # Limpeza profunda: remove colchetes e substitui vírgula por ponto
    s = str(valor).replace("[", "").replace("]", "").replace(",", ".")
    
    # Pega a primeira parte antes de qualquer barra, espaço ou ponto e vírgula
    s = s.split('/')[0].split(';')[0].split(' ')[0].strip()
    
    # Mantém apenas números e o primeiro ponto decimal encontrado
    apenas_numeros = re.findall(r"[-+]?\d*\.\d+|\d+", s)
    
    try:
        return float(apenas_numeros[0]) if apenas_numeros else 0.0
    except:
        return 0.0

def alertas_validacao_projeto(dados: dict):
    alertas = []
    if not dados: return ["⚠️ Dados ausentes."]

    # Usando a nova extração robusta
    potencia_val = extrair_primeiro_valor(dados.get("potencia") or dados.get("potencia_hp_cv"))
    tensao_val = extrair_primeiro_valor(dados.get("tensao") or dados.get("tensao_v"))
    corrente_val = extrair_primeiro_valor(dados.get("corrente") or dados.get("corrente_nominal_a"))
    rpm_val = extrair_primeiro_valor(dados.get("rpm") or dados.get("rpm_nominal"))

    if potencia_val <= 0: alertas.append("⚠️ Potência não informada ou zero.")
    if tensao_val <= 0: alertas.append("⚠️ Tensão inválida.")
    if corrente_val <= 0: alertas.append("⚠️ Corrente não informada.")
    if rpm_val <= 0: alertas.append("⚠️ RPM não informado.")

    if rpm_val > 0:
        if not (700 <= rpm_val <= 3650):
            alertas.append("⚠️ RPM fora da faixa industrial comum (60Hz).")
        elif 3550 <= rpm_val <= 3650 or 1700 <= rpm_val <= 1850:
            pass 
        else:
            alertas.append("ℹ️ RPM sugere escorregamento elevado ou motor especial.")

    if tensao_val > 1000:
        alertas.append("🔴 Risco: Tensão de Alta Voltagem detectada.")

    return alertas

# Mantenha as funções calcular_parametros e sugerir_ligacao/sugerir_equivalentes_paralelos como estão
