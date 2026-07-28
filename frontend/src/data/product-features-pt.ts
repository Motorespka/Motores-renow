/** Mapa de funcionalidades (produto) — alinhado à página /funcionalidades. */

export const FUNCIONALIDADES_WA_MSG =
  "Olá! Quero alinhar o roadmap da Moto-Renow com a nossa oficina (o que já usamos vs. o que falta).";

type FeatureBlock = { title: string; items: string[] };
type FeatureSection = {
  id: string;
  title: string;
  eyebrow?: string;
  lead?: string;
  blocks: FeatureBlock[];
};

export const featureSections: FeatureSection[] = [
  {
    id: "donos-resumo",
    title: "Resumo para o dono",
    eyebrow: "GESTÃO",
    lead: "O que importa no dia a dia: saber onde está cada motor e o que a equipa precisa de si.",
    blocks: [
      {
        title: "Controlo operacional",
        items: [
          "Fila e prioridades visíveis",
          "Estados de OS sem chase no WhatsApp interno",
          "Histórico para reclamações e garantia"
        ]
      },
      {
        title: "Decisão comercial",
        items: [
          "Mapa de módulos para conversa de plano",
          "Sem pagamento neste site",
          "Contacto humano por WhatsApp"
        ]
      }
    ]
  },
  {
    id: "fluxo-30s",
    title: "Fluxo em 30 segundos",
    eyebrow: "OPERAÇÃO",
    lead: "Do recebimento à entrega com rasto técnico.",
    blocks: [
      {
        title: "Entrada",
        items: ["OS com motor / cliente", "Foto e plaqueta quando disponível", "Triagem rápida"]
      },
      {
        title: "Bancada → entrega",
        items: ["Consulta ao acervo", "Intervenção e testes", "PDF / fecho com histórico"]
      }
    ]
  },
  {
    id: "entrada-triagem",
    title: "Entrada e triagem",
    blocks: [
      {
        title: "Recebimento",
        items: ["Identificação do motor", "Notas do cliente", "Prioridade e prazo"]
      },
      {
        title: "OCR / plaqueta (quando activo)",
        items: ["Leitura assistida", "Revisão humana obrigatória", "Campos validados no cadastro"]
      }
    ]
  },
  {
    id: "diagnostico",
    title: "Diagnóstico",
    blocks: [
      {
        title: "Consulta técnica",
        items: ["Busca por marca, polos, RPM, tensão", "Ficha completa", "Alertas de revisão"]
      },
      {
        title: "Gêmeo digital (camada avançada)",
        items: ["Leitura física assistida", "Comparativos", "Não substitui ensaio de bancada"]
      }
    ]
  },
  {
    id: "intervencao-os",
    title: "Intervenção e OS",
    blocks: [
      {
        title: "Ordens de serviço",
        items: ["Etapas da oficina", "Responsável / turno", "Notas e anexos"]
      },
      {
        title: "Biblioteca de cálculos",
        items: ["Receitas reutilizáveis", "Revisões", "Testes de bancada registados"]
      }
    ]
  },
  {
    id: "qualidade-entrega",
    title: "Qualidade e entrega",
    blocks: [
      {
        title: "Conferência",
        items: ["Segundo olhar em casos sensíveis", "Checklist antes de fechar", "Rasto auditável"]
      },
      {
        title: "Entrega",
        items: ["PDF técnico", "Histórico no Supabase", "Comunicação ao cliente"]
      }
    ]
  },
  {
    id: "stock-compras",
    title: "Stock e compras",
    eyebrow: "ROADMAP / PLANO",
    lead: "Itens que podem estar no plano Oficina/Pro consoante a conversa comercial.",
    blocks: [
      {
        title: "Peças e fio",
        items: ["Notas de necessidade na OS", "Ligação a fornecedor (a combinar)", "Evitar paragem por falta de rasto"]
      },
      {
        title: "Limites honestos",
        items: ["Não é ERP completo de armazém", "Encaixe exacto define-se consigo"]
      }
    ]
  },
  {
    id: "cliente-comunicacao",
    title: "Cliente e comunicação",
    blocks: [
      {
        title: "Estado sem ruído",
        items: ["Resposta baseada em OS", "Menos “vou ver e digo”", "Histórico partilhável internamente"]
      },
      {
        title: "Comercial",
        items: ["WhatsApp para planos e condições", "Sem checkout no site"]
      }
    ]
  },
  {
    id: "gestao-dono",
    title: "Gestão para o dono",
    blocks: [
      {
        title: "Indicadores",
        items: ["Volume na fila", "OS activas", "Visão de carga da equipa"]
      },
      {
        title: "Equipa",
        items: ["Acessos por perfil", "Menos dependência de um único técnico"]
      }
    ]
  },
  {
    id: "diferenciacao",
    title: "Área técnica diferenciada",
    blocks: [
      {
        title: "Moto-Renow vs. genéricos",
        items: ["Linguagem de rebobinagem", "Acervo e biblioteca de motores", "Fluxo de oficina eléctrica"]
      },
      {
        title: "IA com travão",
        items: ["OCR e sugestões com revisão", "Não substitui norma nem laudo legal"]
      }
    ]
  },
  {
    id: "para-oficinas",
    title: "Segmentos de oficina",
    blocks: [
      {
        title: "Quem encaixa",
        items: ["Oficinas de manutenção de motores", "Equipas com vários turnos", "Casas com acervo próprio"]
      },
      {
        title: "O que alinhar na demo",
        items: ["Tipos de motor habituais", "Nº de técnicos", "O que já usam hoje"]
      }
    ]
  },
  {
    id: "conteudo-area",
    title: "Glossário rápido",
    blocks: [
      {
        title: "Termos",
        items: ["OS = ordem de serviço", "Acervo = base de motores", "Conferência = segundo olhar técnico"]
      },
      {
        title: "Dados",
        items: ["Supabase como backend", "Streamlit legado → painel Next/Vercel"]
      }
    ]
  },
  {
    id: "materiais-decisao",
    title: "Materiais para decidir",
    blocks: [
      {
        title: "No site",
        items: ["Planos (visão de produto)", "Para oficinas", "Engenharia / manutenção eléctrica"]
      },
      {
        title: "Por WhatsApp",
        items: ["Proposta", "Acessos de trial", "Condições e faturação"]
      }
    ]
  },
  {
    id: "juridico-linha",
    title: "RGPD e responsabilidade",
    blocks: [
      {
        title: "Linha clara",
        items: ["Dados operacionais na conta combinada", "Sem pagamento nesta página", "Ferramenta de apoio — não substitui ensaio calibrado"]
      },
      {
        title: "Contrato",
        items: ["NDA / cláusulas à parte se necessário", "Contacto humano antes de expor dados sensíveis"]
      }
    ]
  },
  {
    id: "contacto-humano",
    title: "Suporte humano",
    blocks: [
      {
        title: "Como falamos",
        items: ["WhatsApp comercial e onboarding", "Login só para quem já tem acesso"]
      },
      {
        title: "O que NÃO fazer no site",
        items: ["Não enviar cartão/IBAN", "Não colar secrets em formulários públicos"]
      }
    ]
  },
  {
    id: "site-o-que-evitar",
    title: "Foco do site",
    blocks: [
      {
        title: "Este site serve para",
        items: ["Explicar produto", "Entrar no painel", "Pedir demo"]
      },
      {
        title: "Evitar aqui",
        items: ["Checkout", "Upload de bases confidenciais sem acordo", "Promessas de substituição total de ERP"]
      }
    ]
  }
];

export const featureFaq: { q: string; a: string }[] = [
  {
    q: "Tudo isto já está no painel?",
    a: "Nem tudo na mesma versão. Use a lista como mapa; na demo alinhamos o que está activo no vosso acesso."
  },
  {
    q: "Substitui o Streamlit?",
    a: "O objectivo é o painel Vercel (Next) com a mesma lógica de negócio e Supabase. A migração pode ser faseada."
  },
  {
    q: "Como peço acesso?",
    a: "WhatsApp (botões nesta página) ou /login se já tiver conta."
  },
  {
    q: "Há pagamento online?",
    a: "Não neste site. Condições e faturação tratam-se por WhatsApp."
  }
];
