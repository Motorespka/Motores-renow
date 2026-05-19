## Resumo batch rebobinagem (2026-05-19 00:24:36)

- **input**: `C:\Users\micke\Desktop\O rebobinador\_extraidos_motor`
- **work_queue_csv**: `exports/review/pass1_v2_block_63.csv`
- **output_tag**: `extraidos_motor_fase7a_pass1_v2_block_63_flash`
- **dry-run**: `False` (sem chamadas Gemini à API)
- **processados**: `14`
- **cache respostas**: `C:\Users\micke\Desktop\O rebobinador\Motores-renow\logs\extraidos_motor_fase7a_pass1_v2_block_63_flash_gemini_cache_fresh`

### Fontes

- tentativas pipeline local (PDF texto / Tesseract / EasyOCR): 18
- com texto local não vazio: 2
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
- VERDE_AUTO_GEMINI: 1
- AMARELO_REVISAR: 10
- VERMELHO_REVISAR: 2
- PAUSA_INFRA_SEM_CHAVE: 1
- PAUSA_LIMITE_CHAMADAS: 0
- PAUSA_LOTE_INTERROMPIDO: 0

- PAUSA_TODAS_CHAVES_COOLDOWN: 0
- PAUSA_LIMITE_POR_CHAVE: 0
- PAUSA_SEM_CHAVE_OK: 0

### Chaves Gemini usadas (alias)

- UQ_1: 1
- UQ_12: 1
- UQ_13: 2
- UQ_14: 2
- UQ_2: 1
- UQ_3: 1
- UQ_5: 1
- UQ_6: 1
- UQ_7: 1
- UQ_8: 1

### Uso por chave (detalhado)

- rotation_strategy: `round_robin`
- max_calls_per_key_per_run: `2`

- UQ_1 | status=ok | eligible_end=0 | calls=2 | ok=1 | quota=0 | errors=2 | cooldown= | blocked=per_key_limit
- UQ_10 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:47:44Z | blocked=require_ok;cooldown
- UQ_11 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=2 | cooldown=2026-05-19T03:48:30Z | blocked=require_ok;cooldown
- UQ_12 | status=ok | eligible_end=0 | calls=2 | ok=1 | quota=0 | errors=2 | cooldown= | blocked=per_key_limit
- UQ_13 | status=ok | eligible_end=0 | calls=2 | ok=2 | quota=0 | errors=0 | cooldown= | blocked=per_key_limit
- UQ_14 | status=ok | eligible_end=0 | calls=2 | ok=2 | quota=0 | errors=0 | cooldown= | blocked=per_key_limit
- UQ_2 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_3 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_4 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:51:29Z | blocked=require_ok;cooldown
- UQ_5 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_6 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_7 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_8 | status=ok | eligible_end=1 | calls=1 | ok=1 | quota=0 | errors=0 | cooldown= | blocked=
- UQ_9 | status=quota_exhausted | eligible_end=0 | calls=1 | ok=0 | quota=1 | errors=1 | cooldown=2026-05-19T03:53:02Z | blocked=require_ok;cooldown

### Top 10 motivos de bloqueio

- baixa_confianca_local: 11
- faltando_obrigatorio: 7
- infra:gemini_indisponivel_ou_quota: 1
- gemini_falhou:unknown_error:Extra data: line 40 column 4 (char 1377): 1

### Top 11–20 (extra)


### Exemplos (até 10) problemáticos

- drive-download-20260408T000517Z-3-001_345175\ventiladores 2.pdf: faltando_obrigatorio;baixa_confianca_local;gemini_falhou:unknown_error:Extra data: line 40 column 4 (char 1377) missing=['tensao']
- drive-download-20260408T000443Z-3-001_253069\REGULADOR CR.pdf: faltando_obrigatorio;baixa_confianca_local missing=['tensao']
