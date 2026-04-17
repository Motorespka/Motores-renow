"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Save, Search, Shield } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { AdminUser, MeResponse } from "@/lib/types";

export default function AdminPage() {
  const router = useRouter();

  const [token, setToken] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [q, setQ] = useState("");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selected, setSelected] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [okMessage, setOkMessage] = useState("");

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      setToken(session.access_token);
      const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
      if (!mePayload.profile.is_admin) {
        router.replace("/dashboard");
        return;
      }
      setMe(mePayload);
    })().catch(() => {
      router.replace("/login");
    });
  }, [router]);

  async function onSearch(event: FormEvent) {
    event.preventDefault();
    if (q.trim().length < 2 || !token) return;
    setError("");
    setOkMessage("");
    setLoading(true);
    try {
      const result = await apiFetch<AdminUser[]>(
        `/admin/users/search?q=${encodeURIComponent(q.trim())}&limit=25`,
        token
      );
      setUsers(result);
      setSelected(result[0] || null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao buscar usuários.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function saveSelected() {
    if (!selected || !token) return;
    setError("");
    setOkMessage("");
    try {
      const payload = {
        username: selected.username || "",
        nome: selected.nome || "",
        role: selected.role || "user",
        plan: selected.plan || "free",
        ativo: Boolean(selected.ativo)
      };
      const updated = await apiFetch<AdminUser>(
        `/admin/users/${encodeURIComponent(selected.id)}`,
        token,
        {
          method: "PATCH",
          body: JSON.stringify(payload)
        }
      );
      setSelected(updated);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setOkMessage("Usuário atualizado com sucesso.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao salvar usuário.";
      setError(msg);
    }
  }

  if (!me) {
    return <div className="center-screen text-muted">Carregando admin...</div>;
  }

  return (
    <AppShell
      title="Painel Admin"
      subtitle="Gerenciamento de usuarios e planos"
      isAdmin
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="premium-card-elevated p-5">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <div className="font-display text-sm tracking-wider">ADMIN</div>
              <span className="badge-premium badge-warning">RESTRITO</span>
            </div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">
              Gerenciamento de usuários, planos e permissões.
            </div>
          </div>
          <Shield className="w-4 h-4 text-primary" />
        </div>

        <form onSubmit={onSearch} className="mt-4 flex gap-2 flex-wrap">
          <div className="flex-1 min-w-[220px] relative">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              className="w-full h-10 pl-9 pr-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
              placeholder="Buscar por username, nome ou email"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <button
            className="h-10 px-4 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors disabled:opacity-60"
            type="submit"
            disabled={loading}
          >
            {loading ? "Buscando..." : "Buscar"}
          </button>
        </form>
      </div>

      {error ? (
        <div className="mt-3 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}
      {okMessage ? (
        <div className="mt-3 p-3 rounded-lg border border-accent/30 bg-accent/10 text-[12px] text-foreground">
          {okMessage}
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 lg:grid-cols-3">
        <div className="lg:col-span-1 premium-card-elevated p-5">
          <div className="flex items-center justify-between">
            <div className="font-display text-sm tracking-wider">RESULTADOS</div>
            <span className="badge-premium badge-primary">{users.length}</span>
          </div>
          <div className="text-[11px] text-muted-foreground font-tech mt-1">Selecione para editar.</div>

          <div className="mt-4 grid gap-2">
            {users.map((u) => {
              const label = (u.username || u.nome || u.email || u.id) as string;
              const active = selected?.id === u.id;
              return (
                <button
                  key={u.id}
                  className={
                    "w-full text-left px-3 py-2 rounded-xl border transition-colors " +
                    (active
                      ? "border-primary/40 bg-primary/10 text-foreground"
                      : "border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground")
                  }
                  type="button"
                  onClick={() => setSelected(u)}
                >
                  <div className="text-[12px] font-tech truncate">{label}</div>
                  <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground font-mono-tech">
                    <span>{u.role || "user"}</span>
                    <span>•</span>
                    <span>{u.plan || "free"}</span>
                    <span>•</span>
                    <span>{u.ativo ? "ativo" : "inativo"}</span>
                  </div>
                </button>
              );
            })}
            {!users.length ? (
              <div className="premium-card p-4 text-[12px] text-muted-foreground font-tech">
                Sem resultados. Dica: no modo DEV, qualquer busca retorna mocks.
              </div>
            ) : null}
          </div>
        </div>

        <div className="lg:col-span-2 premium-card-elevated p-5">
          <div className="flex items-center justify-between">
            <div className="font-display text-sm tracking-wider">EDITAR USUÁRIO</div>
            {selected ? (
              <span className="badge-premium badge-accent">{selected.id}</span>
            ) : (
              <span className="badge-premium badge-warning">SELECIONE</span>
            )}
          </div>
          <div className="text-[11px] text-muted-foreground font-tech mt-1">Atualize username/nome/role/plano.</div>

          {selected ? (
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Username</label>
                <input
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
                  value={selected.username || ""}
                  onChange={(e) => setSelected({ ...selected, username: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Nome</label>
                <input
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
                  value={selected.nome || ""}
                  onChange={(e) => setSelected({ ...selected, nome: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Role</label>
                <select
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
                  value={selected.role || "user"}
                  onChange={(e) => setSelected({ ...selected, role: e.target.value })}
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-[11px] text-muted-foreground tracking-wide font-tech">Plano</label>
                <select
                  className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
                  value={selected.plan || "free"}
                  onChange={(e) => setSelected({ ...selected, plan: e.target.value })}
                >
                  <option value="free">free</option>
                  <option value="paid">paid</option>
                  <option value="pro">pro</option>
                  <option value="premium">premium</option>
                  <option value="enterprise">enterprise</option>
                  <option value="business">business</option>
                </select>
              </div>

              <div className="md:col-span-2 flex items-center justify-between gap-3">
                <label className="flex items-center gap-2 text-[12px] text-muted-foreground font-tech">
                  <input
                    className="accent-primary"
                    type="checkbox"
                    checked={Boolean(selected.ativo)}
                    onChange={(e) => setSelected({ ...selected, ativo: e.target.checked })}
                  />
                  Conta ativa
                </label>

                <button
                  type="button"
                  className="h-10 px-4 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors flex items-center gap-2"
                  onClick={saveSelected}
                >
                  <Save className="w-4 h-4" />
                  Salvar
                </button>
              </div>
            </div>
          ) : (
            <div className="mt-4 premium-card p-4 text-[12px] text-muted-foreground font-tech">
              Selecione um usuário na coluna “Resultados”.
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
