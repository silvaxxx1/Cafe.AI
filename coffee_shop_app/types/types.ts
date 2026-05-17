// Products Interface
export interface Product {
    id: string;
    category: string;
    description: string;
    image_url: string;
    name: string;
    price: number;
    rating: number;
  }

export interface ProductCategory {
    id: string;
    selected: boolean;
}

// ── Agent memory shapes ────────────────────────────────────────────────────────

export interface GuardMemory {
  agent: 'guard_agent';
  guard_decision: 'allowed' | 'not allowed';
}

export interface ClassificationMemory {
  agent: 'classification_agent';
  classification_decision: 'details_agent' | 'order_taking_agent' | 'recommendation_agent';
}

export interface OrderItem {
  item: string;
  quantity: number;
  price: number;
}

export interface OrderMemory {
  agent: 'order_taking_agent';
  'step number': string;
  order: OrderItem[];
  asked_recommendation_before: boolean;
}

export interface RecommendationMemory {
  agent: 'recommendation_agent';
  last_recommendations: string[];
}

export type AgentMemory =
  | GuardMemory
  | ClassificationMemory
  | OrderMemory
  | RecommendationMemory;

// ── Message Interface ──────────────────────────────────────────────────────────

export interface MessageInterface {
  role: string;
  content: string;
  memory?: AgentMemory;
}