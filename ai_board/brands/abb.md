# Brand Pack: ABB

## 1) Visão geral
- Presença relevante em contextos industriais/comerciais conforme aplicação e cadeia de manutenção.
- Pode aparecer no sistema em motores, acionamentos ou conjuntos relacionados, dependendo do cadastro de origem.
- Este pack não representa canal oficial da marca.

## 2) Estilo de identificação e cadastro
- Conferir como a marca aparece em campos de marca, modelo, descrição livre e observações.
- Registrar nomenclaturas exatamente como lidas e manter normalização separada.
- Priorizar identificação por evidência (placa, etiqueta, documentação técnica, histórico de oficina).

## 3) Padrões percebidos em oficina/mercado
- Considerar variações entre linhas/séries e períodos de fabricação.
- Considerar diferenças entre dado nominal de placa e comportamento de bancada.
- Usar padrões prudentes observáveis; evitar afirmação de catálogo oficial sem fonte.

## 4) Pontos de atenção
- Erros comuns: unidade trocada, leitura parcial, campo crítico ausente e associação indevida por nome parecido.
- Não confiar apenas no nome da marca quando tensão, rpm, polos, ligação ou aplicação não fecharem.
- Em caso ambíguo, retornar para regras genéricas e solicitar validação humana.

## 5) Inconsistências comuns
- Conflito entre tipo declarado e dados elétricos preenchidos.
- Placa com ruído ou leitura incompleta gerando cadastro contraditório.
- Mistura entre características de equipamentos de famílias diferentes no mesmo registro.
- Sinais de alteração/recondicionamento sem rastreabilidade técnica suficiente.

## 6) Relação com outras marcas
- Comparar com pares do mesmo universo com base em aplicação, contexto técnico e coerência dos campos.
- Universo eletromotores: WEG, Siemens, ABB e Nidec.
- Universo motoredutores/redutores: Bonfiglioli, Nord, SEW e Cestari.
- Universo automação/acionamento: Schneider, Danfoss, Bosch Rexroth, GE, Mitsubishi e Toshiba.

## 7) Regra de cautela
- Se marca/modelo não forem suficientes, aplicar `generic_motor_rules.md` e `data_consistency_rules.md`.
- Em redutor/motoredutor, carregar também `generic_gearmotor_rules.md`.
- Em dúvida crítica de manutenção/rebobinagem, carregar `rewinding_and_workshop_rules.md` e recomendar revisão humana.
