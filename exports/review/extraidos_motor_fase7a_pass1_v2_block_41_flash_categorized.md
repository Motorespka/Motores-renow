# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-16T19:27:00Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_41_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| VERDE_COM_ALERTA | 5 | 35.7% |
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


## VERDE_SEGURO (lista)

*Total: 9*

- `drive-download-20260403T124026Z-3-001_224929\605042439.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042441.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042451.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042463.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042465.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042468.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042474.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042486.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605042501.pdf`

## VERDE_COM_ALERTA

*Total: 5*

- `drive-download-20260403T124026Z-3-001_224929\605028115.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028315.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605029715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605041001.pdf`

## AMARELO_REVISAR

*Total: 0*


## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_41_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_41_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_41_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_41_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_41_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.