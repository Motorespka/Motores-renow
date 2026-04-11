def diagnostico_motor(dados, engenharia, fabrica):

    avisos = []

    corrente = dados.get("corrente")
    potencia = fabrica.get("potencia_kw")

    if not corrente or not potencia:
        return ["Dados insuficientes"]

    try:
        corrente = float(corrente.replace(",", "."))
    except:
        return ["Corrente inválida"]

    # ======================
    # SUPER AQUECIMENTO
    # ======================
    if corrente > 15:
        avisos.append("⚠️ Possível superaquecimento")

    # ======================
    # ESPIRAS BAIXAS
    # ======================
    espiras = engenharia.get("media_espiras")

    if espiras and espiras < 20:
        avisos.append("⚠️ Espiras baixas → risco de alta corrente")

    # ======================
    # POLARIDADE
    # ======================
    rpm = dados.get("rpm")

    if rpm and "3500" in rpm and espiras and espiras > 60:
        avisos.append("⚠️ Espiras altas para motor 2 polos")

    # ======================
    # TORQUE
    # ======================
    if corrente < 2:
        avisos.append("⚠️ Possível falta de torque")

    if not avisos:
        avisos.append("🟢 Motor dentro do padrão técnico")

    return avisos
