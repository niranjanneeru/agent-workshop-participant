import { useState, useEffect } from "react";
import { Star, ShoppingCart, Truck, Shield } from "lucide-react";
import { api } from "../api";
import type { Product, Category } from "../types";

interface HomePageProps {
  searchQuery: string;
  onProductClick: (id: number) => void;
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
  "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)",
  "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
];

export default function HomePage({
  searchQuery,
  onProductClick,
  onAddToCart,
}: HomePageProps) {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    api.products
      .list({
        search: searchQuery || undefined,
        category_id: selectedCategory ?? undefined,
        limit: 40,
      })
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [searchQuery, selectedCategory]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {!searchQuery && !selectedCategory && (
        <div className="mb-8 rounded-2xl bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700 p-8 md:p-12 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
          <div className="relative">
            <h1 className="text-3xl md:text-4xl font-extrabold mb-3">
              Welcome to KV Kart
            </h1>
            <p className="text-white/80 text-lg mb-5 max-w-lg">
              Discover amazing products at great prices. Shop from thousands of
              brands with fast delivery.
            </p>
            <div className="flex flex-wrap items-center gap-5 text-sm text-white/70">
              <div className="flex items-center gap-1.5">
                <Truck className="w-4 h-4" />
                <span>Free delivery over ₹499</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Shield className="w-4 h-4" />
                <span>Secure payments</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition cursor-pointer ${
            selectedCategory === null
              ? "bg-violet-600 text-white shadow-md"
              : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
          }`}
        >
          All
        </button>
        {categories.map((cat) => (
          <button
            key={cat.category_id}
            onClick={() =>
              setSelectedCategory(
                cat.category_id === selectedCategory ? null : cat.category_id,
              )
            }
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition cursor-pointer ${
              selectedCategory === cat.category_id
                ? "bg-violet-600 text-white shadow-md"
                : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {(searchQuery || selectedCategory) && (
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">
            {searchQuery
              ? `Results for "${searchQuery}"`
              : categories.find((c) => c.category_id === selectedCategory)
                  ?.name}
          </h2>
          <span className="text-sm text-gray-500">
            {products.length} products
          </span>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl overflow-hidden animate-pulse"
            >
              <div className="aspect-square bg-gray-200" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
                <div className="h-4 bg-gray-200 rounded w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg">No products found</p>
          <p className="text-sm mt-1">Try a different search or category</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map((product) => (
            <ProductCard
              key={product.product_id}
              product={product}
              onClick={() => onProductClick(product.product_id)}
              onAddToCart={() => onAddToCart(product.product_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ProductCard({
  product,
  onClick,
  onAddToCart,
}: {
  product: Product;
  onClick: () => void;
  onAddToCart: () => void;
}) {
  const gradient = GRADIENTS[product.product_id % GRADIENTS.length];
  const hasDiscount = product.discount_percent > 0;

  return (
    <div className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition group border border-gray-100">
      <div
        className="aspect-square relative cursor-pointer bg-gray-100"
        style={product.image_url ? undefined : { background: gradient }}
        onClick={onClick}
      >
        {product.image_url ? (
          <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center" style={{ background: gradient }}>
            <span className="text-white/30 text-6xl font-bold select-none">
              {product.name.charAt(0)}
            </span>
          </div>
        )}
        {hasDiscount && (
          <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-md">
            {Math.round(product.discount_percent)}% OFF
          </span>
        )}
        {product.stock_quantity === 0 && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <span className="text-white font-semibold text-sm">
              Out of Stock
            </span>
          </div>
        )}
      </div>
      <div className="p-3">
        <p className="text-xs text-gray-500 mb-0.5">{product.brand_name}</p>
        <h3
          className="text-sm font-medium text-gray-900 line-clamp-2 mb-2 hover:text-violet-700 cursor-pointer"
          onClick={onClick}
        >
          {product.name}
        </h3>
        <div className="flex items-center gap-1 mb-2">
          <div className="flex items-center gap-0.5 bg-green-600 text-white text-xs px-1.5 py-0.5 rounded">
            <span>{product.average_rating?.toFixed(1) || "0.0"}</span>
            <Star className="w-3 h-3 fill-current" />
          </div>
          <span className="text-xs text-gray-500">
            ({product.total_ratings})
          </span>
        </div>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-base font-bold text-gray-900">
            ₹{product.selling_price?.toLocaleString()}
          </span>
          {hasDiscount && (
            <span className="text-xs text-gray-400 line-through">
              ₹{product.base_price?.toLocaleString()}
            </span>
          )}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAddToCart();
          }}
          disabled={product.stock_quantity === 0}
          className="w-full flex items-center justify-center gap-1.5 bg-violet-600 hover:bg-violet-700 disabled:bg-gray-300 text-white text-sm font-medium py-2 rounded-lg transition cursor-pointer disabled:cursor-not-allowed"
        >
          <ShoppingCart className="w-4 h-4" />
          Add to Cart
        </button>
      </div>
    </div>
  );
}
