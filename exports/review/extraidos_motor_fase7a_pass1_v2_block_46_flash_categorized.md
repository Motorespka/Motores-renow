# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-16T21:03:37Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 1 | 7.1% |
| VERDE_SEGURO | 13 | 92.9% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **13** (**92.9%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

*Total: 13*

- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  1 2 CV-C 80 A -220- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  1 2 CV-C80A -110-220- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  1 2 CV-C80A -127- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  3 4 CV-C80B -110-220- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  3 4 CV-C80B -127- 6P.pdf`
- `drive-download-20260403T123335Z-3-001_145302\VOGE MONOFASICO CAP. PERMANENTE BK  3 4 CV-C80B -220- 6P.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,15cv 2p nema42 2 50,60hz 20x57.9 605013152.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,16cv 2p iec63r 23 60hz 25x49.4 605013018.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,16cv 2p iec63r 23 60hz 25x49.4 605013037.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,6cv 4p iec63 12 60hz 35x56.4 605009001.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,6cv 4p iec63r 24 60hz 40x56.4 605013180.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,7cv 4p iec63r 2 50,60hz 50x56.4 605012285.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1,8cv 2p iec63r 12 60hz 40x49.2 605042114.pdf`

## VERDE_COM_ALERTA

*Total: 0*


## AMARELO_REVISAR

*Total: 1*

- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_46_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.