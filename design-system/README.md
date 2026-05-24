# Design System — Gêmeo Digital (PMTH)

Tokens e CSS compartilhados entre **Streamlit** (bancada) e **Next.js** (site).

## Arquivos

| Arquivo | Uso |
|---------|-----|
| `digital-twin-tokens.json` | Fonte única de cores, tipografia e faixas de exibição |
| `digital-twin.css` | Variáveis CSS base |

## Consumidores

- **Streamlit:** `assets/demo_calculo_dashboard.css` → `page/demo_calculo_ui.py` → `page/demo_calculo_components.py`
- **Next.js:** `frontend/src/lib/digital-twin-tokens.ts` + `frontend/src/styles/digital-twin.css` + `frontend/src/components/digital-twin/`
- **API:** `GET /api/v1/design/digital-twin-tokens` (FastAPI)

## Prévia Next

```bash
cd frontend && npm run dev
# http://localhost:3000/gemeo-digital
```

## Streamlit

Abra o Gêmeo Digital no app e execute um cálculo — o painel direito usa o layout PMTH (veredito, comparativo, gauges SVG, laudo PDF).
