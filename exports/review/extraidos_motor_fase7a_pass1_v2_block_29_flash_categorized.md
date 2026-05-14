# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-14T23:50:41Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 3 | 21.4% |
| VERDE_SEGURO | 11 | 78.6% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **11** (**78.6%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

*Total: 11*

- `drive-download-20260403T124026Z-3-001_224929\605046034.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605050002.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605050003.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605050004.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605051007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605051008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605051009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605052001.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605052002.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605053002.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605053003.pdf`

## VERDE_COM_ALERTA

*Total: 0*


## AMARELO_REVISAR

*Total: 3*

- `drive-download-20260403T124026Z-3-001_224929\605046028.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605046031.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605052005.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_29_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.