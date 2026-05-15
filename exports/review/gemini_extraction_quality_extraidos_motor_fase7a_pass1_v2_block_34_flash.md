# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-15T01:11:16Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_34_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 9 |
| Verdes com alerta | 3 |
| Amarelos | 1 |
| Vermelhos | 1 |

## Top motivos de alerta (todos os códigos)

- `A10_tipo_vazio_ou_desconhecido`: **4**
- `S_pipeline_AMARELO_REVISAR`: **1**
- `A03_trifasico_com_auxiliar_preenchido`: **1**
- `S_pipeline_VERMELHO_REVISAR`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A10_tipo_vazio_ou_desconhecido`: **4**
- `A03_trifasico_com_auxiliar_preenchido`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260408T000443Z-3-001_253069\BOBI.PDF`
- `drive-download-20260408T000443Z-3-001_253069\EST.PDF`
- `drive-download-20260408T000443Z-3-001_253069\Esquema Eletrico Geradores Branco.pdf`
- `drive-download-20260408T000443Z-3-001_253069\GERADOR 15 KVA (1).pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_34_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_34_flash.json`