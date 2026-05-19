# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-19T02:28:35Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_60_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 6 |
| Verdes com alerta | 1 |
| Amarelos | 4 |
| Vermelhos | 3 |

## Top motivos de alerta (todos os códigos)

- `A10_tipo_vazio_ou_desconhecido`: **5**
- `A09_tensao_vazia`: **5**
- `S_pipeline_AMARELO_REVISAR`: **4**
- `S_pipeline_VERMELHO_REVISAR`: **3**
- `A03_trifasico_com_auxiliar_preenchido`: **2**
- `A03b_trifasico_principal_vazio_aux_preenchido`: **2**
- `A01_mono_sem_fio_espiras_passo_principal`: **1**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**
- `A06_WARNING_espiras_normalizada_rastreavel`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A10_tipo_vazio_ou_desconhecido`: **5**
- `A09_tensao_vazia`: **5**
- `A03_trifasico_com_auxiliar_preenchido`: **2**
- `A03b_trifasico_principal_vazio_aux_preenchido`: **2**
- `A01_mono_sem_fio_espiras_passo_principal`: **1**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **1**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260408T000443Z-3-001_253069\BOBI.PDF`
- `drive-download-20260408T000443Z-3-001_253069\EST.PDF`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`
- `drive-download-20260408T000443Z-3-001_253069\REGULADOR ESCOVA.pdf`
- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_60_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_60_flash.json`