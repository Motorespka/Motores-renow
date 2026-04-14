"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode } from "react";

import { supabase } from "@/lib/supabase";

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  isAdmin?: boolean;
  userLabel?: string;
  canAccessCadastro?: boolean;
};

export function AppShell({
  title,
  subtitle,
  children,
  isAdmin = false,
  userLabel = "",
  canAccessCadastro = false
}: Props) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  const links = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/motors", label: "Consulta" },
    ...(canAccessCadastro ? [{ href: "/cadastro", label: "Cadastro" }] : []),
    ...(isAdmin ? [{ href: "/admin", label: "Admin" }] : [])
  ];

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <div className="brand">Moto-Renow</div>
        {userLabel ? <div className="text-muted">Logado como: {userLabel}</div> : null}
        <nav className="menu">
          {links.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`));
            return (
            <Link
              key={item.href}
              href={item.href}
              className={active ? "menu-link active" : "menu-link"}
            >
              {item.label}
            </Link>
            );
          })}
        </nav>
        <button onClick={handleLogout} className="logout-btn">
          Logout
        </button>
      </aside>

      <main className="app-main">
        <header className="page-header">
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </header>
        {children}
      </main>
    </div>
  );
}
