# core/calculadora.py

# =====================================
# LIMPEZA DE DADOS
# =====================================

def limpar_numero(valor):
    if valor is None:
        return 0

    if isinstance(valor, str):
        valor = valor.replace(",", ".").strip()

    try:
        return float(valor)
    except:
        return 0


# =====================================
# VALIDAÇÃO DO PROJETO
# =====================================

def alertas_validacao_projeto(dados: dict):

    alertas = []

    if not dados:
        alertas.append("⚠️ Nenhum dado informado.")
        return alertas

    potencia = limpar_numero(dados.get("potencia"))
    tensao = limpar_numero(dados.get("tensao"))
    corrente = limpar_numero(dados.get("corrente"))
    rpm = limpar_numero(dados.get("rpm"))

    # ---------- CAMPOS OBRIGATÓRIOS ----------
    if potencia <= 0:
        alertas.append("⚠️ Potência não informada.")

    if tensao <= 0:
        alertas.append("⚠️ Tensão inválida.")

    if corrente <= 0:
        alertas.append("⚠️ Corrente não informada.")

    if rpm <= 0:
        alertas.append("⚠️ RPM não informado.")

    # ---------- VALORES SUSPEITOS ----------
    if potencia > 500:
        alertas.append("⚠️ Potência muito alta. Verifique unidade.")

    if tensao > 1000:
        alertas.append("⚠️ Tensão acima do normal.")

    if rpm > 5000:
        alertas.append("⚠️ RPM fora do padrão industrial.")

    return alertas


# =====================================
# CÁLCULO ELÉTRICO
# =====================================

def calcular_parametros(dados: dict):

    potencia = limpar_numero(dados.get("potencia"))
    tensao = limpar_numero(dados.get("tensao"))
    corrente = limpar_numero(dados.get("corrente"))

    resultado = {}

    if tensao > 0 and corrente > 0:
        resultado["potencia_aproximada"] = round(
            tensao * corrente * 1.732 / 1000, 2
        )

    return resultado


# =====================================
# PREPARAR DADOS PARA BANCO
# =====================================

def preparar_dados(dados: dict):

    return {
        "cliente": dados.get("cliente", "").strip(),
        "motor": dados.get("motor", "").strip(),
        "potencia": limpar_numero(dados.get("potencia")),
        "tensao": limpar_numero(dados.get("tensao")),
        "corrente": limpar_numero(dados.get("corrente")),
        "rpm": limpar_numero(dados.get("rpm")),
    }
