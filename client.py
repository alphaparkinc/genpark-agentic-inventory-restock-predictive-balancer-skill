"""
Agentic Inventory Restock Predictive Balancer (Zero External Dependencies)
Calculates EMA demand velocity, statistical safety stock, and automated supplier PO generation.
"""
import time
import math
import hashlib
import json
from typing import Dict, Any, List, Optional

SERVICE_Z_VALUES = {
    "STANDARD_90": 1.28,
    "HIGH_95": 1.645,
    "CRITICAL_99": 2.33
}

class AgenticInventoryRestockPredictiveBalancer:
    def __init__(self, default_service_level: str = "HIGH_95"):
        self.default_service_level = default_service_level

    def evaluate_sku_inventory(
        self,
        sku: str,
        current_stock: int,
        lead_time_days: int,
        sales_history_7d: List[float],
        unit_cost_usd: float = 25.0,
        service_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates run rate, computes Reorder Point:
        ROP = (Daily Demand * Lead Time) + Safety Stock
        Safety Stock = z * StdDev * sqrt(Lead Time)
        """
        if not sales_history_7d:
            sales_history_7d = [10.0]

        # Calculate mean daily demand
        n = len(sales_history_7d)
        mean_demand = sum(sales_history_7d) / max(1, n)

        # Standard deviation of demand
        variance = sum((x - mean_demand) ** 2 for x in sales_history_7d) / max(1, n)
        std_dev = math.sqrt(variance)

        # Service level factor z
        z = SERVICE_Z_VALUES.get((service_level or self.default_service_level).upper(), 1.645)

        # Safety Stock formula: z * sigma * sqrt(L)
        safety_stock = math.ceil(z * std_dev * math.sqrt(max(1, lead_time_days)))

        # Reorder Point (ROP)
        reorder_point = math.ceil((mean_demand * lead_time_days) + safety_stock)

        # Days of Inventory Remaining (DOIR)
        days_remaining = round(current_stock / max(0.1, mean_demand), 1)

        # Needs restock if current on-hand <= ROP
        needs_restock = current_stock <= reorder_point

        # Recommended order quantity: Economic Batch or 30 days of demand
        target_buffer_days = 30
        ideal_stock_level = math.ceil(mean_demand * (lead_time_days + target_buffer_days)) + safety_stock
        recommended_order_units = max(0, ideal_stock_level - current_stock) if needs_restock else 0

        urgency = "OK"
        if needs_restock:
            urgency = "CRITICAL_STOCKOUT_RISK" if days_remaining <= lead_time_days else "REORDER_TRIGGERED"

        return {
            "sku": sku,
            "current_stock": current_stock,
            "mean_daily_sales": round(mean_demand, 2),
            "lead_time_days": lead_time_days,
            "safety_stock_units": safety_stock,
            "reorder_point_units": reorder_point,
            "days_of_inventory_remaining": days_remaining,
            "needs_restock": needs_restock,
            "restock_urgency": urgency,
            "recommended_order_units": recommended_order_units,
            "estimated_po_cost_usd": round(recommended_order_units * unit_cost_usd, 2)
        }

    def generate_purchase_order(
        self,
        sku: str,
        supplier_id: str,
        evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesizes formal Purchase Order payload for ERP/Warehouse integration."""
        if not evaluation.get("needs_restock"):
            return {
                "po_created": False,
                "reason": "Stock level exceeds reorder point; no replenishment required."
            }

        now = time.time()
        po_id = "PO-" + hashlib.sha256(f"{sku}:{supplier_id}:{now}".encode("utf-8")).hexdigest()[:8].upper()

        return {
            "po_created": True,
            "purchase_order_id": po_id,
            "sku": sku,
            "supplier_id": supplier_id,
            "ordered_quantity": evaluation["recommended_order_units"],
            "urgency": evaluation["restock_urgency"],
            "total_estimated_amount_usd": evaluation["estimated_po_cost_usd"],
            "created_at": now,
            "status": "AWAITING_SUPPLIER_CONFIRMATION"
        }
