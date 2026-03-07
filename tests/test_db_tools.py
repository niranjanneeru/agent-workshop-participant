import sys
import traceback

import pytest

from src.tools import (
    add_to_cart,
    add_to_wishlist,
    cancel_order,
    check_product_availability,
    create_return_request,
    create_support_ticket,
    get_all_brands,
    get_all_categories,
    get_available_coupons,
    get_bulk_orders_by_ids,
    get_bulk_payments_by_orders,
    get_bulk_products_by_ids,
    get_bulk_shipments_by_orders,
    get_cart_items,
    get_delivery_estimate,
    get_full_tracking_by_order,
    get_logistics_partners,
    get_order_by_id,
    get_order_by_order_number,
    get_order_details_full,
    get_order_items,
    get_orders_by_user,
    get_payment_by_order,
    get_payments_by_user,
    get_product_by_id,
    get_product_reviews,
    get_products_by_brand,
    get_products_by_category,
    get_refund_by_order,
    get_refund_by_user,
    get_refund_status,
    get_return_requests_by_order,
    get_return_requests_by_user,
    get_shipment_by_order,
    get_ticket_details,
    get_tickets_by_user,
    get_tracking_events,
    get_user_addresses,
    get_user_by_email,
    get_user_notifications,
    get_user_profile,
    get_wallet_balance,
    get_wallet_transactions,
    get_wishlist,
    mark_notification_read,
    remove_from_cart,
    remove_from_wishlist,
    search_products,
    update_cart_quantity,
    update_order_status,
    update_return_status,
    update_shipment_status,
    update_ticket_status,
    validate_coupon,
)

# ─── Test all tools by invoking them against the real MySQL database ─────────
# Each tool is called with valid data from the DB. Write tools are tested with
# business-logic guard-rails that should safely reject or succeed without harm.


passed = 0
failed = 0
results = []


def run_test(name: str, fn, *args, **kwargs):
    """Run a single tool test and track results."""
    global passed, failed
    try:
        result = fn.invoke(*args, **kwargs)
        passed += 1
        results.append(("PASS", name, result))
        print(f"  ✅ {name}")
        return result
    except Exception as e:
        failed += 1
        results.append(("FAIL", name, str(e)))
        print(f"  ❌ {name}: {e}")
        traceback.print_exc()
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ORDERS - READ
# ═══════════════════════════════════════════════════════════════════════════════
def _main():
    global passed, failed, results
    section_failures = []
    section_before = failed

    print("\n📦 ORDERS - READ")
    print("-" * 60)

    run_test(
        "get_order_by_order_number",
        get_order_by_order_number,
        {"order_number": "KV-20250115-0001"},
    )

    run_test(
        "get_order_by_order_number (not found)",
        get_order_by_order_number,
        {"order_number": "NONEXISTENT-999"},
    )

    run_test(
        "get_order_by_id",
        get_order_by_id,
        {"order_id": 1},
    )

    run_test(
        "get_order_by_id (not found)",
        get_order_by_id,
        {"order_id": 999999},
    )

    run_test(
        "get_orders_by_user",
        get_orders_by_user,
        {"user_id": 1},
    )

    run_test(
        "get_orders_by_user (with status filter)",
        get_orders_by_user,
        {"user_id": 1, "status_filter": "delivered"},
    )

    run_test(
        "get_orders_by_user (invalid status)",
        get_orders_by_user,
        {"user_id": 1, "status_filter": "invalid_status"},
    )

    run_test(
        "get_order_items",
        get_order_items,
        {"order_id": 1},
    )

    run_test(
        "get_order_items (no items)",
        get_order_items,
        {"order_id": 999999},
    )

    run_test(
        "get_order_details_full",
        get_order_details_full,
        {"order_number": "KV-20250115-0001"},
    )

    run_test(
        "get_order_details_full (not found)",
        get_order_details_full,
        {"order_number": "NONEXISTENT-999"},
    )

    run_test(
        "get_bulk_orders_by_ids",
        get_bulk_orders_by_ids,
        {"order_ids": [1, 2, 3]},
    )

    run_test(
        "get_bulk_orders_by_ids (empty list)",
        get_bulk_orders_by_ids,
        {"order_ids": []},
    )

    run_test(
        "get_bulk_orders_by_ids (too many)",
        get_bulk_orders_by_ids,
        {"order_ids": list(range(1, 25))},
    )

    section_failures.append(("orders_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # ORDERS - WRITE (testing business-logic rejections on delivered orders)
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n📦 ORDERS - WRITE")
    print("-" * 60)

    # order_id=1 is 'delivered', so cancel should be rejected by business logic
    run_test(
        "cancel_order (rejected - delivered order)",
        cancel_order,
        {"order_id": 1, "reason": "Testing cancellation on delivered order"},
    )

    run_test(
        "cancel_order (not found)",
        cancel_order,
        {"order_id": 999999, "reason": "Test reason"},
    )

    run_test(
        "cancel_order (short reason)",
        cancel_order,
        {"order_id": 1, "reason": "hi"},
    )

    # order_id=1 is 'delivered', only valid transition is 'return_requested'
    run_test(
        "update_order_status (invalid transition)",
        update_order_status,
        {"order_id": 1, "new_status": "shipped"},
    )

    run_test(
        "update_order_status (not found)",
        update_order_status,
        {"order_id": 999999, "new_status": "confirmed"},
    )

    section_failures.append(("orders_write", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # PRODUCTS - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🛍️  PRODUCTS - READ")
    print("-" * 60)

    run_test(
        "get_product_by_id",
        get_product_by_id,
        {"product_id": 1},
    )

    run_test(
        "get_product_by_id (not found)",
        get_product_by_id,
        {"product_id": 999999},
    )

    run_test(
        "search_products (keyword)",
        search_products,
        {"query": "KVTech"},
    )

    run_test(
        "search_products (with category filter)",
        search_products,
        {"query": "phone", "category_id": 6},
    )

    run_test(
        "search_products (with price range)",
        search_products,
        {"query": "KVTech", "min_price": 100.0, "max_price": 50000.0},
    )

    run_test(
        "search_products (no results)",
        search_products,
        {"query": "xyznonexistentproduct12345"},
    )

    run_test(
        "get_products_by_category",
        get_products_by_category,
        {"category_id": 6},
    )

    run_test(
        "get_products_by_category (no products)",
        get_products_by_category,
        {"category_id": 999999},
    )

    run_test(
        "get_products_by_brand",
        get_products_by_brand,
        {"brand_id": 1},
    )

    run_test(
        "get_products_by_brand (no products)",
        get_products_by_brand,
        {"brand_id": 999999},
    )

    run_test(
        "get_product_reviews",
        get_product_reviews,
        {"product_id": 1},
    )

    run_test(
        "get_all_categories",
        get_all_categories,
        {},
    )

    run_test(
        "get_all_brands",
        get_all_brands,
        {},
    )

    run_test(
        "get_bulk_products_by_ids",
        get_bulk_products_by_ids,
        {"product_ids": [1, 2, 3]},
    )

    run_test(
        "get_bulk_products_by_ids (empty)",
        get_bulk_products_by_ids,
        {"product_ids": []},
    )

    run_test(
        "get_bulk_products_by_ids (too many)",
        get_bulk_products_by_ids,
        {"product_ids": list(range(1, 35))},
    )

    run_test(
        "check_product_availability (in stock)",
        check_product_availability,
        {"product_id": 1},
    )

    run_test(
        "check_product_availability (not found)",
        check_product_availability,
        {"product_id": 999999},
    )

    section_failures.append(("products_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # LOGISTICS - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🚚 LOGISTICS - READ")
    print("-" * 60)

    run_test(
        "get_shipment_by_order",
        get_shipment_by_order,
        {"order_id": 1},
    )

    run_test(
        "get_shipment_by_order (no shipment)",
        get_shipment_by_order,
        {"order_id": 999999},
    )

    run_test(
        "get_tracking_events",
        get_tracking_events,
        {"shipment_id": 3},
    )

    run_test(
        "get_tracking_events (no events)",
        get_tracking_events,
        {"shipment_id": 999999},
    )

    run_test(
        "get_full_tracking_by_order",
        get_full_tracking_by_order,
        {"order_id": 3},
    )

    run_test(
        "get_full_tracking_by_order (no shipment)",
        get_full_tracking_by_order,
        {"order_id": 999999},
    )

    run_test(
        "get_delivery_estimate",
        get_delivery_estimate,
        {"origin_pincode": "682042", "destination_pincode": "682036"},
    )

    run_test(
        "get_delivery_estimate (no route)",
        get_delivery_estimate,
        {"origin_pincode": "000000", "destination_pincode": "999999"},
    )

    run_test(
        "get_logistics_partners",
        get_logistics_partners,
        {},
    )

    run_test(
        "get_bulk_shipments_by_orders",
        get_bulk_shipments_by_orders,
        {"order_ids": [1, 2, 3]},
    )

    run_test(
        "get_bulk_shipments_by_orders (empty)",
        get_bulk_shipments_by_orders,
        {"order_ids": []},
    )

    run_test(
        "get_bulk_shipments_by_orders (too many)",
        get_bulk_shipments_by_orders,
        {"order_ids": list(range(1, 25))},
    )

    section_failures.append(("logistics_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # LOGISTICS - WRITE (testing rejection on terminal-state shipment)
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🚚 LOGISTICS - WRITE")
    print("-" * 60)

    # shipment_id=1 is 'delivered' (terminal), so this should be rejected
    run_test(
        "update_shipment_status (rejected - terminal state)",
        update_shipment_status,
        {"shipment_id": 1, "new_status": "in_transit"},
    )

    run_test(
        "update_shipment_status (not found)",
        update_shipment_status,
        {"shipment_id": 999999, "new_status": "picked_up"},
    )

    section_failures.append(("logistics_write", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # PAYMENTS - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n💳 PAYMENTS - READ")
    print("-" * 60)

    run_test(
        "get_payment_by_order",
        get_payment_by_order,
        {"order_id": 1},
    )

    run_test(
        "get_payment_by_order (no payment)",
        get_payment_by_order,
        {"order_id": 999999},
    )

    run_test(
        "get_payments_by_user",
        get_payments_by_user,
        {"user_id": 1},
    )

    run_test(
        "get_payments_by_user (no payments)",
        get_payments_by_user,
        {"user_id": 999999},
    )

    run_test(
        "get_bulk_payments_by_orders",
        get_bulk_payments_by_orders,
        {"order_ids": [1, 2, 3]},
    )

    run_test(
        "get_bulk_payments_by_orders (empty)",
        get_bulk_payments_by_orders,
        {"order_ids": []},
    )

    run_test(
        "get_bulk_payments_by_orders (too many)",
        get_bulk_payments_by_orders,
        {"order_ids": list(range(1, 25))},
    )

    section_failures.append(("payments_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # RETURNS - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🔄 RETURNS - READ")
    print("-" * 60)

    run_test(
        "get_return_requests_by_order",
        get_return_requests_by_order,
        {"order_id": 22},
    )

    run_test(
        "get_return_requests_by_order (none found)",
        get_return_requests_by_order,
        {"order_id": 999999},
    )

    run_test(
        "get_return_requests_by_user",
        get_return_requests_by_user,
        {"user_id": 6},
    )

    run_test(
        "get_return_requests_by_user (none found)",
        get_return_requests_by_user,
        {"user_id": 999999},
    )

    run_test(
        "get_refund_by_order",
        get_refund_by_order,
        {"order_id": 12},
    )

    run_test(
        "get_refund_by_order (none found)",
        get_refund_by_order,
        {"order_id": 999999},
    )

    run_test(
        "get_refund_by_user",
        get_refund_by_user,
        {"user_id": 6},
    )

    run_test(
        "get_refund_by_user (none found)",
        get_refund_by_user,
        {"user_id": 999999},
    )

    run_test(
        "get_refund_status",
        get_refund_status,
        {"refund_id": 1},
    )

    run_test(
        "get_refund_status (not found)",
        get_refund_status,
        {"refund_id": 999999},
    )

    section_failures.append(("returns_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # RETURNS - WRITE (testing business-logic rejections)
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🔄 RETURNS - WRITE")
    print("-" * 60)

    # order_id=1 is delivered but well past the 7-day window, should be rejected
    run_test(
        "create_return_request (rejected - expired window)",
        create_return_request,
        {"order_id": 1, "order_item_id": 1, "user_id": 1, "reason": "defective"},
    )

    run_test(
        "create_return_request (invalid reason)",
        create_return_request,
        {"order_id": 1, "order_item_id": 1, "user_id": 1, "reason": "just_because"},
    )

    run_test(
        "create_return_request (wrong user)",
        create_return_request,
        {"order_id": 1, "order_item_id": 1, "user_id": 999, "reason": "defective"},
    )

    run_test(
        "create_return_request (order not found)",
        create_return_request,
        {"order_id": 999999, "order_item_id": 1, "user_id": 1, "reason": "defective"},
    )

    # return_id=2 is 'refund_completed' (terminal), should be rejected
    run_test(
        "update_return_status (rejected - terminal state)",
        update_return_status,
        {"return_id": 2, "new_status": "approved"},
    )

    run_test(
        "update_return_status (not found)",
        update_return_status,
        {"return_id": 999999, "new_status": "approved"},
    )

    section_failures.append(("returns_write", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # SUPPORT - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🎫 SUPPORT - READ")
    print("-" * 60)

    run_test(
        "get_tickets_by_user",
        get_tickets_by_user,
        {"user_id": 6},
    )

    run_test(
        "get_tickets_by_user (none found)",
        get_tickets_by_user,
        {"user_id": 999999},
    )

    run_test(
        "get_ticket_details",
        get_ticket_details,
        {"ticket_id": 1},
    )

    run_test(
        "get_ticket_details (not found)",
        get_ticket_details,
        {"ticket_id": 999999},
    )

    section_failures.append(("support_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # SUPPORT - WRITE (testing validation rejections)
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🎫 SUPPORT - WRITE")
    print("-" * 60)

    run_test(
        "create_support_ticket (invalid category)",
        create_support_ticket,
        {
            "user_id": 1,
            "category": "invalid_cat",
            "subject": "Test subject",
            "description": "This is a test description for validation",
        },
    )

    run_test(
        "create_support_ticket (invalid priority)",
        create_support_ticket,
        {
            "user_id": 1,
            "category": "general_inquiry",
            "subject": "Test subject",
            "description": "This is a test description for validation",
            "priority": "super_urgent",
        },
    )

    run_test(
        "create_support_ticket (short subject)",
        create_support_ticket,
        {
            "user_id": 1,
            "category": "general_inquiry",
            "subject": "Hi",
            "description": "This is a test description for validation",
        },
    )

    run_test(
        "create_support_ticket (short description)",
        create_support_ticket,
        {
            "user_id": 1,
            "category": "general_inquiry",
            "subject": "Test subject line",
            "description": "Short",
        },
    )

    run_test(
        "create_support_ticket (user not found)",
        create_support_ticket,
        {
            "user_id": 999999,
            "category": "general_inquiry",
            "subject": "Test subject line",
            "description": "This is a test description for validation",
        },
    )

    # ticket_id=3 is 'resolved', only valid transitions: closed, open
    run_test(
        "update_ticket_status (invalid transition)",
        update_ticket_status,
        {"ticket_id": 3, "new_status": "in_progress"},
    )

    run_test(
        "update_ticket_status (not found)",
        update_ticket_status,
        {"ticket_id": 999999, "new_status": "in_progress"},
    )

    section_failures.append(("support_write", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # COUPONS - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🎟️  COUPONS - READ")
    print("-" * 60)

    run_test(
        "validate_coupon (valid coupon)",
        validate_coupon,
        {"code": "SAVE500", "user_id": 1, "order_amount": 5000.0},
    )

    run_test(
        "validate_coupon (coupon not found)",
        validate_coupon,
        {"code": "FAKECOUPON", "user_id": 1, "order_amount": 1000.0},
    )

    run_test(
        "validate_coupon (low order amount)",
        validate_coupon,
        {"code": "SAVE500", "user_id": 1, "order_amount": 10.0},
    )

    run_test(
        "get_available_coupons (no user filter)",
        get_available_coupons,
        {},
    )

    run_test(
        "get_available_coupons (with user filter)",
        get_available_coupons,
        {"user_id": 1},
    )

    section_failures.append(("coupons_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # WALLET - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n💰 WALLET - READ")
    print("-" * 60)

    run_test(
        "get_wallet_balance",
        get_wallet_balance,
        {"user_id": 1},
    )

    run_test(
        "get_wallet_balance (no wallet)",
        get_wallet_balance,
        {"user_id": 999999},
    )

    run_test(
        "get_wallet_transactions",
        get_wallet_transactions,
        {"user_id": 1},
    )

    run_test(
        "get_wallet_transactions (with limit)",
        get_wallet_transactions,
        {"user_id": 1, "limit": 5},
    )

    run_test(
        "get_wallet_transactions (no wallet)",
        get_wallet_transactions,
        {"user_id": 999999},
    )

    section_failures.append(("wallet_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # NOTIFICATIONS - READ/WRITE
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🔔 NOTIFICATIONS - READ/WRITE")
    print("-" * 60)

    run_test(
        "get_user_notifications",
        get_user_notifications,
        {"user_id": 1},
    )

    run_test(
        "get_user_notifications (unread only)",
        get_user_notifications,
        {"user_id": 1, "unread_only": True},
    )

    run_test(
        "mark_notification_read (not found / already read)",
        mark_notification_read,
        {"notification_id": 999999},
    )

    section_failures.append(("notifications", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # USERS - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n👤 USERS - READ")
    print("-" * 60)

    run_test(
        "get_user_profile",
        get_user_profile,
        {"user_id": 1},
    )

    run_test(
        "get_user_profile (not found)",
        get_user_profile,
        {"user_id": 999999},
    )

    run_test(
        "get_user_by_email",
        get_user_by_email,
        {"email": "arjun.menon@email.com"},
    )

    run_test(
        "get_user_by_email (not found)",
        get_user_by_email,
        {"email": "nobody@nowhere.com"},
    )

    run_test(
        "get_user_addresses",
        get_user_addresses,
        {"user_id": 1},
    )

    run_test(
        "get_user_addresses (none found)",
        get_user_addresses,
        {"user_id": 999999},
    )

    section_failures.append(("users_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # CART - READ
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🛒 CART - READ")
    print("-" * 60)

    run_test(
        "get_cart_items (empty cart)",
        get_cart_items,
        {"user_id": 1},
    )

    run_test(
        "get_wishlist (empty wishlist)",
        get_wishlist,
        {"user_id": 1},
    )

    section_failures.append(("cart_read", failed - section_before))
    section_before = failed
    # ═══════════════════════════════════════════════════════════════════════════════
    # CART - WRITE (full add → update → remove cycle)
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n🛒 CART - WRITE")
    print("-" * 60)

    # Test add_to_cart validation: quantity < 1
    run_test(
        "add_to_cart (invalid quantity)",
        add_to_cart,
        {"user_id": 1, "product_id": 1, "quantity": 0},
    )

    # Test add_to_cart validation: product not found
    run_test(
        "add_to_cart (product not found)",
        add_to_cart,
        {"user_id": 1, "product_id": 999999, "quantity": 1},
    )

    # Add an item to the cart (product_id=1 has stock_quantity=150)
    run_test(
        "add_to_cart (success)",
        add_to_cart,
        {"user_id": 1, "product_id": 1, "quantity": 1},
    )

    # Add the same product again — should increment quantity
    run_test(
        "add_to_cart (increment existing)",
        add_to_cart,
        {"user_id": 1, "product_id": 1, "quantity": 1},
    )

    # Verify cart now has the item
    cart_result = run_test(
        "get_cart_items (after add)",
        get_cart_items,
        {"user_id": 1},
    )

    # Get the cart_item_id for update/remove tests
    cart_item_id = None
    if cart_result and isinstance(cart_result, dict) and cart_result.get("items"):
        cart_item_id = cart_result["items"][0]["cart_item_id"]

    if cart_item_id:
        # Update quantity
        run_test(
            "update_cart_quantity",
            update_cart_quantity,
            {"cart_item_id": cart_item_id, "quantity": 3},
        )

        # Test stock validation
        run_test(
            "update_cart_quantity (exceeds stock)",
            update_cart_quantity,
            {"cart_item_id": cart_item_id, "quantity": 99999},
        )

        # Test negative quantity
        run_test(
            "update_cart_quantity (negative)",
            update_cart_quantity,
            {"cart_item_id": cart_item_id, "quantity": -1},
        )

        # Remove from cart
        run_test(
            "remove_from_cart",
            remove_from_cart,
            {"cart_item_id": cart_item_id},
        )
    else:
        print("  ⚠️  Skipped cart update/remove tests (no cart_item_id)")

    # Remove non-existent
    run_test(
        "remove_from_cart (not found)",
        remove_from_cart,
        {"cart_item_id": 999999},
    )

    # update non-existent
    run_test(
        "update_cart_quantity (not found)",
        update_cart_quantity,
        {"cart_item_id": 999999, "quantity": 1},
    )

    # ═══════════════════════════════════════════════════════════════════════════════
    # WISHLIST - WRITE (full add → remove cycle)
    # ═══════════════════════════════════════════════════════════════════════════════
    section_failures.append(("cart_write", failed - section_before))
    section_before = failed
    print("\n💝 WISHLIST - WRITE")
    print("-" * 60)

    # Test add_to_wishlist: product not found
    run_test(
        "add_to_wishlist (product not found)",
        add_to_wishlist,
        {"user_id": 1, "product_id": 999999},
    )

    # Add a product to wishlist
    run_test(
        "add_to_wishlist (success)",
        add_to_wishlist,
        {"user_id": 1, "product_id": 1},
    )

    # Try adding the same product — should detect duplicate
    run_test(
        "add_to_wishlist (duplicate)",
        add_to_wishlist,
        {"user_id": 1, "product_id": 1},
    )

    # Get wishlist to find the wishlist_id
    wish_list = run_test(
        "get_wishlist (after add)",
        get_wishlist,
        {"user_id": 1},
    )

    wishlist_id = None
    if isinstance(wish_list, list) and wish_list:
        wishlist_id = wish_list[0]["wishlist_id"]

    if wishlist_id:
        run_test(
            "remove_from_wishlist",
            remove_from_wishlist,
            {"wishlist_id": wishlist_id},
        )
    else:
        print("  ⚠️  Skipped wishlist remove test (no wishlist_id)")

    run_test(
        "remove_from_wishlist (not found)",
        remove_from_wishlist,
        {"wishlist_id": 999999},
    )

    section_failures.append(("wishlist_write", failed - section_before))
    # ═══════════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print(f"🏁 TEST SUMMARY: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for status, name, detail in results:
            if status == "FAIL":
                print(f"  - {name}: {detail}")
        return (1, section_failures)
    print("\n✅ All tools verified successfully!")
    return (0, section_failures)


TOOL_SECTIONS = [
    "orders_read",
    "orders_write",
    "products_read",
    "logistics_read",
    "logistics_write",
    "payments_read",
    "returns_read",
    "returns_write",
    "support_read",
    "support_write",
    "coupons_read",
    "wallet_read",
    "notifications",
    "users_read",
    "cart_read",
    "cart_write",
    "wishlist_write",
]


@pytest.fixture(scope="module")
def tool_section_results():
    _, section_failures = _main()
    return {name: count for name, count in section_failures}


@pytest.mark.integration
@pytest.mark.parametrize("section", TOOL_SECTIONS)
def test_tool_section(section, tool_section_results):
    assert tool_section_results[section] == 0, f"section {section} had failures"


if __name__ == "__main__":
    sys.exit(_main()[0])
