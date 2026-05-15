# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-15T21:44:43Z`
- Últimas linhas analisadas (bundle): **20**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 5 | 45.5% |
| VERDE_COM_ALERTA | 2 | 18.2% |
| VERDE_SEGURO | 1 | 9.1% |
| VERMELHO_DADO_RUIM | 3 | 27.3% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **1** (**9.1%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
- **VERMELHO infra (no_keys/quota/429)**: **0** (**0.0%**) da amostra.

## Estado das chaves (ficheiro gemini_keys_status.json)

- OK sem cooldown ativo (aprox.): **24**
- Em quota_exhausted no último snapshot: **0**
- Distribuição por status: `{"ok": 24, "unknown_error": 4}`

## Critério automático “pronto para escalar”

- VERDE_SEGURO ≥ **75%**
- infraestrutura **VERMELHO_NO_KEYS_OU_QUOTA** relativamente **baixa**
- pelo menos **uma chave OK** utilizável (sem cooldown imediato)
- sem **quota_exhausted** generalizada no snapshot

**Resultado:** ❌ Critérios não cumpridos ou infraestrutura frágil.

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (9.1%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `baixa_confianca_local`: **7**
- `faltando_obrigatorio`: **7**
- `gemini_falhou:unknown_error:Extra data: line 63 column 4 (char 1389)`: **1**

## VERDE_SEGURO (lista)

*Total: 1*

- `drive-download-20260408T000511Z-3-001_428675\ventilador de ar.pdf`

## VERDE_COM_ALERTA

*Total: 2*

- `drive-download-20260408T000443Z-3-001_253069\TC.PDF`
- `drive-download-20260408T000511Z-3-001_428675\60HZ_VENT-AVIARIO_MOTO-FRICCAO.pdf`

## AMARELO_REVISAR

*Total: 5*

- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 3.pdf`
- `drive-download-20260408T000529Z-3-001_185960\VENTILADOR 3 VELOCIDADES.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 3*

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR EB.pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR ESCOVA.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf`

## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.