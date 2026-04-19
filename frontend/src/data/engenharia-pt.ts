/** Página pública: manutenção de motores elétricos — linguagem de engenharia de campo (sem código). */

export const ENGENHARIA_WA_MSG =
  "Olá! Sou técnico/engenheiro de manutenção de motores elétricos e quero perceber profundidade técnica da Moto-Renow (consulta, OS, conferência).";

export const focoTecnico: { title: string; body: string }[] = [
  {
    title: "Consulta e rasto técnico",
    body: "Ficha do motor, leitura de placa e histórico para reduzir ambiguidade entre desmontagem, rebobinagem e ensaio — com alertas quando convém revisão humana."
  },
  {
    title: "Ordens de serviço e etapas",
    body: "Estado da intervenção visível para a equipa: menos retrabalho por falta de contexto entre turnos."
  },
  {
    title: "Conferência e critério",
    body: "Fluxo para segundo olhar antes de fechar trabalho sensível — alinhado a boas práticas de oficina, não substitui norma nem laudo legal quando aplicável."
  },
  {
    title: "Biblioteca e receitas (quando ativo no plano)",
    body: "Reutilização de parâmetros e revisões técnicas — útil para padronizar bobinagens e revisões na casa."
  }
];

export const honestidade: string[] = [
  "A plataforma apoia decisão e registo; não substitui ensaio, instrumentação calibrada nem experiência do técnico.",
  "Conteúdo de catálogo e regras de negócio combinam-se com a vossa operação — o contacto comercial é por WhatsApp, sem pagamento neste site."
];

export const checklistCampo: string[] = [
  "Confirmar identidade do motor (placa, frame, kW, tensão, rpm) antes de assumir bobinagem.",
  "Registar ensaios relevantes (isolamento, continuidade, ensaio a seco quando aplicável) no fluxo da OS.",
  "Deixar explícito o que ficou por fazer ou em espera de peça — para o próximo turno ou para o cliente."
];

export const faqEng: { q: string; a: string }[] = [
  {
    q: "Isto substitui o software que já uso na oficina?",
    a: "Depende do que usam hoje. A Moto-Renow foca-se no rasto técnico e na oficina de motores; a integração com outros sistemas é conversa caso a caso."
  },
  {
    q: "Serve para motores de AT e de pequena potência?",
    a: "O desenho é pensado em oficina de manutenção elétrica; o encaixe exacto diz-se melhor com exemplos dos vossos tipos habituais."
  }
];
