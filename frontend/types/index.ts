export type Trip = {
  id: number;
  name: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: string;
  description?: string;
};
export type Participant = {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  participant_type: string;
  status: string;
  groups: string[];
  total_due: number;
  total_paid: number;
  balance: number;
  has_account: boolean;
};
export type Membership = {
  role: "ADMIN" | "ORGANIZER" | "PARTICIPANT";
  participant_id: number | null;
  can_manage: boolean;
};
export type Accommodation = {
  id: number;
  name: string;
  city: string;
  address?: string;
  capacity: number;
  occupancy: number;
  bedrooms: number;
  bathrooms: number;
  total_price: number;
  cleaning_fee: number;
  other_fees: number;
  distance_to_beach?: string;
  status: string;
  participant_ids: number[];
};
export type Scenario = {
  id: number;
  name: string;
  description?: string;
  status: string;
  accommodation_ids: number[];
  accommodations: string[];
  capacity: number;
  bedrooms: number;
  bathrooms: number;
  total_cost: number;
  confirmed_participants: number;
  cost_per_person: number;
  votes: { YES: number; MAYBE: number; NO: number };
};
export type Expense = {
  id: number;
  description: string;
  category: string;
  amount: number;
  expense_date: string;
  allocation_type: string;
  status: string;
  allocations: { participant_id: number; amount: number }[];
};
export type Payment = {
  id: number;
  participant_id: number;
  amount: number;
  payment_date: string;
  payment_method: string;
  description?: string;
  status: string;
};
export type Dashboard = {
  participants: {
    total: number;
    confirmed: number;
    statuses: Record<string, number>;
  };
  accommodation_status: string;
  budget: { estimated: number; actual: number };
  payments: { received: number; pending: number };
  expenses_by_category: Record<string, number>;
  scenarios: number;
};
