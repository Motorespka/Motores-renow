import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Moto-Renow Web",
  description: "Plataforma tecnica para consulta e diagnostico de motores."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="dark">{children}</body>
    </html>
  );
}

