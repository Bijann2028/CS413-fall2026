"""Small discount calculator used in CS413 Lab 1."""


def calculate_total(prices, discount_percent):
    """Return the total after applying a percentage discount."""
    subtotal = sum(prices)
    return subtotal * (1 - discount_percent / 100)


def main():
    prices = [50.0, 40.0, 60.0]
    discount_percent = 20
    expected_total = 120.0
    actual_total = calculate_total(prices, discount_percent)

    print(f"Subtotal:       ${sum(prices):.2f}")
    print(f"Discount:        {discount_percent}%")
    print(f"Expected total: ${expected_total:.2f}")
    print(f"Program output: ${actual_total:.2f}")


if __name__ == "__main__":
    main()
