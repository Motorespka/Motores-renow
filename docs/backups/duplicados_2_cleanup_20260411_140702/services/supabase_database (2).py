from datetime import datetime


def salvar_motor_supabase(supabase, motor):
    """
    Persistência do motor no Supabase.
    Mantém o mesmo retorno (sucesso, mensagem) do código atual.
    """
    try:
        motor["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = supabase.table("motores").insert(motor).execute()

        if res.data:
            return True, "✅ Motor salvo com sucesso no Supabase!"
        else:
            return False, f"⚠️ O banco não retornou confirmação: {res}"

    except Exception as e:
        return False, f"❌ Erro ao salvar no Supabase: {str(e)}"
