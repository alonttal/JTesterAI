import os
from pathlib import Path


def create_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"✅ Created: {path}")


# Define the root for source code
ROOT = Path("src/main/java")

# 1. The "Imported" Dependency (in a different package)
payment_gateway_code = """
package com.simulation.payment;

public class PaymentGateway {
    public boolean charge(String creditCard, double amount) {
        // Imagine this calls a bank API
        return true; 
    }

    public void refund(String transactionId) {
        // Void transaction
    }
}
"""

# 2. The "Same Package" Dependency (Implicit, no import needed)
inventory_system_code = """
package com.simulation.orders;

public class InventorySystem {
    public boolean hasStock(String itemId) {
        return true;
    }

    public void reserveItem(String itemId) {
        System.out.println("Reserved " + itemId);
    }
}
"""

# 3. The Target Class (Uses both above)
order_service_code = """
package com.simulation.orders;

import com.simulation.payment.PaymentGateway;

public class OrderService {
    private final PaymentGateway paymentGateway;
    private final InventorySystem inventorySystem;

    public OrderService(PaymentGateway paymentGateway, InventorySystem inventorySystem) {
        this.paymentGateway = paymentGateway;
        this.inventorySystem = inventorySystem;
    }

    public boolean placeOrder(String itemId, double price, String creditCard) {
        if (price <= 0) {
            throw new IllegalArgumentException("Price must be positive");
        }

        // Use Implicit Dependency
        if (!inventorySystem.hasStock(itemId)) {
            throw new IllegalStateException("Item out of stock");
        }

        // Use Imported Dependency
        boolean paid = paymentGateway.charge(creditCard, price);

        if (paid) {
            inventorySystem.reserveItem(itemId);
            return true;
        }

        return false;
    }
}
"""

# Execute creation
create_file(ROOT / "com/simulation/payment/PaymentGateway.java", payment_gateway_code)
create_file(ROOT / "com/simulation/orders/InventorySystem.java", inventory_system_code)
create_file(ROOT / "com/simulation/orders/OrderService.java", order_service_code)

print("\n🎉 Simulation environment ready!")
print("Run the agent on OrderService to see if it mocks both dependencies correctly.")