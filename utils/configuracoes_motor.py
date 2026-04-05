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
