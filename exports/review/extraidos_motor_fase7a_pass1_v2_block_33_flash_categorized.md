# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-15T01:01:31Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 4 | 28.6% |
| VERDE_SEGURO | 10 | 71.4% |

## Aproveitamento real (import seguro)

- **VERDE_SEGURO**: **10** (**71.4%**) — candidatos diretos com campos obrigatórios + sem alerta **A***.
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

**Recomendação:** **Não escalar agora.** taxa VERDE_SEGURO (71.4%) abaixo de 75%

## Top motivos de bloqueio (campo motivos_bloqueio no bundle)


## VERDE_SEGURO (lista)

*Total: 10*

- `drive-download-20260403T124026Z-3-001_224929\605062009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605064007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605064008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605064009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605064010.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065003.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605066007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605066009.pdf`

## VERDE_COM_ALERTA

*Total: 0*


## AMARELO_REVISAR

*Total: 4*

- `drive-download-20260403T124026Z-3-001_224929\605064006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605065008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605066008.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 0*


## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_33_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.