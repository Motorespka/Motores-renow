"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { getCurrentSession } from "@/lib/auth";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [nome, setNome] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      const session = await getCurrentSession();
      if (session) {
        router.replace("/dashboard");
      }
    })();
  }, [router]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const emailNorm = email.trim().toLowerCase();

    try {
      if (mode === "login") {
        const { error: loginError } = await supabase.auth.signInWithPassword({
          email: emailNorm,
          password
        });
        if (loginError) throw loginError;
        router.replace("/dashboard");
      } else {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email: emailNorm,
          password,
          options: {
            data: {
              username: username.trim(),
              nome: nome.trim()
            }
          }
        });
        if (signUpError) throw signUpError;
        if (data.session) {
          router.replace("/dashboard");
        } else {
          setMode("login");
          setError("Conta criada. Verifique seu email para confirmar e depois faca login.");
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha na autenticacao.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="center-screen">
      <div className="card auth-card">
        <h1>{mode === "login" ? "Entrar no Moto-Renow" : "Criar conta"}</h1>
        <p className="text-muted">
          Plataforma web fora do Streamlit, mantendo Supabase Auth e regras do seu projeto.
        </p>

        {error ? <div className="error">{error}</div> : null}

        <form onSubmit={onSubmit}>
          {mode === "register" ? (
            <>
              <div className="field">
                <label>Nome</label>
                <input value={nome} onChange={(e) => setNome(e.target.value)} required />
              </div>
              <div className="field">
                <label>Username</label>
                <input value={username} onChange={(e) => setUsername(e.target.value)} required />
              </div>
            </>
          ) : null}

          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label>Senha</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          <button className="btn" disabled={loading} type="submit">
            {loading ? "Processando..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>
        </form>

        <div style={{ marginTop: 12 }}>
          <button
            className="btn secondary"
            onClick={() => setMode((prev) => (prev === "login" ? "register" : "login"))}
            type="button"
          >
            {mode === "login" ? "Criar nova conta" : "Ja tenho conta"}
          </button>
        </div>
      </div>
    </div>
  );
}
