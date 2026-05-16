# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-16T21:18:56Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 1 | 7.1% |
| VERDE_COM_ALERTA | 4 | 28.6% |
| VERDE_SEGURO | 9 | 64.3% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **9** (**64.3%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (64.3%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `faltando_obrigatorio`: **1**

## VERDE_SEGURO (lista)

*Total: 9*

- `drive-download-20260403T124026Z-3-001_224929\1.25cv 4p nema56 12 60hz 90x97.4 605042351.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2p iec90 23 60hz 74.4x65 605038017.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 4p iec80 23 60hz 95x82 605029007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 4p nema56 12 60hz 85x97.1 605012198.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 4p nema56 24 60hz 90x97.4 605012255.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 6p iec100 234 60hz 150x97.5 606506408.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 6p iec90 23 60hz 110x89.4 605088507 r.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 6p iec90 23 60hz 110x89.4 605088507.pdf`
- `drive-download-20260403T124026Z-3-001_224929\10cv 2p iec132 234 60hz 112x140 606502419.pdf`

## VERDE_COM_ALERTA

*Total: 4*

- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2,4p iec63r 2 260,150hz 70x56.4 605012237.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2p iec63r 2 260hz 30x48.8 605012162.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2p iec63r 2 260hz 30x48.8 605012206.pdf`
- `drive-download-20260403T124026Z-3-001_224929\1.5cv 4p iec63r 2 150hz 50x56.4 605012172.pdf`

## AMARELO_REVISAR

*Total: 1*

- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_47_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.