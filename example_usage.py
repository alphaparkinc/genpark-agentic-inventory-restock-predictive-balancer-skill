"""Example usage for AgenticInventoryRestockPredictiveBalancer."""
import sys
import json
from client import AgenticInventoryRestockPredictiveBalancer

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== Agentic Commerce Supply Chain Inventory Balancer Demo ===")
    balancer = AgenticInventoryRestockPredictiveBalancer()

    sales_7d = [45.0, 52.0, 48.0, 55.0, 50.0, 60.0, 53.0] # mean ~51.8 units/day

    print("\n--- 1. Evaluating SKU Run-Rate and Reorder Point (ROP) ---")
    eval_res = balancer.evaluate_sku_inventory(
        sku="ECOFLOW-DELTA-PRO-3",
        current_stock=180,
        lead_time_days=7,
        sales_history_7d=sales_7d,
        unit_cost_usd=1200.00
    )
    print(f"Mean Daily Demand: {eval_res['mean_daily_sales']} units")
    print(f"Safety Stock Buffer: {eval_res['safety_stock_units']} units")
    print(f"Reorder Point: {eval_res['reorder_point_units']} units")
    print(f"Current Stock: {eval_res['current_stock']} units (Days Left: {eval_res['days_of_inventory_remaining']})")
    print(f"Needs Restock: {eval_res['needs_restock']} (Status: {eval_res['restock_urgency']})")

    if eval_res["needs_restock"]:
        print("\n--- 2. Synthesizing Autonomous Supplier Purchase Order ---")
        po = balancer.generate_purchase_order(
            sku="ECOFLOW-DELTA-PRO-3",
            supplier_id="SUP-ECOFLOW-OFFICIAL",
            evaluation=eval_res
        )
        print(f"Created PO #{po['purchase_order_id']} for {po['ordered_quantity']} units")
        print(f"Estimated Total PO Cost: ${po['total_estimated_amount_usd']:,.2f}")

if __name__ == "__main__":
    main()
