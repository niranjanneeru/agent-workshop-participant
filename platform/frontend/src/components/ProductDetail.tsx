import { useState, useEffect } from "react";
import {
  ArrowLeft,
  Star,
  ShoppingCart,
  Package,
  Shield,
  Truck,
} from "lucide-react";
import { api } from "../api";
import type { Product, Review } from "../types";

interface ProductDetailProps {
  productId: number;
  onBack: () => void;
  onAddToCart: (productId: number) => void;
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

export default function ProductDetail({
  productId,
  onBack,
  onAddToCart,
}: ProductDetailProps) {
  const [product, setProduct] = useState<Product | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    api.products.get(productId).then(setProduct);
    api.products.reviews(productId).then(setReviews).catch(() => {});
  }, [productId]);

  if (!product) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-32" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="aspect-square bg-gray-200 rounded-2xl" />
            <div className="space-y-4">
              <div className="h-6 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-8 bg-gray-200 rounded w-1/3" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const gradient = GRADIENTS[product.product_id % GRADIENTS.length];
  const hasDiscount = product.discount_percent > 0;

  const handleAdd = () => {
    onAddToCart(product.product_id);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <button
        onClick={onBack}
        className="flex items-center gap-1 text-gray-600 hover:text-gray-900 mb-6 text-sm cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to products
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div
          className="aspect-square rounded-2xl overflow-hidden relative bg-gray-100"
          style={product.image_url ? undefined : { background: gradient }}
        >
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center" style={{ background: gradient }}>
              <span className="text-white/20 text-[120px] font-bold select-none">
                {product.name.charAt(0)}
              </span>
            </div>
          )}
          {hasDiscount && (
            <span className="absolute top-4 left-4 bg-red-500 text-white text-sm font-bold px-3 py-1.5 rounded-lg">
              {Math.round(product.discount_percent)}% OFF
            </span>
          )}
        </div>

        <div>
          <p className="text-sm text-violet-600 font-medium mb-1">
            {product.brand_name}
          </p>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {product.name}
          </h1>
          <p className="text-sm text-gray-500 mb-3">{product.category_name}</p>

          <div className="flex items-center gap-2 mb-4">
            <div className="flex items-center gap-1 bg-green-600 text-white text-sm px-2 py-1 rounded-md">
              <span className="font-medium">
                {product.average_rating?.toFixed(1)}
              </span>
              <Star className="w-3.5 h-3.5 fill-current" />
            </div>
            <span className="text-sm text-gray-500">
              {product.total_ratings} ratings
            </span>
          </div>

          <div className="flex items-baseline gap-3 mb-2">
            <span className="text-3xl font-bold text-gray-900">
              ₹{product.selling_price?.toLocaleString()}
            </span>
            {hasDiscount && (
              <>
                <span className="text-lg text-gray-400 line-through">
                  ₹{product.base_price?.toLocaleString()}
                </span>
                <span className="text-green-600 font-medium text-sm">
                  Save ₹
                  {(product.base_price - product.selling_price).toLocaleString()}
                </span>
              </>
            )}
          </div>
          <p className="text-xs text-gray-500 mb-6">Inclusive of all taxes</p>

          <div className="mb-6">
            {product.stock_quantity > 0 ? (
              <span className="text-green-600 font-medium text-sm">
                {product.stock_quantity > 10
                  ? "In Stock"
                  : `Only ${product.stock_quantity} left!`}
              </span>
            ) : (
              <span className="text-red-500 font-medium text-sm">
                Out of Stock
              </span>
            )}
          </div>

          <button
            onClick={handleAdd}
            disabled={product.stock_quantity === 0}
            className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-300 text-white font-semibold py-3 rounded-xl transition text-base mb-6 cursor-pointer disabled:cursor-not-allowed"
          >
            <ShoppingCart className="w-5 h-5" />
            {added ? "Added to Cart!" : "Add to Cart"}
          </button>

          <div className="grid grid-cols-3 gap-3 mb-6">
            {[
              { icon: Truck, label: "Free Delivery" },
              { icon: Shield, label: "Warranty" },
              { icon: Package, label: "Easy Returns" },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="text-center p-3 bg-gray-50 rounded-xl">
                <Icon className="w-5 h-5 mx-auto text-gray-600 mb-1" />
                <span className="text-xs text-gray-600">{label}</span>
              </div>
            ))}
          </div>

          {product.description && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                {product.description}
              </p>
            </div>
          )}
        </div>
      </div>

      {reviews.length > 0 && (
        <div className="mt-10">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Customer Reviews
          </h3>
          <div className="space-y-4">
            {reviews.map((review) => (
              <div
                key={review.review_id}
                className="bg-white rounded-xl p-4 border border-gray-100"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex items-center gap-0.5 bg-green-600 text-white text-xs px-1.5 py-0.5 rounded">
                    <span>{review.rating}</span>
                    <Star className="w-3 h-3 fill-current" />
                  </div>
                  {review.title && (
                    <span className="font-medium text-sm text-gray-900">
                      {review.title}
                    </span>
                  )}
                </div>
                {review.body && (
                  <p className="text-sm text-gray-600 mb-2">{review.body}</p>
                )}
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span>
                    {review.first_name} {review.last_name}
                  </span>
                  {review.is_verified_purchase ? (
                    <span className="text-green-600">Verified Purchase</span>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
