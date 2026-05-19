# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-19T22:49:27Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_68_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 10 | 71.4% |
| VERDE_COM_ALERTA | 1 | 7.1% |
| VERDE_SEGURO | 2 | 14.3% |
| VERMELHO_DADO_RUIM | 1 | 7.1% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **2** (**14.3%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
- **VERMELHO infra (no_keys/quota/429)**: **0** (**0.0%**) da amostra.

## Estado das chaves (ficheiro gemini_keys_status.json)

- OK sem cooldown ativo (aprox.): **28**
- Em quota_exhausted no último snapshot: **0**
- Distribuição por status: `{"ok": 28}`

## Critério automático “pronto para escalar”

- VERDE_SEGURO ≥ **75%**
- infraestrutura **VERMELHO_NO_KEYS_OU_QUOTA** relativamente **baixa**
- pelo menos **uma chave OK** utilizável (sem cooldown imediato)
- sem **quota_exhausted** generalizada no snapshot

**Resultado:** ❌ Critérios não cumpridos ou infraestrutura frágil.

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (14.3%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `baixa_confianca_local`: **12**
- `faltando_obrigatorio`: **5**

## VERDE_SEGURO (lista)

*Total: 2*

- `drive-download-20260408T000629Z-3-001_255314\21.jpg`
- `drive-download-20260408T000629Z-3-001_255314\22.jpg`

## VERDE_COM_ALERTA

*Total: 1*

- `drive-download-20260408T000629Z-3-001_255314\23.jpg`

## AMARELO_REVISAR

*Total: 10*

- `drive-download-20260408T000529Z-3-001_185960\VENTILADOR 3 VELOCIDADES.pdf`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000529Z-3-001_185960\1d217467-02db-4a7f-8017-ea2f9ac0a715.jpg`
- `drive-download-20260408T000529Z-3-001_185960\1d9b3430-0b16-4701-b724-661974ff8b49.jpg`
- `drive-download-20260408T000529Z-3-001_185960\324e6cbc-2bab-43ed-9303-2d560b1da7ec.jpg`
- `drive-download-20260408T000529Z-3-001_185960\8bc49b76-90d1-4f38-bd2f-86cd93ad3689.jpg`
- `drive-download-20260408T000529Z-3-001_185960\bda2a6e0-62ba-4738-8a58-964852f4ad8d.jpg`
- `drive-download-20260408T000529Z-3-001_185960\dc81f9cf-0541-4d2d-87c5-686e9c194c01.jpg`
- `drive-download-20260408T000529Z-3-001_185960\f837d1fb-1d86-4e42-aa6a-9eaa9c696086.jpg`
- `drive-download-20260408T000605Z-3-001_290649\arno.jpg`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 1*

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`

## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_68_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_68_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_68_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_68_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_68_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.