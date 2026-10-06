"""MCP Server for Agentic Inventory Restock Predictive Balancer."""
import sys
import json
import time
from client import AgenticInventoryRestockPredictiveBalancer

balancer = AgenticInventoryRestockPredictiveBalancer()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "balance_predictive_inventory":
        raise ValueError(f"Unknown tool: {name}")

    action = args.get("action", "evaluate_sku_inventory")
    sku = args.get("sku", "SKU-DEFAULT")
    stock = int(args.get("current_stock", 50))
    lead = int(args.get("lead_time_days", 7))
    hist = args.get("sales_history_7d", [12.0, 15.0, 14.0, 18.0, 10.0, 16.0, 13.0])

    if action == "evaluate_sku_inventory":
        return balancer.evaluate_sku_inventory(sku, stock, lead, hist)
    elif action == "generate_purchase_order":
        ev = balancer.evaluate_sku_inventory(sku, stock, lead, hist)
        return balancer.generate_purchase_order(sku, args.get("supplier_id", "SUP-GLOBAL-01"), ev)
    else:
        raise ValueError(f"Invalid action: {action}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running self-test...")
        history = [20.0, 25.0, 22.0, 28.0, 21.0, 24.0, 26.0]
        ev = balancer.evaluate_sku_inventory("SKU-ROBOT-01", current_stock=30, lead_time_days=5, sales_history_7d=history)
        assert ev["needs_restock"] is True
        assert ev["reorder_point_units"] > 30
        po = balancer.generate_purchase_order("SKU-ROBOT-01", "SUP-UNITREE", ev)
        assert po["po_created"] is True
        assert "PO-" in po["purchase_order_id"]
        print("Self-test PASSED!")
        sys.exit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "AgenticInventoryRestockPredictiveBalancer", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [{
                            "name": "balance_predictive_inventory",
                            "description": "Calculate SKU run rate, reorder point (ROP), safety stock buffer, and generate automated restock purchase orders.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["evaluate_sku_inventory", "generate_purchase_order"]},
                                    "sku": {"type": "string"},
                                    "current_stock": {"type": "integer"},
                                    "lead_time_days": {"type": "integer"},
                                    "sales_history_7d": {"type": "array"}
                                },
                                "required": ["action"]
                            }
                        }]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
