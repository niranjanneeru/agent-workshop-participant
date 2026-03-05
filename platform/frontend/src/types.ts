export interface Product {
  product_id: number;
  name: string;
  description: string;
  selling_price: number;
  base_price: number;
  discount_percent: number;
  stock_quantity: number;
  average_rating: number;
  total_ratings: number;
  brand_name: string;
  category_name: string;
  category_id: number;
  brand_id: number;
  tags: string;
  image_url?: string | null;
}

export interface Category {
  category_id: number;
  name: string;
  description: string;
  parent_category_id: number | null;
}

export interface Brand {
  brand_id: number;
  name: string;
  logo_url: string;
}

export interface CartItem {
  cart_item_id: number;
  product_id: number;
  quantity: number;
  name: string;
  selling_price: number;
  base_price: number;
  discount_percent: number;
  brand_name: string;
  stock_quantity: number;
  image_url?: string | null;
}

export interface Order {
  order_id: number;
  order_number: string;
  order_status: string;
  placed_at: string;
  confirmed_at: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
  items: OrderItem[];
}

export interface OrderItem {
  order_item_id: number;
  product_id: number;
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  item_status: string;
}

export interface Review {
  review_id: number;
  rating: number;
  title: string;
  body: string;
  first_name: string;
  last_name: string;
  created_at: string;
  is_verified_purchase: boolean | number;
  helpful_count: number;
}

export interface User {
  user_id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatEvent {
  type: "token" | "tool_call" | "status" | "done" | "error";
  content?: string;
  name?: string;
  intent?: string;
}
