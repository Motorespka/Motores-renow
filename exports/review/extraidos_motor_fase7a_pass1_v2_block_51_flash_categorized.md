# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-17T18:13:17Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_51_flash_candidates.csv`

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

- `drive-download-20260403T124026Z-3-001_224929\3,4cv 4p nema56 12 60hz 45x97.1 605012196.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,4cv 4p nema56 12 60hz 60x97.4 605012248 r.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,4cv 6p iec80 23 60hz 81.5x130 606506004.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,4cv 6p iec80 23 60hz 95x81.4 605072505.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,4cv 6p iec80 234 60hz 95x81.4 605012282 r.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,4cv 6p iec80 234 60hz 95x81.4 605012282.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,4cv 6p iec90 234 60hz 89.5x90 606506405.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3,5cv 4p nema56 2 60hz 130x97.1 605012147.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3cv 4p iec90 23 60hz 120x89.4 605013170.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3cv 4p iec90 23 60hz 120x89.4 605042412.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3cv 4p iec90 23 60hz 89.4x120 605029009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\3cv 4p nema56 12 60hz 130x97.1 605012134.pdf`

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

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_51_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_51_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_51_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_51_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_51_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.