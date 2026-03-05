import {
  ShoppingCart,
  Package,
  Search,
  ChevronDown,
  Store,
} from "lucide-react";
import type { User } from "../types";

interface HeaderProps {
  users: User[];
  currentUser: User | null;
  onUserChange: (user: User) => void;
  cartCount: number;
  onCartClick: () => void;
  onOrdersClick: () => void;
  onHomeClick: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSearch: () => void;
}

export default function Header({
  users,
  currentUser,
  onUserChange,
  cartCount,
  onCartClick,
  onOrdersClick,
  onHomeClick,
  searchQuery,
  onSearchChange,
  onSearch,
}: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-gradient-to-r from-violet-600 to-purple-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center gap-4">
        <button
          onClick={onHomeClick}
          className="flex items-center gap-2 text-white font-bold text-xl shrink-0 cursor-pointer"
        >
          <Store className="w-7 h-7" />
          <span className="hidden sm:inline">KV Kart</span>
        </button>

        <form
          className="flex-1 max-w-xl relative"
          onSubmit={(e) => {
            e.preventDefault();
            onSearch();
          }}
        >
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search products, brands, categories..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-white/90 text-gray-900 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-white/50"
          />
        </form>

        <div className="relative shrink-0">
          <select
            value={currentUser?.user_id ?? ""}
            onChange={(e) => {
              const user = users.find(
                (u) => u.user_id === Number(e.target.value),
              );
              if (user) onUserChange(user);
            }}
            className="appearance-none bg-white/20 text-white text-sm pl-3 pr-8 py-2 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-white/50"
          >
            {users.map((u) => (
              <option
                key={u.user_id}
                value={u.user_id}
                className="text-gray-900"
              >
                {u.first_name} {u.last_name}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-white/70 pointer-events-none" />
        </div>

        <button
          onClick={onOrdersClick}
          className="text-white/90 hover:text-white p-2 rounded-lg hover:bg-white/10 transition shrink-0 cursor-pointer"
          title="My Orders"
        >
          <Package className="w-5 h-5" />
        </button>

        <button
          onClick={onCartClick}
          className="relative text-white/90 hover:text-white p-2 rounded-lg hover:bg-white/10 transition shrink-0 cursor-pointer"
          title="Cart"
        >
          <ShoppingCart className="w-5 h-5" />
          {cartCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-amber-400 text-gray-900 text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
              {cartCount > 9 ? "9+" : cartCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
