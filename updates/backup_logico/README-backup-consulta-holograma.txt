Backups relacionados com holograma / Consulta (Streamlit)
=========================================================

Ficheiros criados a partir do Git (commit 311db66 — antes da alteração de filtros
na coluna principal e do ajuste de fragment na V21.0.14):

  motor_hologram.py.backup-311db66-consulta-estavel
    Cópia exacta de `components/motor_hologram.py` nesse commit.
    (O holograma em si não mudou depois desse ponto; o problema era sobretudo o layout da Consulta.)

  page_consulta.py.backup-311db66-sidebar-filtros
    Cópia exacta de `page/consulta.py` com filtros na **sidebar** e corpo ainda em `@maybe_fragment`.
    NÃO restaurar tal qual se precisar da correção StreamlitAPIException — use só como referência de texto/UI.

Para restaurar manualmente o holograma (ficheiro da componente):

  copy /Y updates\backup_logico\motor_hologram.py.backup-311db66-consulta-estavel components\motor_hologram.py

(Em PowerShell: Copy-Item.)

Correcção aplicada na Consulta actual: o `for` dos motores voltou a ficar **dentro** da mesma
`st.columns` que o cabeçalho e a paginação, para o WebGL / model-viewer não ficar desligado do bloco de layout.
