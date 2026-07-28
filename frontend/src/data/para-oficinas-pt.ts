/** Conteúdo público: página Para oficinas (donos / gestores). */

export const PARA_OFICINAS_WA_MSG =
  "Olá! Sou dono/gestor de oficina de motores e quero perceber como a Moto-Renow encaixa na nossa operação (equipa, OS, prazos).";

export const doresTipicas: string[] = [
  "Histórico do motor espalhado em papel, WhatsApp e cabeça de quem estava no turno.",
  "Retrabalho porque o próximo técnico não vê o que já foi medido ou combinado.",
  "Dificuldade em priorizar a fila quando entram vários motores no mesmo dia.",
  "Cliente a pedir prazo e estado — e a equipa a improvisar a resposta.",
  "Receitas de bobinagem boas que ficam num PC ou pasta e ninguém encontra.",
  "Falta de rasto quando há reclamação ou garantia após a entrega."
];

export const oQueAjudamos: { title: string; body: string }[] = [
  {
    title: "Visibilidade da fila",
    body: "Painel e estados de OS para ver o que está em bancada, à espera de peça ou pronto a entregar."
  },
  {
    title: "Rasto técnico partilhável",
    body: "Ficha do motor e intervenções no mesmo sítio — menos dependência de “quem lembra”."
  },
  {
    title: "Conversa comercial limpa",
    body: "Planos e condições por WhatsApp; no site não pedimos cartão nem dados bancários."
  }
];

export const transparencia: string[] = [
  "Nesta aplicação não há checkout nem captura de IBAN/cartão.",
  "Proposta, faturação e NDA (se aplicável) tratam-se por WhatsApp ou contrato à parte.",
  "Acesso à equipa e dados de motores ficam no vosso ambiente (Supabase / conta combinada).",
  "O que aparece nas páginas públicas é mapa de produto — o encaixe exacto combina-se caso a caso."
];

export const faqDono: { q: string; a: string }[] = [
  {
    q: "Quanto custa?",
    a: "Investimento sob consulta. Preferimos alinhar módulos, nº de utilizadores e prioridades antes de fechar valores — por WhatsApp."
  },
  {
    q: "Serve para oficina pequena?",
    a: "Sim. O Essencial foca consulta e registo; Oficina e Pro escalam filas, OS e conferência consoante o volume."
  },
  {
    q: "Os dados ficam onde?",
    a: "No projeto Supabase / infraestrutura combinada convosco. Não usamos o site de marketing para recolher pagamentos."
  },
  {
    q: "Preciso abandonar o Streamlit?",
    a: "A migração para o painel Vercel (Next) é gradual: o objectivo é a mesma operação com UI mais estável em produção."
  }
];
