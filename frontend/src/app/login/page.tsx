"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  getCurrentSession,
  isDevDemoLoginAllowed,
  setDevDemoSession,
  tryDevDemoCredentials,
} from "@/lib/auth";
import { supabase, SUPABASE_CONFIGURED } from "@/lib/supabase";

function normalizeLoginId(raw: string): string {
  const v = raw.trim().toLowerCase();
  if (!v) return v;
  // Streamlit usava username; no web aceitamos username curto → email local
  if (!v.includes("@")) return `${v}@gmail.com`;
  return v;
}

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

  async function goDashboardAfterAuth() {
    // Evita corrida: getSession() no /dashboard antes da sessão gravar no storage.
    for (let i = 0; i < 8; i += 1) {
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        router.replace("/dashboard");
        return;
      }
      await new Promise((r) => setTimeout(r, 80));
    }
    router.replace("/dashboard");
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const emailNorm = normalizeLoginId(email);
    const passwordRaw = password;

    try {
      if (mode === "login") {
        if (tryDevDemoCredentials(email.trim().toLowerCase(), passwordRaw) || tryDevDemoCredentials(emailNorm, passwordRaw)) {
          if (!setDevDemoSession()) {
            throw new Error(
              "Não foi possível gravar a sessão de teste (localStorage). Saia do modo privado ou use outro browser."
            );
          }
          router.replace("/dashboard");
          return;
        }

        if (!SUPABASE_CONFIGURED) {
          throw new Error("Supabase não configurado neste deploy. Contacte o administrador.");
        }

        const { data, error: loginError } = await supabase.auth.signInWithPassword({
          email: emailNorm,
          password: passwordRaw,
        });
        if (loginError) {
          throw new Error(
            `${loginError.message} — use o e-mail completo (ex.: seu@gmail.com) e a senha Admin123! se acabámos de repor.`
          );
        }
        if (!data.session) {
          throw new Error("Login sem sessão. Confirme o e-mail no Supabase ou tente de novo.");
        }
        await goDashboardAfterAuth();
      } else {
        if (!SUPABASE_CONFIGURED) {
          throw new Error("Supabase não configurado neste deploy.");
        }
        const { data, error: signUpError } = await supabase.auth.signUp({
          email: emailNorm,
          password: passwordRaw,
          options: {
            data: {
              username: username.trim() || emailNorm.split("@")[0],
              nome: nome.trim() || username.trim() || emailNorm.split("@")[0],
              role: "user",
            },
          },
        });
        if (signUpError) throw signUpError;
        if (data.session) {
          await goDashboardAfterAuth();
        } else {
          setMode("login");
          setError("Conta criada. Se pedir confirmação de e-mail, confirme e depois entre. Senão, entre já com a mesma senha.");
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
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden">
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      <div className="absolute -top-32 left-[-120px] w-[520px] h-[520px] rounded-full bg-primary/10 blur-3xl pointer-events-none" />
      <div className="absolute -top-40 right-[-160px] w-[520px] h-[520px] rounded-full bg-accent/10 blur-3xl pointer-events-none" />

      <div className="w-full max-w-md premium-card-elevated p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary via-primary/90 to-primary/70 flex items-center justify-center shadow-lg">
            <span className="font-display text-[12px] tracking-widest font-bold text-primary-foreground">MR</span>
          </div>
          <div className="flex flex-col">
            <span className="font-display text-sm font-bold tracking-wider text-foreground">MOTO-RENOW</span>
            <span className="text-[10px] text-primary/70 tracking-[0.22em] font-medium">TECHNICAL PLATFORM</span>
          </div>
        </div>

        <h1 className="font-display text-base font-bold tracking-wider text-foreground">
          {mode === "login" ? "ENTRAR" : "CRIAR CONTA"}
        </h1>
        <p className="text-[11px] text-muted-foreground font-tech mt-1">
          Painel web (Vercel + Supabase). O login do Streamlit antigo era por utilizador/tabela — aqui é e-mail + senha.
        </p>

        <div className="mt-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-[11px] leading-relaxed text-foreground/90 font-tech space-y-1">
          <p className="font-semibold text-emerald-200/95">Acesso rápido (reposto agora)</p>
          <p>
            E-mail: <code className="font-mono-tech">k45430494@gmail.com</code>
          </p>
          <p>
            ou: <code className="font-mono-tech">admin@gmail.com</code>
          </p>
          <p>
            Senha: <code className="font-mono-tech">Admin123!</code>
          </p>
          {isDevDemoLoginAllowed() ? (
            <p className="text-muted-foreground">
              Demo: <code className="font-mono-tech">admin</code> / <code className="font-mono-tech">admin</code>
            </p>
          ) : null}
        </div>

        {error ? (
          <div className="mt-4 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
            {error}
          </div>
        ) : null}

        <form noValidate onSubmit={onSubmit} className="mt-5 space-y-3">
          {mode === "register" ? (
            <>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Nome</label>
                <input
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Username</label>
                <input
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </>
          ) : null}

          <div className="space-y-1">
            <label className="text-[11px] text-muted-foreground tracking-wide font-tech">
              E-mail (ou utilizador)
            </label>
            <input
              className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50"
              type="text"
              inputMode="email"
              autoComplete="username"
              placeholder="k45430494@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Senha</label>
            <input
              className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50"
              type="password"
              autoComplete="current-password"
              placeholder="Admin123!"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            className="w-full h-10 rounded-xl bg-primary/15 border border-primary/30 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors"
            disabled={loading}
            type="submit"
          >
            {loading ? "PROCESSANDO..." : mode === "login" ? "ENTRAR" : "CADASTRAR"}
          </button>
        </form>

        <div className="mt-4 flex flex-col gap-2 text-[11px]">
          <div className="flex items-center justify-between">
            <button
              className="text-muted-foreground hover:text-foreground transition-colors font-tech"
              onClick={() => setMode((prev) => (prev === "login" ? "register" : "login"))}
              type="button"
            >
              {mode === "login" ? "Criar nova conta" : "Já tenho conta"}
            </button>
            <span className="text-muted-foreground/70 font-mono-tech">/login</span>
          </div>
          <Link href="/" className="font-tech text-muted-foreground hover:text-primary transition-colors">
            ← Início
          </Link>
        </div>
      </div>
    </div>
  );
}
