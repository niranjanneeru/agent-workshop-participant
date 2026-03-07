# ── Orders ───────────────────────────────────────────────────────────────
from src.tools.orders import (
    get_order_by_order_number,
    get_order_by_id,
    get_orders_by_user,
    get_order_items,
    get_order_details_full,
    get_bulk_orders_by_ids,
    cancel_order,
    update_order_status,
)

# ── Products ─────────────────────────────────────────────────────────────
from src.tools.products import (
    get_product_by_id,
    search_products,
    get_products_by_category,
    get_products_by_brand,
    get_product_reviews,
    get_all_categories,
    get_all_brands,
    get_bulk_products_by_ids,
    check_product_availability,
)

# ── Logistics ────────────────────────────────────────────────────────────
from src.tools.logistics import (
    get_shipment_by_order,
    get_tracking_events,
    get_full_tracking_by_order,
    get_delivery_estimate,
    get_logistics_partners,
    get_bulk_shipments_by_orders,
    update_shipment_status,
)

# ── Payments ─────────────────────────────────────────────────────────────
from src.tools.payments import (
    get_payment_by_order,
    get_payments_by_user,
    get_bulk_payments_by_orders,
)

# ── Returns & Refunds ────────────────────────────────────────────────────
from src.tools.returns import (
    get_return_requests_by_order,
    get_return_requests_by_user,
    get_refund_by_order,
    get_refund_by_user,
    get_refund_status,
    create_return_request,
    update_return_status,
)

# ── Users ────────────────────────────────────────────────────────────────
from src.tools.users import (
    get_user_profile,
    get_user_by_email,
    get_user_addresses,
)

# ── Cart & Wishlist ──────────────────────────────────────────────────────
from src.tools.cart import (
    get_cart_items,
    get_wishlist,
    add_to_cart,
    update_cart_quantity,
    remove_from_cart,
    add_to_wishlist,
    remove_from_wishlist,
)

# ── Support Tickets ──────────────────────────────────────────────────────
from src.tools.support import (
    get_tickets_by_user,
    get_ticket_details,
    create_support_ticket,
    update_ticket_status,
)

# ── Coupons ──────────────────────────────────────────────────────────────
from src.tools.coupons import (
    validate_coupon,
    get_available_coupons,
)

# ── Wallet ───────────────────────────────────────────────────────────────
from src.tools.wallet import (
    get_wallet_balance,
    get_wallet_transactions,
)

# ── Notifications ────────────────────────────────────────────────────────
from src.tools.notifications import (
    get_user_notifications,
    mark_notification_read,
)

all_tools = [
    # Orders
    get_order_by_order_number, get_order_by_id, get_orders_by_user,
    get_order_items, get_order_details_full, get_bulk_orders_by_ids,
    cancel_order, update_order_status,
    # Products
    get_product_by_id, search_products, get_products_by_category,
    get_products_by_brand, get_product_reviews, get_all_categories,
    get_all_brands, get_bulk_products_by_ids, check_product_availability,
    # Logistics
    get_shipment_by_order, get_tracking_events, get_full_tracking_by_order,
    get_delivery_estimate, get_logistics_partners, get_bulk_shipments_by_orders,
    update_shipment_status,
    # Payments
    get_payment_by_order, get_payments_by_user, get_bulk_payments_by_orders,
    # Returns & Refunds
    get_return_requests_by_order, get_return_requests_by_user,
    get_refund_by_order, get_refund_by_user, get_refund_status,
    create_return_request, update_return_status,
    # Users
    get_user_profile, get_user_by_email, get_user_addresses,
    # Cart & Wishlist
    get_cart_items, get_wishlist, add_to_cart, update_cart_quantity,
    remove_from_cart, add_to_wishlist, remove_from_wishlist,
    # Support
    get_tickets_by_user, get_ticket_details, create_support_ticket,
    update_ticket_status,
    # Coupons
    validate_coupon, get_available_coupons,
    # Wallet
    get_wallet_balance, get_wallet_transactions,
    # Notifications
    get_user_notifications, mark_notification_read,
]

from src.tools.rag import create_rag_tools
