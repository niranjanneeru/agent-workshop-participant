import { useState, useEffect } from "react";
import {
  ArrowLeft,
  Package,
  Clock,
  CheckCircle,
  Truck,
  XCircle,
  RotateCcw,
} from "lucide-react";
import { api } from "../api";
import type { Order } from "../types";

interface OrdersViewProps {
  userId: number;
  onBack: () => void;
}

type IconComponent = React.ComponentType<{ className?: string }>;

const STATUS_CONFIG: Record<
  string,
  { color: string; icon: IconComponent; label: string }
> = {
  pending: {
    color: "bg-yellow-100 text-yellow-700",
    icon: Clock,
    label: "Pending",
  },
  confirmed: {
    color: "bg-blue-100 text-blue-700",
    icon: CheckCircle,
    label: "Confirmed",
  },
  processing: {
    color: "bg-blue-100 text-blue-700",
    icon: Package,
    label: "Processing",
  },
  shipped: {
    color: "bg-purple-100 text-purple-700",
    icon: Truck,
    label: "Shipped",
  },
  out_for_delivery: {
    color: "bg-indigo-100 text-indigo-700",
    icon: Truck,
    label: "Out for Delivery",
  },
  delivered: {
    color: "bg-green-100 text-green-700",
    icon: CheckCircle,
    label: "Delivered",
  },
  cancelled: {
    color: "bg-red-100 text-red-700",
    icon: XCircle,
    label: "Cancelled",
  },
  return_requested: {
    color: "bg-orange-100 text-orange-700",
    icon: RotateCcw,
    label: "Return Requested",
  },
  returned: {
    color: "bg-gray-100 text-gray-700",
    icon: RotateCcw,
    label: "Returned",
  },
};

export default function OrdersView({ userId, onBack }: OrdersViewProps) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .orders(userId)
      .then(setOrders)
      .catch(() => setOrders([]))
      .finally(() => setLoading(false));
  }, [userId]);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-gray-600 hover:text-gray-900 mb-6 text-sm cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to products
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Orders</h1>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl p-4 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
              <div className="h-4 bg-gray-200 rounded w-1/4" />
            </div>
          ))}
        </div>
      ) : orders.length === 0 ? (
        <div className="text-center py-16">
          <Package className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 font-medium">No orders yet</p>
          <p className="text-sm text-gray-400 mt-1">
            Start shopping to see your orders here
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => {
            const config =
              STATUS_CONFIG[order.order_status] || STATUS_CONFIG.pending;
            const Icon = config.icon;
            return (
              <div
                key={order.order_id}
                className="bg-white rounded-xl border border-gray-100 overflow-hidden"
              >
                <div className="px-4 py-3 border-b border-gray-50 flex items-center justify-between">
                  <div>
                    <span className="font-mono text-sm font-medium text-gray-900">
                      {order.order_number}
                    </span>
                    <span className="text-xs text-gray-400 ml-3">
                      {new Date(order.placed_at).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}
                  >
                    <Icon className="w-3 h-3" />
                    {config.label}
                  </span>
                </div>
                <div className="px-4 py-3">
                  {order.items.map((item) => (
                    <div
                      key={item.order_item_id}
                      className="flex items-center justify-between py-1.5"
                    >
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-gray-700">
                          {item.name}
                        </span>
                        <span className="text-xs text-gray-400 ml-2">
                          x{item.quantity}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        ₹{item.total_price?.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
