export interface Car {
  source: string;
  make: string;
  model: string;
  year: number;
  price: number;
  mileage: number;
  condition: string;
  vin: string;
  location: string;
  trim: string;
  drive_type: string;
  color: string;
  url: string;
  safety_rating?: string;
  recalls?: string[];
  fuel_economy?: string;
  deal_score?: number;
}

export interface TradeInEstimate {
  trade_in_value: number | null;
  reasoning: string;
  financing_impact: string;
  confidence: "high" | "medium" | "low" | "none";
}

export interface Message {
  id: string;
  role: "user" | "agent";
  content: string;
  cars?: Car[];
  estimate?: TradeInEstimate;
}
