# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-19T02:28:50Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 4 | 28.6% |
| VERDE_COM_ALERTA | 1 | 7.1% |
| VERDE_SEGURO | 6 | 42.9% |
| VERMELHO_DADO_RUIM | 3 | 21.4% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **6** (**42.9%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (42.9%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `faltando_obrigatorio`: **7**
- `baixa_confianca_local`: **7**
- `gemini_falhou:unknown_error:Extra data: line 63 column 4 (char 1544)`: **1**
- `gemini_falhou:unknown_error:Extra data: line 64 column 4 (char 1496)`: **1**

## VERDE_SEGURO (lista)

*Total: 6*

- `drive-download-20260403T124026Z-3-001_224929\605015131.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605016087.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605016201.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605017014.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605017020.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605026002.pdf`

## VERDE_COM_ALERTA

*Total: 1*

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR ESCOVA.pdf`

## AMARELO_REVISAR

*Total: 4*

- `drive-download-20260408T000443Z-3-001_253069\BOBI.PDF`
- `drive-download-20260408T000443Z-3-001_253069\EST.PDF`
- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 3*

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf`

## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.