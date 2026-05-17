# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-17T18:55:33Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_54_flash_candidates.csv`

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

- `drive-download-20260403T124026Z-3-001_224929\605012203.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012205.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012216.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012228.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012236.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012264.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012274.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012278.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012286.pdf`

## VERDE_COM_ALERTA

*Total: 4*

- `drive-download-20260403T124026Z-3-001_224929\1.5cv 2,4p iec63r 2 260,150hz 70x56.4 605012237.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012154.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012170.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605012309.pdf`

## AMARELO_REVISAR

*Total: 1*

- `drive-download-20260403T124026Z-3-001_224929\1,8cv 4e8p nema42 2 50,60hz 30x68 605012085.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_54_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_54_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_54_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_54_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_54_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.