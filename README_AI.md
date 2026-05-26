MOTO-RENOW AI INITIALIZATION

This repository enables autonomous engineering behavior guided by AI guardrails.

## Streamlit demo — neuro-simbólico (kill switch)

On **Streamlit Cloud** or any host, set environment variable or Streamlit secret `DEMO_NEURO_SYMBOLIC` to `false`, `0`, or `off` to disable the Gemini “judge” path on the calculation demo (`page/demo_calculo.py`) without redeploying application code. Any other value (or unset) keeps the feature enabled when the user selects inferência neuro-simbólica.
