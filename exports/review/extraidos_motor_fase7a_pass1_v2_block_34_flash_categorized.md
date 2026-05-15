# Relatório pós-lote — categorização de qualidade

- Gerado: `2026-05-15T21:15:12Z`
- Últimas linhas analisadas (bundle): **14**
- CSV bundle: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_candidates.csv`

## Totais por categoria

| Categoria | Quantidade | % do lote |
|---|---:|---:|
| AMARELO_REVISAR | 1 | 7.1% |
| VERDE_COM_ALERTA | 3 | 21.4% |
| VERDE_SEGURO | 9 | 64.3% |
| VERMELHO_DADO_RUIM | 1 | 7.1% |

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

- `baixa_confianca_local`: **4**

## VERDE_SEGURO (lista)

*Total: 9*

- `drive-download-20260403T124026Z-3-001_224929\605066010.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605067006.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605067007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605067008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605067009.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605068005.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605068007.pdf`
- `drive-download-20260403T124026Z-3-001_224929\605068008.pdf`
- `drive-download-20260403T124026Z-3-001_224929\6cv 6p iec132 234 60hz 148.6x130 605072712.pdf`

## VERDE_COM_ALERTA

*Total: 3*

- `drive-download-20260408T000443Z-3-001_253069\BOBI.PDF`
- `drive-download-20260408T000443Z-3-001_253069\EST.PDF`
- `drive-download-20260408T000443Z-3-001_253069\GERADOR 15 KVA (1).pdf`

## AMARELO_REVISAR

*Total: 1*

- `drive-download-20260408T000443Z-3-001_253069\Esquema Eletrico Geradores Branco.pdf`

## VERMELHO — infra (reprocessar depois)

*Total: 0*


## VERMELHO — dados / revisão humana

*Total: 1*

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`

## Saídas geradas

- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_categorized.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_categorized.json`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_categorized_reprocess_no_keys.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_categorized_manual_review.csv`
- `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_categorized_safe_green_candidates.csv`

## Nota sobre OCR local

No lote 100 registado, o texto OCR local estava vazio em todas as linhas — qualquer escalação maior depende de Gemini ou de melhoria de OCR/Tesseract reais.