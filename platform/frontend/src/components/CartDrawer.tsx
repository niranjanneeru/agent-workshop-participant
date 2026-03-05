import { X, ShoppingBag } from "lucide-react";
import type { CartItem } from "../types";

interface CartDrawerProps {
  open: boolean;
  onClose: () => void;
  items: CartItem[];
  onRemove: (cartItemId: number) => void;
}

const GRADIENTS = [
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
  "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
  "linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)",
  "linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)",
];

export default function CartDrawer({
  open,
  onClose,
  items,
  onRemove,
}: CartDrawerProps) {
  const total = items.reduce(
    (sum, item) => sum + item.selling_price * item.quantity,
    0,
  );

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-50 transition-opacity"
          onClick={onClose}
        />
      )}

      <div
        className={`fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 shadow-2xl transform transition-transform duration-300 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="text-lg font-bold text-gray-900">
              Shopping Cart ({items.length})
            </h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded-lg transition cursor-pointer"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-4">
            {items.length === 0 ? (
              <div className="text-center py-16">
                <ShoppingBag className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500 font-medium">Your cart is empty</p>
                <p className="text-sm text-gray-400 mt-1">
                  Add items to get started
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {items.map((item) => (
                  <div
                    key={item.cart_item_id}
                    className="flex gap-3 bg-gray-50 rounded-xl p-3"
                  >
                    <div className="w-20 h-20 rounded-lg shrink-0 overflow-hidden bg-gray-100 flex items-center justify-center">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div
                          className="w-full h-full flex items-center justify-center text-white/40 text-2xl font-bold"
                          style={{ background: GRADIENTS[item.product_id % GRADIENTS.length] }}
                        >
                          {item.name.charAt(0)}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {item.name}
                      </h4>
                      <p className="text-xs text-gray-500">
                        {item.brand_name}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="font-bold text-gray-900">
                          ₹
                          {(
                            item.selling_price * item.quantity
                          ).toLocaleString()}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">
                            Qty: {item.quantity}
                          </span>
                          <button
                            onClick={() => onRemove(item.cart_item_id)}
                            className="text-xs text-red-500 hover:text-red-700 cursor-pointer"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {items.length > 0 && (
            <div className="border-t border-gray-100 px-5 py-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total</span>
                <span className="text-xl font-bold text-gray-900">
                  ₹{total.toLocaleString()}
                </span>
              </div>
              <button className="w-full bg-violet-600 hover:bg-violet-700 text-white font-semibold py-3 rounded-xl transition cursor-pointer">
                Proceed to Checkout
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
