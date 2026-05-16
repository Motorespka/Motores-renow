# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-16T20:14:27Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_44_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 1 | 7.1% |
| VERDE_COM_ALERTA | 6 | 42.9% |
| VERDE_SEGURO | 7 | 50.0% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **7** (**50.0%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
- **VERMELHO infra (no_keys/quota/429)**: **0** (**0.0%**) da amostra.

## Estado das chaves (ficheiro gemini_keys_status.json)

- OK sem cooldown ativo (aprox.): **27**
- Em quota_exhausted no último snapshot: **0**
- Distribuição por status: `{"ok": 27, "unknown_error": 1}`

## Critério automático “pronto para escalar”

- VERDE_SEGURO ≥ **75%**
- infraestrutura **VERMELHO_NO_KEYS_OU_QUOTA** relativamente **baixa**
- pelo menos **uma chave OK** utilizável (sem cooldown imediato)
- sem **quota_exhausted** generalizada no snapshot

**Resultado:** ❌ Critérios não cumpridos ou infraestrutura frágil.

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (50.0%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)

- `faltando_obrigatorio`: **1**
- `baixa_confianca_local`: **1**

## VERDE_SEGURO (lista)

*Total: 7*

- `drive-download-20260403T124026Z-3-001_224929\605058006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605060004.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605061007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605064006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605066008.pdf`

## VERDE_COM_ALERTA

*Total: 6*

- `drive-download-20260403T124026Z-3-001_224929\605028115.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028315.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605028715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605029715.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605041001.pdf`
- `drive-download-20260408T000443Z-3-001_253069\Esquema Eletrico Geradores Branco.pdf`

## AMARELO_REVISAR

*Total: 1*

- `drive-download-20260408T000443Z-3-001_253069\BOBI.PDF`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_44_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_44_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_44_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_44_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_44_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.