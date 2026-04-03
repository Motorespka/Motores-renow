import base64
import hmac
import hashlib
import streamlit as st
from datetime import datetime, timedelta

TEMPO_SESSAO = 8  # horas
QP_KEY = "auth"   # nome do query param


def _get_query_params() -> dict:
    # compatível com versões novas/antigas do Streamlit
    try:
        return dict(st.query_params)
    except Exception:
        return dict(st.experimental_get_query_params())


def _set_query_params(**params) -> None:
    try:
        st.query_params.clear()
        for k, v in params.items():
            if v is None:
                continue
            st.query_params[k] = v
    except Exception:
        st.experimental_set_query_params(**{k: v for k, v in params.items() if v is not None})


def _secret_key() -> bytes:
    # use uma chave fixa em secrets para assinar o token
    # se não existir, cai no APP_PASSWORD (melhor do que nada)
    key = st.secrets.get("AUTH_SECRET_KEY") or st.secrets.get("APP_PASSWORD") or "dev"
    return str(key).encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _sign(payload: str) -> str:
    sig = hmac.new(_secret_key(), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(sig)


def _make_token(expira_em: datetime) -> str:
    exp_ts = str(int(expira_em.timestamp()))
    payload = f"exp={exp_ts}"
    sig = _sign(payload)
    return _b64url_encode(f"{payload}.{sig}".encode("utf-8"))


def _parse_token(token: str) -> datetime | None:
    try:
        decoded = _b64url_decode(token).decode("utf-8")
        payload, sig = decoded.rsplit(".", 1)
        if not hmac.compare_digest(_sign(payload), sig):
            return None
        parts = dict(p.split("=", 1) for p in payload.split("&") if "=" in p)
        exp_ts = int(parts.get("exp", "0"))
        expira_em = datetime.fromtimestamp(exp_ts)
        return expira_em
    except Exception:
        return None


def criar_sessao():
    st.session_state.logado = True
    st.session_state.expira_em = datetime.now() + timedelta(hours=TEMPO_SESSAO)

    # grava token na URL para sobreviver ao refresh (F5)
    token = _make_token(st.session_state.expira_em)
    qp = _get_query_params()
    qp[QP_KEY] = token
    _set_query_params(**qp)


def sessao_valida():
    # 1) sessão atual
    if st.session_state.get("logado") and st.session_state.get("expira_em"):
        if datetime.now() <= st.session_state.expira_em:
            return True
        limpar_sessao()
        return False

    # 2) reidrata a sessão do token na URL (sobrevive ao F5)
    qp = _get_query_params()
    token = qp.get(QP_KEY)
    if isinstance(token, list):
        token = token[0] if token else None
    if not token:
        return False

    expira_em = _parse_token(token)
    if not expira_em:
        return False
    if datetime.now() > expira_em:
        limpar_sessao()
        return False

    st.session_state.logado = True
    st.session_state.expira_em = expira_em
    return True


def limpar_sessao():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

    # remove token da URL
    qp = _get_query_params()
    qp.pop(QP_KEY, None)
    _set_query_params(**qp)
