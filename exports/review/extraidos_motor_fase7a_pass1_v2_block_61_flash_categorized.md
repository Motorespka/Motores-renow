# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-19T02:47:05Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 6 | 42.9% |
| VERDE_COM_ALERTA | 3 | 21.4% |
| VERDE_SEGURO | 2 | 14.3% |
| VERMELHO_DADO_RUIM | 3 | 21.4% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **2** (**14.3%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (14.3%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `baixa_confianca_local`: **13**
- `faltando_obrigatorio`: **6**
- `gemini_falhou:unknown_error:Extra data: line 63 column 4 (char 1544)`: **1**
- `gemini_falhou:unknown_error:Extra data: line 64 column 4 (char 1496)`: **1**

## VERDE_SEGURO (lista)

*Total: 2*

- `drive-download-20260408T000529Z-3-001_185960\6bbe2fd4-7adf-44a6-bdde-b89413fd6628.jpg`
- `drive-download-20260408T000529Z-3-001_185960\7a381ec7-685e-4eb4-bf68-a2470fcf7637.jpg`

## VERDE_COM_ALERTA

*Total: 3*

- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000529Z-3-001_185960\0b36da0a-68fa-411f-8d98-42612aac07cd.jpg`
- `drive-download-20260408T000529Z-3-001_185960\80dae8d4-2a6d-4153-8b6c-c84b919e1600.jpg`

## AMARELO_REVISAR

*Total: 6*

- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 3.pdf`
- `drive-download-20260408T000529Z-3-001_185960\1d217467-02db-4a7f-8017-ea2f9ac0a715.jpg`
- `drive-download-20260408T000529Z-3-001_185960\1d9b3430-0b16-4701-b724-661974ff8b49.jpg`
- `drive-download-20260408T000529Z-3-001_185960\324e6cbc-2bab-43ed-9303-2d560b1da7ec.jpg`
- `drive-download-20260408T000529Z-3-001_185960\8bc49b76-90d1-4f38-bd2f-86cd93ad3689.jpg`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 3*

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf`

## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.