# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-15T00:44:32Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_31_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 2 | 14.3% |
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


## VERDE_SEGURO (lista)

*Total: 12*

- `drive-download-20260403T124026Z-3-001_224929\605058002.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605058003.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605058005.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605058007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605058008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605058009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605059003.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605059006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605059007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605059008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605059009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605059010.pdf`

## VERDE_COM_ALERTA

*Total: 0*


## AMARELO_REVISAR

*Total: 2*

- `drive-download-20260403T124026Z-3-001_224929\605058004.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605058006.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_31_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_31_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_31_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_31_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_31_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.