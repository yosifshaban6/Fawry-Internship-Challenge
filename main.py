from abc import ABC, abstractmethod
from datetime import datetime

class Shippable(ABC):
  @abstractmethod
  def get_name(self): pass

  @abstractmethod
  def get_weight(self): pass

class Product(Shippable):
  def __init__(self, name, price_per_unit, *, 
               available_quantity=0, available_weight=0,
               expiration_date=None, is_shippable=False, by_weight=False):
    self.name = name
    self.price_per_unit = price_per_unit
    self.expiration_date = expiration_date
    self.is_shippable = is_shippable
    self.by_weight = by_weight
    self.available_quantity = available_quantity
    self.available_weight = available_weight

  def is_expired(self):
    if not self.expiration_date:
      return False
    return datetime.strptime(self.expiration_date, "%Y-%m-%d") < datetime.now()

  def get_total_price(self, amount):
    return self.price_per_unit * amount

  def get_weight(self, amount):
    return amount if self.by_weight else 0

  def get_name(self):
    return self.name

class Inventory:
  def __init__(self):
    self.products = {}

  def add_product(self, product: Product):
    self.products[product.name] = product

  def get_product(self, name):
    return self.products.get(name)

  def is_available(self, name, amount):
    product = self.get_product(name)
    if not product or product.is_expired():
      return False, "Product not found or expired."
    if product.by_weight:
      if amount > product.available_weight:
        return False, f"Only {product.available_weight}g of {name} available."
    else:
      if amount > product.available_quantity:
        return False, f"Only {product.available_quantity} units of {name} available."
    return True, ""

  def deduct_stock(self, name, amount):
    product = self.get_product(name)
    if product:
      if product.by_weight:
        product.available_weight -= amount
      else:
        product.available_quantity -= amount

  def list_products(self):
    print("Available Products:")
    print(f"{'Name':<25} {'Type':<10} {'Price':<10} {'Stock':<10} {'Expires':<12}")
    print("-" * 70)
    for p in self.products.values():
      type_ = "Weight" if p.by_weight else "Quantity"
      stock = f"{p.available_weight}g" if p.by_weight else f"{p.available_quantity} pcs"
      expiration = p.expiration_date if p.expiration_date else "N/A"
      print(f"{p.name:<25} {type_:<10} {p.price_per_unit:<10.2f} {stock:<10} {expiration:<12}")
    print("-" * 70)

class CartItem:
  def __init__(self, product: Product, amount):
    self.product = product
    self.amount = amount

  def get_total_price(self):
    return self.product.get_total_price(self.amount)

  def get_weight(self):
    return self.product.get_weight(self.amount)

  def get_name(self):
    return self.product.get_name()

class Customer:
  def __init__(self, name, balance):
    self.name = name
    self.balance = balance

class ShoppingCart:
  SHIPPING_FEE = 5.0

  def __init__(self, customer: Customer, inventory: Inventory):
    self.customer = customer
    self.inventory = inventory
    self.__items = []

  def add_item(self, product_name, amount):
    product = self.inventory.get_product(product_name)
    if not product:
      print(f"{product_name} not found in inventory.")
      return
    if product.is_expired():
      print(f"Cannot add {product_name}: expired.")
      return
    available, msg = self.inventory.is_available(product_name, amount)
    if not available:
      print(f"Cannot add {product_name}: {msg}")
      return
    self.__items.append(CartItem(product, amount))

  def is_empty(self):
    return len(self.__items) == 0

  def get_total_price(self):
    return sum(item.get_total_price() for item in self.__items)

  def get_shippable_items(self):
    return [item for item in self.__items if item.product.is_shippable]

  def view_cart(self):
    if self.is_empty():
      print("Your cart is empty.")
      return
    print("Your cart contains:")
    print(f"{'No.':<4} {'Name':<20} {'Qty/Wt':<10} {'Expires':<12} {'Shippable':<10} {'Total':<8}")
    print("-" * 70)
    for i, item in enumerate(self.__items, 1):
      prod = item.product
      expiration = prod.expiration_date if prod.expiration_date else "N/A"
      shippable = "Yes" if prod.is_shippable else "No"
      qty_or_wt = f"{item.amount:.2f} g" if prod.by_weight else f"{item.amount} pcs"
      print(f"{i:<4} {prod.name:<20} {qty_or_wt:<10} {expiration:<12} {shippable:<10} {item.get_total_price():.2f}$")
    print("-" * 70)
    print(f"Subtotal: {self.get_total_price():.2f}$")

  def checkout(self):
    print("\nProcessing Checkout...")
    if self.is_empty():
      print("Cart is empty.")
      return
    for item in self.__items:
      if item.product.is_expired():
        print(f"Cannot checkout: {item.product.name} is expired.")
        return
    subtotal = self.get_total_price()
    total = subtotal + self.SHIPPING_FEE
    if self.customer.balance < total:
      print("Insufficient balance.")
      return
    for item in self.__items:
      self.inventory.deduct_stock(item.product.name, item.amount)
    self.customer.balance -= total
    print("\n" + "=" * 50)
    print("RECEIPT")
    print("=" * 50)
    print(f"{'Product':<20} {'Qty/Wt':<10} {'Unit':<10} {'Total':<10}")
    print("-" * 50)
    for item in self.__items:
      name = item.product.name
      amount = f"{item.amount:.2f}g" if item.product.by_weight else f"{item.amount} pcs"
      unit_price = f"{item.product.price_per_unit:.2f}$"
      total_price = f"{item.get_total_price():.2f}$"
      print(f"{name:<20} {amount:<10} {unit_price:<10} {total_price:<10}")
    print("-" * 50)
    print(f"{'Subtotal':<42} {subtotal:.2f}$")
    print(f"{'Shipping Fee':<42} {self.SHIPPING_FEE:.2f}$")
    print(f"{'Total Paid':<42} {total:.2f}$")
    print(f"{'Balance Left':<42} {self.customer.balance:.2f}$")
    print("=" * 50)
    shippable_items = self.get_shippable_items()
    if shippable_items:
      ShippingService.send_items(shippable_items)
    self.__items.clear()
    print("Checkout complete.\n")

class ShippingService:
  @staticmethod
  def send_items(items):
    print("\nShipping the following items:")
    for item in items:
      print(f"- {item.get_name()} ({item.get_weight()}g)")
    print("Shipping completed.")

if __name__ == "__main__":
  inventory = Inventory()
  inventory.add_product(Product("Cheese", 0.05, available_weight=2000, expiration_date="2025-08-01", is_shippable=True, by_weight=True))
  inventory.add_product(Product("TV", 10000.0, available_quantity=3, is_shippable=True))
  inventory.add_product(Product("Mobile Scratch Card", 50.0, available_quantity=5))
  inventory.add_product(Product("Biscuits", 10.0, available_quantity=10, expiration_date="2023-01-01"))

  customer = Customer("Youssef", balance=20000)
  cart = ShoppingCart(customer, inventory)

  inventory.list_products()

  cart.add_item("Cheese", 1000)
  cart.add_item("TV", 1)
  cart.add_item("Mobile Scratch Card", 2)
  cart.add_item("TV", 5)
  cart.add_item("Cheese", 1500)
  cart.add_item("Biscuits", 2)

  cart.view_cart()
  cart.checkout()

  cart.add_item("TV", 2)
  cart.view_cart()
  cart.checkout()
