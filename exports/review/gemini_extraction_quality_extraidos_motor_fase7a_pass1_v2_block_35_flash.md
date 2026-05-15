# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-15T21:29:42Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_35_flash_candidates.csv`
- Últimas linhas: **20**
- Total auditado: **11**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 1 |
| Verdes com alerta | 2 |
| Amarelos | 5 |
| Vermelhos | 3 |

## Top motivos de alerta (todos os códigos)

- `A10_tipo_vazio_ou_desconhecido`: **9**
- `A09_tensao_vazia`: **7**
- `S_pipeline_AMARELO_REVISAR`: **5**
- `S_pipeline_VERMELHO_REVISAR`: **3**
- `A06_WARNING_espiras_normalizada_rastreavel`: **1**
- `A10_WARNING_tipo_inferido_com_evidencia=monofasico;auxiliar_e/ou_capacitor_preenchidos`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A10_tipo_vazio_ou_desconhecido`: **9**
- `A09_tensao_vazia`: **7**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR EB.pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR ESCOVA.pdf`
- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000443Z-3-001_253069\TC.PDF`
- `drive-download-20260408T000511Z-3-001_428675\60HZ_VENT-AVIARIO_MOTO-FRICCAO.pdf`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 3.pdf`
- `drive-download-20260408T000529Z-3-001_185960\VENTILADOR 3 VELOCIDADES.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_35_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_35_flash.json`