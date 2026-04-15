# Nameplate Reading Rules

## Objetivo
Ler placa com cautela, preservar rastreabilidade e reduzir erro por ruído/ambiguidade.

## Princípios de extração
- Capturar texto bruto e versão normalizada separadamente.
- Não forçar leitura quando caracteres/símbolos estiverem ambíguos.
- Tratar layouts diferentes por fabricante e época como fonte de variação esperada.
- Considerar placas antigas vs modernas sem assumir equivalência direta de nomenclatura.

## Erros comuns de leitura
- confusão visual entre 0/O, 1/I, 5/S, 8/B;
- troca de unidade (CV, kW, A, Hz, rpm);
- leitura parcial de tensão múltipla e ligação;
- interpretação incorreta de campos implícitos.

## Processo recomendado
1. Extrair campos evidentes.
2. Marcar campos duvidosos.
3. Cruzar com coerência técnica geral.
4. Classificar confiança da leitura.
5. Recomendar confirmação humana quando ambiguidade afetar decisão.
