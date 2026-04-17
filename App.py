from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_APP_PATH = Path(__file__).with_name("app.py")
_SPEC = spec_from_file_location("moto_renow_streamlit_app", _APP_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Nao foi possivel carregar o entrypoint Streamlit em {_APP_PATH}.")

_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
main = _MODULE.main


if __name__ == "__main__":
    main()
