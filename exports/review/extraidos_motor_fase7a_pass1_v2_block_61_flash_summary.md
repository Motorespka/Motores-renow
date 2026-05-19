## Resumo batch rebobinagem (2026-05-18 23:46:51)

- **input**: `C:\Users\micke\Desktop\O rebobinador\_extraidos_motor`
- **work_queue_csv**: `exports/review/pass1_v2_block_61.csv`
- **output_tag**: `extraidos_motor_fase7a_pass1_v2_block_61_flash`
- **dry-run**: `False` (sem chamadas Gemini à API)
- **processados**: `14`
- **cache respostas**: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\logs\extraidos_motor_fase7a_pass1_v2_block_61_flash_gemini_cache`

### Fontes

- tentativas pipeline local (PDF texto / Tesseract / EasyOCR): 19
- com texto local não vazio: 1
- chamadas API Gemini: 14
- imagens com fallback Gemini (contagem interna): 14
- respostas servidas do cache (sem API): 0

### Economia de chaves / cache

- pastas cache consultadas: 1
- **cache_hits**: 0
- **cache_misses** (resolveu por API): 14
- **gemini_calls_real**: 14
- **gemini_calls_avoided_by_cache**: 0
- **quota_429**: 0
- **quota_429_consecutive_max**: 0
- skipped_existing_green: 0
- skipped_existing_success: 0

### Status

- VERDE_AUTO_LOCAL: 0
- VERDE_AUTO_GEMINI: 5
- AMARELO_REVISAR: 6
- VERMELHO_REVISAR: 3
- PAUSA_INFRA_SEM_CHAVE: 0
- PAUSA_LIMITE_CHAMADAS: 0
- PAUSA_LOTE_INTERROMPIDO: 0

- PAUSA_TODAS_CHAVES_COOLDOWN: 0
- PAUSA_LIMITE_POR_CHAVE: 0
- PAUSA_SEM_CHAVE_OK: 0

### Chaves Gemini usadas (alias)

- UQ_1: 2
- UQ_10: 2
- UQ_11: 1
- UQ_3: 1
- UQ_4: 1
- UQ_5: 1
- UQ_6: 1
- UQ_7: 1
- UQ_8: 1
- UQ_9: 1

### Uso por chave (detalhado)

- rotation_strategy: `round_robin`
- max_calls_per_key_per_run: `2`

- UQ_1 | status=ok | eligible_end=0 | calls=2 | ok=2 | quota=0 | errors=0 | cooldown= | blocked=per_key_limit
- UQ_10 | status=ok | eligible_end=0 | calls=2 | ok=2 | quota=0 | errors=0 | cooldown= | blocked=per_key_limit
- UQ_11 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_12 | status=unknown_error | eligible_end=0 | calls=1 | ok=0 | quota=0 | errors=2 | cooldown= | blocked=require_ok
- UQ_13 | status=unknown_error | eligible_end=0 | calls=1 | ok=0 | quota=0 | errors=2 | cooldown= | blocked=require_ok
- UQ_14 | status=unknown_error | eligible_end=0 | calls=1 | ok=0 | quota=0 | errors=2 | cooldown= | blocked=require_ok
- UQ_2 | status=unknown_error | eligible_end=0 | calls=1 | ok=0 | quota=0 | errors=2 | cooldown= | blocked=require_ok
- UQ_3 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=1 | cooldown= | blocked=
- UQ_4 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_5 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_6 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_7 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_8 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_9 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=

### Top 10 motivos de bloqueio

- baixa_confianca_local: 13
- faltando_obrigatorio: 6
- gemini_falhou:unknown_error:Extra data: line 63 column 4 (char 1544): 1
- gemini_falhou:unknown_error:Extra data: line 64 column 4 (char 1496): 1

### Top 11–20 (extra)


### Exemplos (até 10) problemáticos

- drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf: faltando_obrigatorio;baixa_confianca_local missing=['tensao']
- drive-download-20260408T000517Z-3-001_345175\ventiladores 1.pdf: faltando_obrigatorio;baixa_confianca_local;gemini_falhou:unknown_error:Extra data: line 63 column 4 (char 1544) missing=['tensao']
- drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf: faltando_obrigatorio;baixa_confianca_local;gemini_falhou:unknown_error:Extra data: line 64 column 4 (char 1496) missing=['tensao']
