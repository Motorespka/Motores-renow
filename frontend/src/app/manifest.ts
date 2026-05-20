import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Moto-Renow",
    short_name: "MotoRenow",
    description: "Plataforma técnica para motores industriais.",
    start_url: "/",
    display: "standalone",
    background_color: "#050a12",
    theme_color: "#24d7ff",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml"
      }
    ]
  };
}

