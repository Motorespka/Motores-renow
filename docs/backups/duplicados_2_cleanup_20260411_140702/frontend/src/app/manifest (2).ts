import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Moto-Renow",
    short_name: "MotoRenow",
    description: "Plataforma técnica para motores industriais.",
    start_url: "/",
    display: "standalone",
    background_color: "#070d18",
    theme_color: "#2fd5ff",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml"
      }
    ]
  };
}

