import { HomeSessionRedirect } from "@/components/marketing/HomeSessionRedirect";
import { PublicHome } from "@/components/marketing/PublicHome";

/** Landing pública imediata (planos, funcionalidades, login). Sessão só redireciona depois. */
export default function HomePage() {
  return (
    <>
      <HomeSessionRedirect />
      <PublicHome />
    </>
  );
}
