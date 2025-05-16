# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# CMPS 372 - Assignment01 - A. Bethel 
# Point of Sale System (Console + OOP with Inheritance)
# For this assignment, you will create a POS system 
# that will have the capability to make a purchase, 
# make a return, add inventory and view reports
# Point of Sale System (Console-Based, with Inheritance)
# Supports: Purchase, Return, Inventory Management, and Reports
# Uses: Inheritance and Polymorphism, Lists for in-memory data
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

import os
# Validates the files used are found by Python
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
# GUI used to show program
from tkinter import messagebox, simpledialog, PhotoImage

# Base Transaction class 
class Transaction:
    def __init__(self, inventory):
        self.inventory = inventory
        self.selected_items = []
        self.total = 0.0

    def select_items_gui(self, action_label):
        while True:
            items_str = "\n".join([f"{item['name']} - ${item['price']}" for item in self.inventory])
            item_name = simpledialog.askstring(action_label, f"Select an item:\n\n{items_str}")
            if not item_name:
                break
            match = next((item for item in self.inventory if item['name'].lower() == item_name.lower()), None)
            if match:
                self.selected_items.append(match)
                cont = messagebox.askyesno(action_label, "Add another item?")
                if not cont:
                    break
            else:
                messagebox.showerror("Error", f"'{item_name}' not found in inventory.")

    def calculate_total(self):
        self.total = sum(item["price"] for item in self.selected_items)
        return self.total


# Purchase using inheritance 
class Purchase(Transaction):
    def complete(self):
        self.select_items_gui("Make Purchase")
        total = self.calculate_total()
        if self.selected_items:
            for item in self.selected_items:
                sales.append(item)  # Track item for report
            messagebox.showinfo("Total", f"Your total is: ${total:.2f}\nThank you for shopping at Chili's!")
        return total


# Return using inheritance 
class Return(Transaction):
    def complete(self):
        self.select_items_gui("Return Items")
        total = self.calculate_total()
        if self.selected_items:
            messagebox.showinfo("Refund", f"Your refund total is: ${total:.2f}\nThank you for visiting Chili's!")
        return -total  # Negative to deduct from total profit


# Global Variables 

inventory = [
    {"name": "Bacon Burger", "price": 12.49},
    {"name": "Boneless Wings", "price": 10.49},
    {"name": "Southwest Eggrolls", "price": 9.99},
    {"name": "Caesar Salad", "price": 7.99},
    {"name": "Classic Sirloin", "price": 17.49},
    {"name": "Rack of Ribs", "price": 15.99},
    {"name": "Shrimp Alfredo", "price": 14.99},
    {"name": "Chocolate Cake", "price": 7.49},
    {"name": "Chocolate Chip Cookie", "price": 6.99},
    {"name": "Soft Drink", "price": 2.79},
    {"name": "Iced Tea", "price": 2.49},
    {"name": "Margarita", "price": 6.99}
] # Populate inventory list

sales = [] # Tracks each customer's total (purchase or return)
report_totals = []  # Tracks each customer’s total (purchase or return)

# GUI Functions 
def make_purchase():
    purchase = Purchase(inventory)
    total = purchase.complete()
    if total > 0:
        report_totals.append(total)

def make_return():
    ret = Return(inventory)
    total = ret.complete()
    if total < 0:
        report_totals.append(total)

def manage_inventory():
    def refresh_inventory_display():
        text.delete("1.0", tk.END)
        for item in inventory:
            text.insert(tk.END, f"{item['name']} - ${item['price']}\n")

    def add_item():
        name = simpledialog.askstring("Add Item", "Enter item name:")
        try:
            price_input = simpledialog.askstring("Add Item", f"Enter price for '{name}':")
            price = round(float(price_input),2) # Round input two decimals
            inventory.append({"name": name, "price": price})
            refresh_inventory_display()
            messagebox.showinfo("Added", f"{name} added successfully.")
        except:
            messagebox.showerror("Error", "Invalid price.")

    def remove_item():
        name = simpledialog.askstring("Remove Item", "Enter item name to remove:")
        found = next((item for item in inventory if item["name"].lower() == name.lower()), None)
        if found:
            inventory.remove(found)
            refresh_inventory_display()
            messagebox.showinfo("Removed", f"{name} removed successfully.")
        else:
            messagebox.showerror("Not Found", "Item not found.")

    # Inventory window
    inv_win = tk.Toplevel(root)
    inv_win.title("Manage Inventory")
    inv_win.geometry("350x300")

    tk.Label(inv_win, text="Current Inventory:").pack()
    text = tk.Text(inv_win, height=10, width=40)
    text.pack()
    refresh_inventory_display()

    tk.Button(inv_win, text="Add Item", command=add_item).pack(pady=5)
    tk.Button(inv_win, text="Remove Item", command=remove_item).pack(pady=5)
    tk.Button(inv_win, text="Close", command=inv_win.destroy).pack(pady=5)

def view_report():
    customer_count = len(report_totals)
    total_profit = sum(report_totals)
    messagebox.showinfo("Reports", f"Total Customers: {customer_count}\nTotal Profit: ${total_profit:.2f}")

# GUI Create main window
root = tk.Tk()
root.title("Chili's POS System")
root.geometry("700x400")  # Wide window for better spacing
root.configure(bg="lightgreen")  # Set window background here

# Load logo
logo = PhotoImage(file="chilis_logo.png") # Must be in same folder as program

# Main Frame Layout
main_frame = tk.Frame(root, bg="lightgreen")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)


# Left frame for buttons
left_frame = tk.Frame(main_frame, bg="lightgreen")
left_frame.pack(side="left", anchor="n", padx=20)

# Right frame for vertically centered logo
right_frame = tk.Frame(main_frame, bg="lightgreen")
right_frame.pack(side="right", expand=True, fill="both")

logo_label = tk.Label(right_frame, image=logo, bg="lightgreen")
logo_label.place(relx=0.5, rely=0.5, anchor="center")  # Center logo vertically

# Welcome Label
tk.Label(left_frame, text="Welcome to Chili's!\nChoose an option:", font=("Comic Sans MS", 20, "bold"), bg="lightgreen").pack(pady=(0, 15))

# Button Groups 

# Top row: Purchase & Return
frame_top = tk.Frame(left_frame, bg="lightgreen")
frame_top.pack(pady=10)
tk.Button(frame_top, text="1) Make a Purchase", width=20, command=make_purchase).grid(row=0, column=0, padx=5)
tk.Button(frame_top, text="2) Make a Return", width=20, command=make_return).grid(row=0, column=1, padx=5)

# Middle row: Inventory & Report
frame_middle = tk.Frame(left_frame, bg="lightgreen")
frame_middle.pack(pady=10)
tk.Button(frame_middle, text="3) Manage Inventory", width=20, command=manage_inventory).grid(row=0, column=0, padx=5)
tk.Button(frame_middle, text="4) View Report", width=20, command=view_report).grid(row=0, column=1, padx=5)

# Exit Button
tk.Button(left_frame, text="Exit", width=42, bg="#b22222", fg="white", command=root.quit).pack(pady=30)

root.mainloop()

