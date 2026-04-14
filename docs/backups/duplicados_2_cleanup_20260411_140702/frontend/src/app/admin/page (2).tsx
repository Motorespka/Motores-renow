"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

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
      <div className="card">
        <form onSubmit={onSearch} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            style={{ flex: 1, minWidth: 220 }}
            placeholder="Buscar por username, nome ou email"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Buscando..." : "Buscar"}
          </button>
        </form>
      </div>

      {error ? <div className="error" style={{ marginTop: 12 }}>{error}</div> : null}
      {okMessage ? <div className="ok" style={{ marginTop: 12 }}>{okMessage}</div> : null}

      <div className="grid cards" style={{ marginTop: 12 }}>
        <div className="card">
          <h3>Resultados</h3>
          <div className="grid">
            {users.map((u) => (
              <button
                key={u.id}
                className="btn secondary"
                type="button"
                onClick={() => setSelected(u)}
                style={{ textAlign: "left" }}
              >
                {(u.username || u.nome || u.email || u.id) as string}
              </button>
            ))}
            {!users.length ? <p className="text-muted">Sem resultados.</p> : null}
          </div>
        </div>

        <div className="card">
          <h3>Editar usuário</h3>
          {selected ? (
            <div className="grid">
              <div className="field">
                <label>Username</label>
                <input
                  value={selected.username || ""}
                  onChange={(e) => setSelected({ ...selected, username: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Nome</label>
                <input value={selected.nome || ""} onChange={(e) => setSelected({ ...selected, nome: e.target.value })} />
              </div>
              <div className="field">
                <label>Role</label>
                <select value={selected.role || "user"} onChange={(e) => setSelected({ ...selected, role: e.target.value })}>
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div className="field">
                <label>Plano</label>
                <select value={selected.plan || "free"} onChange={(e) => setSelected({ ...selected, plan: e.target.value })}>
                  <option value="free">free</option>
                  <option value="paid">paid</option>
                  <option value="pro">pro</option>
                  <option value="premium">premium</option>
                  <option value="enterprise">enterprise</option>
                  <option value="business">business</option>
                </select>
              </div>
              <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={Boolean(selected.ativo)}
                  onChange={(e) => setSelected({ ...selected, ativo: e.target.checked })}
                />
                Conta ativa
              </label>

              <button type="button" className="btn" onClick={saveSelected}>
                Salvar alterações
              </button>
            </div>
          ) : (
            <p className="text-muted">Selecione um usuário.</p>
          )}
        </div>
      </div>
    </AppShell>
  );
}
