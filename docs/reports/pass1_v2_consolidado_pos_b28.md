# PASS1-LITE V2 — Relatório consolidado (pós-bloco 28)

**Gerado:** 2026-05-14 (UTC)  
**Campanha:** `PASS1_LITE_V2`  
**Manifesto de deploy:** `exports/review/master_release_v2_manifest.csv` (`status_release=OFICIAL`)

## Resumo executivo

| Métrica | Valor |
|--------|------:|
| **OFICIAL no master (SHA únicos)** | **737** |
| **Blocos concluídos na esteira** | 01 → **28** |
| **VERDE_SEGURO (blocos 26–28)** | **34** (14 + 9 + 11) |
| **AMARELO isolado (manual CSV, blocos 26–28)** | **8** (0 + 5 + 3) |
| **Quota HTTP 429 (resumos extract B26–B28)** | **0** |

## Blocos 26–28 (FASE 7C / Gemini 2.5 Flash, imagem 1280 / JPEG 85)

| Bloco | Chamadas Gemini | VERDE_SEGURO | AMARELO (manual) | Notas |
|-------|----------------:|-------------:|-----------------:|--------|
| 26 | 14 | 14 | 0 | 100 % verde |
| 27 | 14 | 9 | 5 | 5× `S_pipeline_AMARELO_REVISAR` |
| 28 | 14 | 11 | 3 | idem |

## Progresso acumulado (`pass1_v2_progress.json`, pós-reconcile B28)

Referência em disco (sincronizado pelo reconcile):

- `ficheiros_processados_v2`: **380**
- `chamadas_gemini_v2`: **385**
- `verde_seguro_total_manifests_v2`: **311** (soma por manifestos reconciliados; métrica interna da campanha)
- `amarelo_isolado_total_manual_csv_v2`: **68**
- `quota_429_total_v2`: **0**

> **Nota:** O total **737** no `master_release_v2_manifest` é a contagem de linhas **OFICIAL** no CSV de release; o campo `verde_seguro_total_manifests_v2` no progresso segue a convenção histórica da campanha (soma dos blocos no `resolved_manifest`) e não substitui o master.

## Próximo passo

- Fila preparada: `exports/review/pass1_v2_block_29.csv` (14 PDFs).
- Após extract + auditoria do B29: categorização → reconcile → `master_release_v2_build_offline.py --phase 7b29` (quando a fase existir no script).

## Integridade

- Auditoria local: `audit_gemini_extraction_quality.py` (regras A01–A11 + pipeline).
- Categorização: `categorize_lote_100_quality.py` (inclui gates de confiança / chaves).
- Densidade de corrente e clusterização: mantidas nos mesmos scripts de auditoria e categorização usados nos blocos anteriores (sem alteração de parâmetros na CLI).
