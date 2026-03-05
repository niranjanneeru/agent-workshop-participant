import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import type { User, CartItem } from "./types";
import Header from "./components/Header";
import HomePage from "./components/HomePage";
import ProductDetail from "./components/ProductDetail";
import CartDrawer from "./components/CartDrawer";
import OrdersView from "./components/OrdersView";
import ChatWidget from "./components/ChatWidget";

type Page = "home" | "product" | "orders";

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [selectedProductId, setSelectedProductId] = useState<number | null>(
    null,
  );
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    api.users().then((u) => {
      setUsers(u);
      if (u.length > 0) setCurrentUser(u[0]);
    });
  }, []);

  const refreshCart = useCallback(() => {
    if (currentUser) {
      api.cart.get(currentUser.user_id).then(setCartItems);
    }
  }, [currentUser]);

  useEffect(() => {
    refreshCart();
  }, [refreshCart]);

  const handleProductClick = (id: number) => {
    setSelectedProductId(id);
    setPage("product");
    window.scrollTo(0, 0);
  };

  const handleAddToCart = async (productId: number) => {
    if (!currentUser) return;
    await api.cart.add(currentUser.user_id, productId);
    refreshCart();
  };

  const handleRemoveFromCart = async (cartItemId: number) => {
    if (!currentUser) return;
    await api.cart.remove(currentUser.user_id, cartItemId);
    refreshCart();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        users={users}
        currentUser={currentUser}
        onUserChange={(u) => {
          setCurrentUser(u);
          setPage("home");
        }}
        cartCount={cartItems.reduce((s, i) => s + i.quantity, 0)}
        onCartClick={() => setCartOpen(true)}
        onOrdersClick={() => setPage("orders")}
        onHomeClick={() => {
          setPage("home");
          setSearchQuery("");
        }}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onSearch={() => setPage("home")}
      />

      <main className="pt-16">
        {page === "home" && (
          <HomePage
            searchQuery={searchQuery}
            onProductClick={handleProductClick}
            onAddToCart={handleAddToCart}
          />
        )}
        {page === "product" && selectedProductId && (
          <ProductDetail
            productId={selectedProductId}
            onBack={() => setPage("home")}
            onAddToCart={handleAddToCart}
          />
        )}
        {page === "orders" && currentUser && (
          <OrdersView
            userId={currentUser.user_id}
            onBack={() => setPage("home")}
          />
        )}
      </main>

      <CartDrawer
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        items={cartItems}
        onRemove={handleRemoveFromCart}
      />

      <ChatWidget userId={currentUser?.user_id ?? null} />
    </div>
  );
}
