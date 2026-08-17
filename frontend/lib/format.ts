export const money = (value: number | string = 0) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    Number(value),
  );
export const shortDate = (value: string) =>
  new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(
    new Date(value + "T12:00:00Z"),
  );
export const categoryLabel: Record<string, string> = {
  ACCOMMODATION: "Hospedagem",
  FUEL: "Combustível",
  TOLL: "Pedágio",
  FOOD: "Alimentação",
  DRINKS: "Bebidas",
  MARKET: "Mercado",
  TOUR: "Passeios",
  TRANSPORT: "Transporte",
  OTHER: "Outros",
};
export const statusLabel: Record<string, string> = {
  PLANNING: "Planejamento",
  CONFIRMED: "Confirmado",
  IN_PROGRESS: "Em andamento",
  FINISHED: "Finalizada",
  CANCELLED: "Cancelado",
  INVITED: "Convidado",
  MAYBE: "Talvez",
  WITHDREW: "Desistiu",
  CANDIDATE: "Candidata",
  VOTING: "Em votação",
  APPROVED: "Aprovado",
  DISCARDED: "Descartado",
  BOOKED: "Reservado",
  DRAFT: "Rascunho",
  OPEN: "Aberta",
  CLOSED: "Fechada",
  PENDING: "Pendente",
};
