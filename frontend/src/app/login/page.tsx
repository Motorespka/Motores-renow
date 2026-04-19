"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
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
          Acesso web (Next.js) integrado ao Supabase Auth.
        </p>

        {error ? (
          <div className="mt-4 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
            {error}
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="mt-5 space-y-3">
          {mode === "register" ? (
            <>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Nome</label>
                <input
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Username</label>
                <input
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </>
          ) : null}

          <div className="space-y-1">
            <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Email</label>
            <input
              className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Senha</label>
            <input
              className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            className="w-full h-10 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors"
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
          <div className="flex flex-wrap gap-x-3 gap-y-1 font-tech text-muted-foreground/90">
            <Link href="/" className="hover:text-primary transition-colors">
              ← Início / venda
            </Link>
            <Link href="/para-oficinas" className="hover:text-primary transition-colors">
              Para oficinas
            </Link>
            <Link href="/engenharia" className="hover:text-primary transition-colors">
              Manutenção elétrica
            </Link>
            <Link href="/funcionalidades" className="hover:text-primary transition-colors">
              Funcionalidades
            </Link>
            <Link href="/planos" className="hover:text-primary transition-colors">
              Planos
            </Link>
            <Link href="/como-comecar" className="hover:text-primary transition-colors">
              Como começar
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
