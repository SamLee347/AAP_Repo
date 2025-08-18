from Database.db import SessionLocal, init_db
from Database_Table.inventory import Inventory
from Database_Table.order import Order

def populate_test_data():
    session = SessionLocal()

    # Clear existing data (important for testing)
    session.query(Order).delete()
    session.query(Inventory).delete()

    # Create Inventory test items
    electronics = Inventory(
        ItemId=101,
        ItemName="Cool Gadget",
        Date="2025-06-01",
        ItemQuantity=100,
        ItemCategory="Electronics",
        UnitsSold=50,
        Weight=1.5,
        Size=10.0,
        Priority="High",
        ItemQuantityLastMonth=80,  # Example lag feature
        Dispose=False,
        Location="Warehouse A",
    )

    clothing = Inventory(
        ItemId=102,
        ItemName="Stylish Shirt",
        Date="2025-07-01",
        ItemQuantity=200,
        ItemCategory="Clothing",
        UnitsSold=100,
        Weight=2.0,
        Size=20.0,
        Priority="Medium",
        ItemQuantityLastMonth=150,  # Example lag feature
        Dispose=False,
        Location="Warehouse B",
    )

    Clothes = Inventory(
        ItemId=103,
        ItemName="Cool Clothes",
        Date="2025-08-01",
        ItemQuantity=150,
        ItemCategory="Clothing",
        UnitsSold=75,
        Weight=15.0,
        Size=50.0,
        Priority="Low",
        ItemQuantityLastMonth=20,  # Example lag feature
        Dispose=True,
        Location="Warehouse C",
    )

    # Create Orders that reference these inventory items
    orders = [
        Order(
            OrderId=1001,
            ItemId=101,  # References electronics ItemId
            OrderQuantity=10,
            Sales=5000,
            Price=500,
            Discount=50,
            Profit=4500,
            DateOrdered="2025-06-15",
            DateReceived="2025-06-20",
            CustomerSegment="Corporate",
        ),
        Order(
            OrderId=1002,
            ItemId=102,  # References clothing ItemId
            OrderQuantity=20,
            Sales=2000,
            Price=100,
            Discount=20,
            Profit=1980,
            DateOrdered="2025-07-10",
            DateReceived="2025-07-12",
            CustomerSegment="Retail",
        ),
        Order(
            OrderId=1003,
            ItemId=101,  # References electronics ItemId again
            OrderQuantity=5,
            Sales=2500,
            Price=500,
            Discount=25,
            Profit=2475,
            DateOrdered="2025-08-05",
            DateReceived="2025-08-10",
            CustomerSegment="Wholesale",
        ),
    ]

    # Add to session and commit
    session.add_all([electronics, clothing, Clothes])
    session.add_all(orders)
    session.commit()
    session.close()