"use client";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, logout } from "@/lib/api";
import { categoryLabel, money, shortDate, statusLabel } from "@/lib/format";
import type {
  Accommodation,
  Dashboard,
  Expense,
  Participant,
  Payment,
  Scenario,
  Trip,
} from "@/types";
import { Badge, Empty, Modal, Progress, Toast } from "@/components/ui";

type View =
  | "dashboard"
  | "people"
  | "stays"
  | "scenarios"
  | "finance"
  | "payments"
  | "settings";
type ModalType =
  | "participant"
  | "group"
  | "stay"
  | "scenario"
  | "expense"
  | "payment"
  | "trip"
  | null;
const menu: { id: View; label: string; icon: string }[] = [
  { id: "dashboard", label: "Visão geral", icon: "⌂" },
  { id: "people", label: "Pessoas e grupos", icon: "♙" },
  { id: "stays", label: "Hospedagens", icon: "⌑" },
  { id: "scenarios", label: "Cenários", icon: "◇" },
  { id: "finance", label: "Financeiro", icon: "$" },
  { id: "payments", label: "Pagamentos", icon: "✓" },
  { id: "settings", label: "Configurações", icon: "⚙" },
];
const tones = (status: string) =>
  status === "CONFIRMED" || status === "APPROVED" || status === "BOOKED"
    ? "good"
    : status === "MAYBE" || status === "VOTING" || status === "PENDING"
      ? "warn"
      : status === "WITHDREW" || status === "CANCELLED"
        ? "bad"
        : "neutral";

export default function AppPage() {
  const router = useRouter();
  const [view, setView] = useState<View>("dashboard");
  const [modal, setModal] = useState<ModalType>(null);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [stays, setStays] = useState<Accommodation[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [groups, setGroups] = useState<
    { id: number; name: string; participant_ids: number[] }[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const trips = await api<Trip[]>("/trips");
      if (!trips.length) throw new Error("Nenhuma viagem disponível");
      const current = trips[0];
      setTrip(current);
      const base = `/trips/${current.id}`;
      const [d, p, a, s, e, pa, g] = await Promise.all([
        api<Dashboard>(`${base}/dashboard`),
        api<Participant[]>(`${base}/participants`),
        api<Accommodation[]>(`${base}/accommodations`),
        api<Scenario[]>(`${base}/scenarios`),
        api<Expense[]>(`${base}/expenses`),
        api<Payment[]>(`${base}/payments`),
        api<{ id: number; name: string; participant_ids: number[] }[]>(
          `${base}/groups`,
        ),
      ]);
      setDashboard(d);
      setParticipants(p);
      setStays(a);
      setScenarios(s);
      setExpenses(e);
      setPayments(pa);
      setGroups(g);
    } catch (e) {
      if ((e as { status?: number }).status === 401) {
        logout();
        return;
      }
      setError(
        e instanceof Error ? e.message : "Não foi possível carregar a viagem",
      );
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    if (!localStorage.getItem("trip_token")) {
      router.replace("/login");
      return;
    }
    load();
  }, [load, router]);
  async function submitted(message: string) {
    setModal(null);
    setToast(message);
    await load();
    setTimeout(() => setToast(""), 3200);
  }
  if (loading)
    return <div className="loading">Carregando os detalhes da viagem…</div>;
  if (error || !trip || !dashboard)
    return (
      <div className="loading">
        <h2>Não foi possível abrir a viagem</h2>
        <p>{error}</p>
        <button className="primary" onClick={load}>
          Tentar novamente
        </button>
      </div>
    );
  const user = JSON.parse(
    localStorage.getItem("trip_user") || '{"name":"Viajante"}',
  );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand light">
          <span className="brand-mark">B</span>
          <span>Bora!</span>
        </div>
        <nav className="nav">
          {menu.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "active" : ""}
              onClick={() => setView(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-chip">
            <span className="avatar">{user.name[0]}</span>
            <div>
              <strong>{user.name}</strong>
              <small>Administrador</small>
            </div>
          </div>
          <button className="logout" onClick={logout}>
            Sair da conta
          </button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div className="trip-selector">
            <span className="trip-dot">☀</span>
            <div>
              <strong>{trip.name}</strong>
              <span>
                {trip.destination} · {shortDate(trip.start_date)} —{" "}
                {shortDate(trip.end_date)}
              </span>
            </div>
          </div>
          <div className="top-actions">
            <button className="icon-button">?</button>
            <button className="icon-button">⌁</button>
          </div>
        </header>
        <div className="content">
          {view === "dashboard" && (
            <DashboardView
              data={dashboard}
              trip={trip}
              expenses={expenses}
              onAction={setModal}
            />
          )}
          {view === "people" && (
            <PeopleView
              participants={participants}
              groups={groups}
              onAction={setModal}
            />
          )}
          {view === "stays" && <StaysView stays={stays} onAction={setModal} />}
          {view === "scenarios" && (
            <ScenariosView
              scenarios={scenarios}
              tripId={trip.id}
              participantId={participants[0]?.id}
              reload={load}
              onAction={setModal}
            />
          )}
          {view === "finance" && (
            <FinanceView
              expenses={expenses}
              participants={participants}
              dashboard={dashboard}
              onAction={setModal}
            />
          )}
          {view === "payments" && (
            <PaymentsView
              payments={payments}
              participants={participants}
              onAction={setModal}
            />
          )}
          {view === "settings" && (
            <SettingsView trip={trip} onAction={setModal} />
          )}
        </div>
      </main>
      <nav className="mobile-nav">
        {menu.slice(0, 5).map((item) => (
          <button
            key={item.id}
            className={view === item.id ? "active" : ""}
            onClick={() => setView(item.id)}
          >
            <span>{item.icon}</span>
            {item.label.split(" ")[0]}
          </button>
        ))}
      </nav>
      {modal && (
        <ActionModal
          type={modal}
          trip={trip}
          participants={participants}
          stays={stays}
          onClose={() => setModal(null)}
          onDone={submitted}
        />
      )}{" "}
      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </div>
  );
}

function Heading({
  eyebrow,
  title,
  description,
  button,
  onClick,
}: {
  eyebrow: string;
  title: string;
  description: string;
  button?: string;
  onClick?: () => void;
}) {
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {button && (
        <button className="primary" onClick={onClick}>
          ＋ {button}
        </button>
      )}
    </div>
  );
}
function Metric({
  label,
  value,
  note,
  tint = "#f3eadb",
}: {
  label: string;
  value: string;
  note: string;
  tint?: string;
}) {
  return (
    <article
      className="metric"
      style={{ "--tint": tint } as React.CSSProperties}
    >
      <div className="metric-label">
        <span>{label}</span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
    </article>
  );
}

function DashboardView({
  data,
  trip,
  expenses,
  onAction,
}: {
  data: Dashboard;
  trip: Trip;
  expenses: Expense[];
  onAction: (m: ModalType) => void;
}) {
  const categories = Object.entries(data.expenses_by_category).sort(
    (a, b) => b[1] - a[1],
  );
  const max = Math.max(...categories.map(([, v]) => Number(v)), 1);
  return (
    <section>
      <Heading
        eyebrow="VISÃO GERAL"
        title={`Olá, ${JSON.parse(localStorage.getItem("trip_user") || '{"name":"viajante"}').name.split(" ")[0]}!`}
        description={`Faltam ${Math.ceil((new Date(trip.start_date).getTime() - Date.now()) / 86400000)} dias. Veja como estão os preparativos.`}
        button="Nova despesa"
        onClick={() => onAction("expense")}
      />
      <div className="cards">
        <Metric
          label="Participantes"
          value={`${data.participants.confirmed} / ${data.participants.total}`}
          note="confirmados na viagem"
          tint="#dceff2"
        />
        <Metric
          label="Orçamento estimado"
          value={money(data.budget.estimated)}
          note={`${money(data.budget.actual)} já realizados`}
          tint="#f3eadb"
        />
        <Metric
          label="Recebido"
          value={money(data.payments.received)}
          note={`${money(data.payments.pending)} a receber`}
          tint="#d9eee8"
        />
        <Metric
          label="Cenários"
          value={String(data.scenarios)}
          note="opções de hospedagem"
          tint="#fee8e2"
        />
      </div>
      <div className="grid-2">
        <article className="panel">
          <div className="panel-header">
            <h2>Despesas por categoria</h2>
            <span>{expenses.length} lançamentos</span>
          </div>
          <div className="bars">
            {categories.map(([category, value]) => (
              <div className="bar-row" key={category}>
                <span>{categoryLabel[category] || category}</span>
                <Progress
                  value={(Number(value) / max) * 100}
                  color={category === "ACCOMMODATION" ? "#174f56" : "#f0735e"}
                />
                <strong>{money(value)}</strong>
              </div>
            ))}
          </div>
        </article>
        <article className="panel">
          <div className="panel-header">
            <h2>Status do grupo</h2>
            <span>{data.participants.total} pessoas</span>
          </div>
          <div className="donut-wrap">
            <div className="donut" />
            <div className="legend">
              {Object.entries(data.participants.statuses).map(
                ([status, count], i) => (
                  <div key={status}>
                    <i
                      style={{
                        background: [
                          "#f0735e",
                          "#f3c06e",
                          "#d9dfdd",
                          "#174f56",
                        ][i % 4],
                      }}
                    />
                    <span>
                      {statusLabel[status] || status}: <strong>{count}</strong>
                    </span>
                  </div>
                ),
              )}
            </div>
          </div>
        </article>
      </div>
    </section>
  );
}

function PeopleView({
  participants,
  groups,
  onAction,
}: {
  participants: Participant[];
  groups: { id: number; name: string; participant_ids: number[] }[];
  onAction: (m: ModalType) => void;
}) {
  const [query, setQuery] = useState("");
  const list = participants.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <section>
      <Heading
        eyebrow="ORGANIZAÇÃO"
        title="Pessoas e grupos"
        description="Um cadastro por pessoa, todos os vínculos preservados."
        button="Adicionar pessoa"
        onClick={() => onAction("participant")}
      />
      <div className="toolbar">
        <input
          className="search"
          placeholder="Buscar por nome…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="secondary" onClick={() => onAction("group")}>
          ＋ Criar grupo
        </button>
        {groups.map((g) => (
          <Badge key={g.id} tone="blue">
            {g.name} · {g.participant_ids.length}
          </Badge>
        ))}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Pessoa</th>
              <th>Grupo</th>
              <th>Devido</th>
              <th>Pago</th>
              <th>Saldo</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {list.map((p) => (
              <tr key={p.id}>
                <td>
                  <div className="person">
                    <span className="avatar">
                      {p.name
                        .split(" ")
                        .map((n) => n[0])
                        .slice(0, 2)}
                    </span>
                    <div>
                      <strong>{p.name}</strong>
                      <small>
                        {p.participant_type === "CHILD"
                          ? "Criança"
                          : p.email || "Adulto"}
                      </small>
                    </div>
                  </div>
                </td>
                <td>{p.groups?.join(", ") || "—"}</td>
                <td>{money(p.total_due)}</td>
                <td>{money(p.total_paid)}</td>
                <td>
                  <strong>{money(p.balance)}</strong>
                </td>
                <td>
                  <Badge tone={tones(p.status)}>
                    {statusLabel[p.status] || p.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StaysView({
  stays,
  onAction,
}: {
  stays: Accommodation[];
  onAction: (m: ModalType) => void;
}) {
  return (
    <section>
      <Heading
        eyebrow="ONDE FICAR"
        title="Hospedagens candidatas"
        description="Compare espaço, localização e custo antes de decidir."
        button="Nova hospedagem"
        onClick={() => onAction("stay")}
      />
      <div className="card-grid">
        {stays.map((stay) => (
          <article className="stay-card" key={stay.id}>
            <Badge tone={tones(stay.status)}>
              {statusLabel[stay.status] || stay.status}
            </Badge>
            <h3>{stay.name}</h3>
            <p className="muted">
              {stay.city}
              {stay.distance_to_beach
                ? ` · ${stay.distance_to_beach} da praia`
                : ""}
            </p>
            <div className="stay-meta">
              <span>⌂ {stay.bedrooms} quartos</span>
              <span>◫ {stay.bathrooms} banheiros</span>
            </div>
            <div className="occupancy">
              <span>
                {stay.occupancy} / {stay.capacity} pessoas
              </span>
              <Progress value={(stay.occupancy / stay.capacity) * 100} />
            </div>
            <div className="stay-price">
              <div>
                <small className="muted">Total + taxas</small>
                <br />
                <strong>
                  {money(
                    Number(stay.total_price) +
                      Number(stay.cleaning_fee) +
                      Number(stay.other_fees),
                  )}
                </strong>
              </div>
              <button className="secondary">Detalhes</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScenariosView({
  scenarios,
  tripId,
  participantId,
  reload,
  onAction,
}: {
  scenarios: Scenario[];
  tripId: number;
  participantId?: number;
  reload: () => Promise<void>;
  onAction: (m: ModalType) => void;
}) {
  async function vote(id: number, value: string) {
    if (!participantId) return;
    await api(`/trips/${tripId}/scenarios/${id}/vote`, {
      method: "PUT",
      body: JSON.stringify({ participant_id: participantId, vote: value }),
    });
    await reload();
  }
  return (
    <section>
      <Heading
        eyebrow="DECISÃO EM GRUPO"
        title="Comparador de cenários"
        description="Capacidade, estrutura, custo e votos lado a lado."
        button="Novo cenário"
        onClick={() => onAction("scenario")}
      />
      <div className="card-grid">
        {scenarios.map((s, index) => (
          <article
            className={`scenario-card ${index === 0 ? "featured" : ""}`}
            key={s.id}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Badge tone={tones(s.status)}>
                {statusLabel[s.status] || s.status}
              </Badge>
              {index === 0 && <Badge tone="good">Melhor custo</Badge>}
            </div>
            <h3>{s.name}</h3>
            <p className="muted">{s.accommodations.join(" + ")}</p>
            <div className="scenario-total">{money(s.total_cost)}</div>
            <small className="muted">
              {money(s.cost_per_person)} por pessoa confirmada
            </small>
            <div className="scenario-stats">
              <div>
                <strong>{s.capacity}</strong>
                <span>CAPACIDADE</span>
              </div>
              <div>
                <strong>{s.bedrooms}</strong>
                <span>QUARTOS</span>
              </div>
              <div>
                <strong>{s.bathrooms}</strong>
                <span>BANHEIROS</span>
              </div>
            </div>
            <div className="votes">
              <button className="vote" onClick={() => vote(s.id, "YES")}>
                👍 {s.votes.YES} sim
              </button>
              <button className="vote" onClick={() => vote(s.id, "MAYBE")}>
                🤔 {s.votes.MAYBE} talvez
              </button>
              <button className="vote" onClick={() => vote(s.id, "NO")}>
                👎 {s.votes.NO} não
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function FinanceView({
  expenses,
  participants,
  dashboard,
  onAction,
}: {
  expenses: Expense[];
  participants: Participant[];
  dashboard: Dashboard;
  onAction: (m: ModalType) => void;
}) {
  return (
    <section>
      <Heading
        eyebrow="CONTROLE FINANCEIRO"
        title="Despesas e rateios"
        description="Todos os cálculos acontecem no servidor e fecham até o último centavo."
        button="Nova despesa"
        onClick={() => onAction("expense")}
      />
      <div className="cards" style={{ marginBottom: 18 }}>
        <Metric
          label="Orçado"
          value={money(dashboard.budget.estimated)}
          note="previsão total"
        />
        <Metric
          label="Realizado"
          value={money(dashboard.budget.actual)}
          note={`${Math.round((Number(dashboard.budget.actual) / Math.max(Number(dashboard.budget.estimated), 1)) * 100)}% do orçamento`}
        />
        <Metric
          label="Recebido"
          value={money(dashboard.payments.received)}
          note="pagamentos confirmados"
        />
        <Metric
          label="A receber"
          value={money(dashboard.payments.pending)}
          note="saldo do grupo"
        />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Despesa</th>
              <th>Categoria</th>
              <th>Data</th>
              <th>Rateio</th>
              <th>Pessoas</th>
              <th>Valor</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((e) => (
              <tr key={e.id}>
                <td>
                  <strong>{e.description}</strong>
                </td>
                <td>{categoryLabel[e.category] || e.category}</td>
                <td>{shortDate(e.expense_date)}</td>
                <td>{e.allocation_type}</td>
                <td>{e.allocations.length}</td>
                <td>
                  <strong>{money(e.amount)}</strong>
                </td>
                <td>
                  <Badge tone={tones(e.status)}>
                    {statusLabel[e.status] || e.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PaymentsView({
  payments,
  participants,
  onAction,
}: {
  payments: Payment[];
  participants: Participant[];
  onAction: (m: ModalType) => void;
}) {
  const names = Object.fromEntries(participants.map((p) => [p.id, p.name]));
  return (
    <section>
      <Heading
        eyebrow="CAIXA DA VIAGEM"
        title="Pagamentos"
        description="Entradas confirmadas, pendências e comprovantes em um lugar."
        button="Registrar pagamento"
        onClick={() => onAction("payment")}
      />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Participante</th>
              <th>Descrição</th>
              <th>Data</th>
              <th>Método</th>
              <th>Valor</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((p) => (
              <tr key={p.id}>
                <td>
                  <strong>{names[p.participant_id] || "Participante"}</strong>
                </td>
                <td>{p.description || "Pagamento"}</td>
                <td>{shortDate(p.payment_date)}</td>
                <td>{p.payment_method}</td>
                <td>
                  <strong>{money(p.amount)}</strong>
                </td>
                <td>
                  <Badge tone={tones(p.status)}>
                    {statusLabel[p.status] || p.status}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SettingsView({
  trip,
  onAction,
}: {
  trip: Trip;
  onAction: (m: ModalType) => void;
}) {
  return (
    <section>
      <Heading
        eyebrow="CONFIGURAÇÕES"
        title="Dados da viagem"
        description="Informações gerais usadas em todo o sistema."
        button="Editar viagem"
        onClick={() => onAction("trip")}
      />
      <article className="panel">
        <div className="form-grid">
          <div>
            <small className="muted">NOME</small>
            <h3>{trip.name}</h3>
          </div>
          <div>
            <small className="muted">DESTINO</small>
            <h3>{trip.destination}</h3>
          </div>
          <div>
            <small className="muted">PERÍODO</small>
            <p>
              {shortDate(trip.start_date)} a {shortDate(trip.end_date)}
            </p>
          </div>
          <div>
            <small className="muted">STATUS</small>
            <p>
              <Badge>{statusLabel[trip.status] || trip.status}</Badge>
            </p>
          </div>
          <div className="field wide">
            <small className="muted">DESCRIÇÃO</small>
            <p>{trip.description || "Sem descrição"}</p>
          </div>
        </div>
      </article>
    </section>
  );
}

function ActionModal({
  type,
  trip,
  participants,
  stays,
  onClose,
  onDone,
}: {
  type: Exclude<ModalType, null>;
  trip: Trip;
  participants: Participant[];
  stays: Accommodation[];
  onClose: () => void;
  onDone: (m: string) => Promise<void>;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const text = (key: string) => String(form.get(key) || "");
    const number = (key: string) => Number(form.get(key) || 0);
    const checked = (key: string) => form.getAll(key).map(Number);
    let path = `/trips/${trip.id}`;
    let body: Record<string, unknown> = {};
    if (type === "participant") {
      path += "/participants";
      body = {
        name: text("name"),
        email: text("email") || null,
        phone: text("phone") || null,
        participant_type: text("participant_type"),
        status: text("status"),
        notes: null,
      };
    }
    if (type === "group") {
      path += "/groups";
      body = { name: text("name"), description: text("description") || null };
    }
    if (type === "stay") {
      path += "/accommodations";
      body = {
        name: text("name"),
        city: text("city"),
        address: text("address") || null,
        capacity: number("capacity"),
        bedrooms: number("bedrooms"),
        bathrooms: number("bathrooms"),
        total_price: number("total_price"),
        cleaning_fee: number("cleaning_fee"),
        status: "CANDIDATE",
      };
    }
    if (type === "scenario") {
      path += "/scenarios";
      body = {
        name: text("name"),
        description: text("description") || null,
        status: "DRAFT",
        extra_costs: number("extra_costs"),
        accommodation_ids: checked("accommodation_ids"),
      };
    }
    if (type === "expense") {
      path += "/expenses";
      const allocation = text("allocation_type");
      body = {
        description: text("description"),
        category: text("category"),
        amount: number("amount"),
        expense_date: text("expense_date"),
        paid_by_participant_id: number("paid_by") || null,
        allocation_type: allocation,
        selected_participant_ids: checked("participant_ids"),
        accommodation_id: null,
        vehicle_id: null,
        group_id: null,
        individual_participant_id:
          allocation === "INDIVIDUAL" ? number("resource_id") || null : null,
        status: "OPEN",
      };
    }
    if (type === "payment") {
      path += "/payments";
      body = {
        participant_id: number("participant_id"),
        amount: number("amount"),
        payment_date: text("payment_date"),
        payment_method: text("payment_method"),
        description: text("description") || null,
        status: "CONFIRMED",
      };
    }
    if (type === "trip") {
      body = {
        name: text("name"),
        destination: text("destination"),
        start_date: text("start_date"),
        end_date: text("end_date"),
        status: text("status"),
        description: text("description") || null,
      };
    }
    try {
      const created = await api<{ id?: number }>(path, {
        method: type === "trip" ? "PUT" : "POST",
        body: JSON.stringify(body),
      });
      if (type === "group" && created.id) {
        await api(`/trips/${trip.id}/groups/${created.id}/participants`, {
          method: "PUT",
          body: JSON.stringify({ participant_ids: checked("participant_ids") }),
        });
      }
      await onDone(
        type === "trip"
          ? "Viagem atualizada"
          : `${labels[type]} criado com sucesso`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível salvar");
    } finally {
      setSaving(false);
    }
  }
  const labels: Record<string, string> = {
    participant: "Participante",
    group: "Grupo",
    stay: "Hospedagem",
    scenario: "Cenário",
    expense: "Despesa",
    payment: "Pagamento",
    trip: "Viagem",
  };
  return (
    <Modal
      title={
        type === "trip" ? "Editar viagem" : `Novo ${labels[type].toLowerCase()}`
      }
      subtitle="Os dados ficam disponíveis imediatamente para o grupo."
      onClose={onClose}
    >
      <form className="form-grid" onSubmit={submit}>
        {type === "participant" && (
          <>
            <Field name="name" label="Nome completo" required />
            <Field name="email" label="E-mail" type="email" />
            <Field name="phone" label="Telefone" />
            <Select
              name="participant_type"
              label="Tipo"
              options={{ ADULT: "Adulto", CHILD: "Criança" }}
            />
            <Select
              name="status"
              label="Status"
              options={{
                INVITED: "Convidado",
                MAYBE: "Talvez",
                CONFIRMED: "Confirmado",
              }}
            />
          </>
        )}
        {type === "group" && (
          <>
            <Field name="name" label="Nome do grupo" required />
            <Field name="description" label="Descrição" />
            <CheckList
              name="participant_ids"
              label="Participantes"
              items={participants.map((p) => ({ id: p.id, label: p.name }))}
            />
          </>
        )}
        {type === "stay" && (
          <>
            <Field name="name" label="Nome da hospedagem" required />
            <Field name="city" label="Cidade" value="Garopaba" required />
            <Field name="address" label="Endereço" wide />
            <Field
              name="capacity"
              label="Capacidade"
              type="number"
              value="10"
              required
            />
            <Field name="bedrooms" label="Quartos" type="number" value="3" />
            <Field name="bathrooms" label="Banheiros" type="number" value="2" />
            <Field
              name="total_price"
              label="Valor total"
              type="number"
              value="0"
              required
            />
            <Field
              name="cleaning_fee"
              label="Taxa de limpeza"
              type="number"
              value="0"
            />
          </>
        )}
        {type === "scenario" && (
          <>
            <Field name="name" label="Nome do cenário" required wide />
            <Field name="description" label="Descrição" wide />
            <Field
              name="extra_costs"
              label="Custos adicionais"
              type="number"
              value="0"
            />
            <CheckList
              name="accommodation_ids"
              label="Hospedagens"
              items={stays.map((s) => ({ id: s.id, label: s.name }))}
            />
          </>
        )}
        {type === "expense" && (
          <>
            <Field name="description" label="Descrição" required />
            <Select name="category" label="Categoria" options={categoryLabel} />
            <Field
              name="amount"
              label="Valor"
              type="number"
              step="0.01"
              required
            />
            <Field
              name="expense_date"
              label="Data"
              type="date"
              value={new Date().toISOString().slice(0, 10)}
              required
            />
            <Select
              name="paid_by"
              label="Pago por"
              options={Object.fromEntries(
                participants.map((p) => [p.id, p.name]),
              )}
            />
            <Select
              name="allocation_type"
              label="Tipo de rateio"
              options={{
                ALL: "Todos confirmados",
                SELECTED: "Selecionados",
                INDIVIDUAL: "Individual",
              }}
            />
            <Select
              name="resource_id"
              label="Pessoa (para rateio individual)"
              options={Object.fromEntries(
                participants.map((p) => [p.id, p.name]),
              )}
            />
            <CheckList
              name="participant_ids"
              label="Participantes (para selecionados)"
              items={participants.map((p) => ({ id: p.id, label: p.name }))}
            />
          </>
        )}
        {type === "payment" && (
          <>
            <Select
              name="participant_id"
              label="Participante"
              options={Object.fromEntries(
                participants.map((p) => [p.id, p.name]),
              )}
            />
            <Field
              name="amount"
              label="Valor"
              type="number"
              step="0.01"
              required
            />
            <Field
              name="payment_date"
              label="Data"
              type="date"
              value={new Date().toISOString().slice(0, 10)}
              required
            />
            <Select
              name="payment_method"
              label="Método"
              options={{
                PIX: "Pix",
                CASH: "Dinheiro",
                CARD: "Cartão",
                TRANSFER: "Transferência",
                OTHER: "Outro",
              }}
            />
            <Field name="description" label="Descrição" wide />
          </>
        )}
        {type === "trip" && (
          <>
            <Field name="name" label="Nome" value={trip.name} required />
            <Field
              name="destination"
              label="Destino"
              value={trip.destination}
              required
            />
            <Field
              name="start_date"
              label="Início"
              type="date"
              value={trip.start_date}
              required
            />
            <Field
              name="end_date"
              label="Fim"
              type="date"
              value={trip.end_date}
              required
            />
            <Select
              name="status"
              label="Status"
              value={trip.status}
              options={{
                PLANNING: "Planejamento",
                CONFIRMED: "Confirmada",
                IN_PROGRESS: "Em andamento",
                FINISHED: "Finalizada",
                CANCELLED: "Cancelada",
              }}
            />
            <Field
              name="description"
              label="Descrição"
              value={trip.description || ""}
              wide
            />
          </>
        )}
        {error && <div className="form-error field wide">{error}</div>}
        <div className="form-actions">
          <button className="secondary" type="button" onClick={onClose}>
            Cancelar
          </button>
          <button className="primary" disabled={saving}>
            {saving ? "Salvando…" : "Salvar"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function Field({
  label,
  wide,
  ...props
}: {
  label: string;
  wide?: boolean;
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className={`field ${wide ? "wide" : ""}`}>
      {label}
      <input {...props} />
    </label>
  );
}
function Select({
  label,
  options,
  ...props
}: {
  label: string;
  options: Record<string, string>;
} & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <label className="field">
      {label}
      <select {...props}>
        {Object.entries(options).map(([value, name]) => (
          <option key={value} value={value}>
            {name}
          </option>
        ))}
      </select>
    </label>
  );
}
function CheckList({
  name,
  label,
  items,
}: {
  name: string;
  label: string;
  items: { id: number; label: string }[];
}) {
  return (
    <label className="field wide">
      {label}
      <span className="check-grid">
        {items.map((item) => (
          <label className="check" key={item.id}>
            <input type="checkbox" name={name} value={item.id} />
            {item.label}
          </label>
        ))}
      </span>
    </label>
  );
}
