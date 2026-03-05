import type {
  Product,
  Category,
  Brand,
  CartItem,
  Order,
  Review,
  User,
  ChatEvent,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  products: {
    list: (params?: {
      search?: string;
      category_id?: number;
      brand_id?: number;
      limit?: number;
      offset?: number;
    }) => {
      const qs = new URLSearchParams();
      if (params?.search) qs.set("search", params.search);
      if (params?.category_id)
        qs.set("category_id", String(params.category_id));
      if (params?.brand_id) qs.set("brand_id", String(params.brand_id));
      if (params?.limit) qs.set("limit", String(params.limit));
      if (params?.offset) qs.set("offset", String(params.offset));
      const q = qs.toString();
      return get<Product[]>(`/products${q ? `?${q}` : ""}`);
    },
    get: (id: number) => get<Product>(`/products/${id}`),
    reviews: (id: number) => get<Review[]>(`/products/${id}/reviews`),
  },

  categories: () => get<Category[]>("/categories"),
  brands: () => get<Brand[]>("/brands"),
  users: () => get<User[]>("/users"),

  cart: {
    get: (userId: number) => get<CartItem[]>(`/cart/${userId}`),
    add: (userId: number, productId: number, quantity = 1) =>
      post<{ status: string }>(`/cart/${userId}`, {
        product_id: productId,
        quantity,
      }),
    remove: (userId: number, cartItemId: number) =>
      del<{ status: string }>(`/cart/${userId}/${cartItemId}`),
  },

  orders: (userId: number) => get<Order[]>(`/orders/${userId}`),

  chat: async function* (
    message: string,
    history: { role: string; content: string }[],
    userId: number,
  ): AsyncGenerator<ChatEvent> {
    const res = await fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history, user_id: userId }),
    });
    if (!res.ok) throw new Error(`Chat error: ${res.status}`);

    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const event of events) {
        const line = event.split("\n").find((l) => l.startsWith("data: "));
        if (line) {
          try {
            yield JSON.parse(line.slice(6)) as ChatEvent;
          } catch {
            /* skip malformed */
          }
        }
      }
    }
    const line = buffer.split("\n").find((l) => l.startsWith("data: "));
    if (line) {
      try {
        yield JSON.parse(line.slice(6)) as ChatEvent;
      } catch {
        /* skip */
      }
    }
  },
};
