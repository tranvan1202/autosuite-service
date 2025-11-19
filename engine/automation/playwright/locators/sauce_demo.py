# root/engine/automation/playwright/locators/sauce_demo.py
"""Locators for Sauce Demo pages."""
# Why: selectors live here so POM stays readable and maintainable.

# Common
L_TITLE = "span.title[data-test='title']"

# Login
URL_LOGIN = "https://www.saucedemo.com/"
L_USERNAME_LOCATOR = "#user-name"
L_PASSWORD_LOCATOR = "#password"  # noqa: S105
L_BTN_LOGIN = "#login-button"
L_INV_GUARD = ".inventory_list"
L_LOGIN_ERR = "[data-test='error']"

# Inventory
L_INV_LIST = ".inventory_list"
L_CARD = ".inventory_item"
L_NAME = ".inventory_item_name"
L_PRICE = ".inventory_item_price"
L_ADD_BTN = ".pricebar button"
L_CART_ICON = ".shopping_cart_link"

# Cart
L_CART_ITEM = ".cart_item"
L_CART_NAME = ".inventory_item_name"
L_BTN_CHECKOUT = "#checkout"

# Checkout step 1
URL_STEP1 = "**/checkout-step-one.html"
L_FIRST = "[data-test='firstName']"
L_LAST = "[data-test='lastName']"
L_ZIP = "[data-test='postalCode']"
L_BTN_CONTINUE = "#continue"

# Checkout step 2
URL_STEP2 = "**/checkout-step-two.html"
L_STEP2_ITEM = ".cart_item"
L_STEP2_NAME = ".inventory_item_name"
L_SUBTOTAL = ".summary_subtotal_label"
L_TAX = ".summary_tax_label"
L_TOTAL = ".summary_total_label"
L_BTN_FINISH = "#finish"

# Complete
URL_COMPLETE = "**/checkout-complete.html"
L_COMPLETE_HEADER = "h2.complete-header"
L_COMPLETE_TEXT = ".complete-text"
