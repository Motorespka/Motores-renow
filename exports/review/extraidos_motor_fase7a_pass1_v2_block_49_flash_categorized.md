# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-17T17:48:05Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_49_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 1 | 7.1% |
| VERDE_COM_ALERTA | 1 | 7.1% |
| VERDE_SEGURO | 12 | 85.7% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **12** (**85.7%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

**Resultado:** ✅ Critérios numéricos principais OK.

**Recomendação:** **Critérios mínimos numéricos cumpridos**, mas rever infraestrutura (OCR local + quotas) antes do lote 1100.

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `faltando_obrigatorio`: **1**

## VERDE_SEGURO (lista)

*Total: 12*

- `drive-download-20260403T124026Z-3-001_224929\1cv 6p iec90 2 60hz 110x89.4 605042418.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1cv 6p iec90 234 60hz 89.5x130 606506406.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1cv 8p iec90 23 60hz 110x89.4 605013254.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1cv 8p iec90 234 60hz 120x89.4 605012358 r.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1cv 8p iec90 234 60hz 120x89.4 605012358.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 2p iec63r 23 60hz 80x49.4 605012125.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 2p iec80 1 50hz 61.2x70 506000009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 2p nema48 23 60hz 80x71.7 605012332.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 4p iec90 2 60hz 100x89.4 605013248.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 4p iec90 23 50,60hz 120x89.4 605012268 r.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 4p iec90 23 50,60hz 120x89.4 605012268.pdf`
- `drive-download-20260403T124026Z-3-001_224929\2cv 4p iec90 23 60hz 100x89.4 605013169.pdf`

## VERDE_COM_ALERTA

*Total: 1*

- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2,4p iec63r 2 260,150hz 70x56.4 605012237.pdf`

## AMARELO_REVISAR

*Total: 1*

- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_49_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_49_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_49_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_49_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_49_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.