# Auditoria extração Gemini (determinística)

- Gerado: `2026-05-19T02:47:05Z`
- Entrada: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\exports\review\extraidos_motor_fase7a_pass1_v2_block_61_flash_candidates.csv`
- Últimas linhas: **14**
- Total auditado: **14**

## Resumo

| Métrica | Valor |
|---|---:|
| Verdes sem alerta | 2 |
| Verdes com alerta | 3 |
| Amarelos | 6 |
| Vermelhos | 3 |

## Top motivos de alerta (todos os códigos)

- `A10_tipo_vazio_ou_desconhecido`: **8**
- `A09_tensao_vazia`: **6**
- `S_pipeline_AMARELO_REVISAR`: **6**
- `S_pipeline_VERMELHO_REVISAR`: **3**
- `A10_WARNING_tipo_inferido_com_evidencia=monofasico;auxiliar_e/ou_capacitor_preenchidos`: **3**
- `A01_mono_sem_fio_espiras_passo_principal`: **2**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **2**
- `A06_WARNING_espiras_normalizada_rastreavel`: **1**

## Top alertas críticos (prefixo `A`, heurísticas de campo)

- `A10_tipo_vazio_ou_desconhecido`: **8**
- `A09_tensao_vazia`: **6**
- `A01_mono_sem_fio_espiras_passo_principal`: **2**
- `A02_mono_sem_fio_espiras_passo_auxiliar`: **2**

## Revisão manual sugerida

Arquivos com pelo menos um alerta **ou** status AMARELO/VERMELHO:

- `drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf`
- `drive-download-20260408T000443Z-3-001_253069\ROT.PDF`
- `drive-download-20260408T000511Z-3-001_428675\esquema vent. de ar.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf`
- `drive-download-20260408T000517Z-3-001_345175\ventiladores 3.pdf`
- `drive-download-20260408T000529Z-3-001_185960\0b36da0a-68fa-411f-8d98-42612aac07cd.jpg`
- `drive-download-20260408T000529Z-3-001_185960\1d217467-02db-4a7f-8017-ea2f9ac0a715.jpg`
- `drive-download-20260408T000529Z-3-001_185960\1d9b3430-0b16-4701-b724-661974ff8b49.jpg`
- `drive-download-20260408T000529Z-3-001_185960\324e6cbc-2bab-43ed-9303-2d560b1da7ec.jpg`
- `drive-download-20260408T000529Z-3-001_185960\6bbe2fd4-7adf-44a6-bdde-b89413fd6628.jpg`
- `drive-download-20260408T000529Z-3-001_185960\7a381ec7-685e-4eb4-bf68-a2470fcf7637.jpg`
- `drive-download-20260408T000529Z-3-001_185960\80dae8d4-2a6d-4153-8b6c-c84b919e1600.jpg`
- `drive-download-20260408T000529Z-3-001_185960\8bc49b76-90d1-4f38-bd2f-86cd93ad3689.jpg`

## Saídas

- CSV: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_61_flash.csv`
- JSON: `exports\review\gemini_extraction_quality_extraidos_motor_fase7a_pass1_v2_block_61_flash.json`