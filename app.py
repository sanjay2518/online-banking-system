import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import hashlib
import json
import os

# Backend Implementation
class Account:
    def __init__(self, account_number, owner, balance=0.0, account_type="Savings"):
        self.account_number = account_number
        self.owner = owner
        self.balance = balance
        self.account_type = account_type
        self.transactions = []
    
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        transaction = Transaction(amount, "Deposit", self.account_number)
        self.transactions.append(transaction)
        return transaction
    
    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        transaction = Transaction(amount, "Withdrawal", self.account_number)
        self.transactions.append(transaction)
        return transaction
    
    def transfer(self, amount, recipient_account):
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds for transfer")
        self.balance -= amount
        recipient_account.balance += amount
        
        transaction_out = Transaction(amount, "Transfer Out", self.account_number, recipient_account.account_number)
        transaction_in = Transaction(amount, "Transfer In", recipient_account.account_number, self.account_number)
        
        self.transactions.append(transaction_out)
        recipient_account.transactions.append(transaction_in)
        
        return transaction_out, transaction_in
    
    def get_transaction_history(self):
        return self.transactions
    
    def get_balance(self):
        return self.balance

    def __str__(self):
        return f"Account {self.account_number} (Balance: ${self.balance:.2f})"

class Customer:
    def __init__(self, customer_id, name, email, phone):
        self.customer_id = customer_id
        self.name = name
        self.email = email
        self.phone = phone
        self.accounts = []
    
    def add_account(self, account):
        self.accounts.append(account)
    
    def get_account(self, account_number):
        for account in self.accounts:
            if account.account_number == account_number:
                return account
        return None
    
    def get_all_accounts(self):
        return self.accounts

class Transaction:
    def __init__(self, amount, transaction_type, account_number, related_account=None):
        self.amount = amount
        self.transaction_type = transaction_type
        self.timestamp = datetime.now()
        self.account_number = account_number
        self.related_account = related_account
    
    def __str__(self):
        return (f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.transaction_type}: "
                f"${self.amount:.2f} (Account: {self.account_number})")

class Bank:
    def __init__(self):
        self.customers = []
        self.accounts = []
        self.load_data()
    
    def add_customer(self, customer):
        self.customers.append(customer)
        for account in customer.accounts:
            self.accounts.append(account)
        self.save_data()
    
    def find_customer(self, customer_id):
        for customer in self.customers:
            if customer.customer_id == customer_id:
                return customer
        return None
    
    def find_account(self, account_number):
        for account in self.accounts:
            if account.account_number == account_number:
                return account
        return None
    
    def save_data(self):
        data = {
            "customers": [
                {
                    "customer_id": customer.customer_id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "accounts": [
                        {
                            "account_number": account.account_number,
                            "balance": account.balance,
                            "account_type": account.account_type,
                            "transactions": [
                                {
                                    "amount": t.amount,
                                    "transaction_type": t.transaction_type,
                                    "timestamp": t.timestamp.isoformat(),
                                    "account_number": t.account_number,
                                    "related_account": t.related_account
                                } for t in account.transactions
                            ]
                        } for account in customer.accounts
                    ]
                } for customer in self.customers
            ]
        }
        
        with open("bank_data.json", "w") as f:
            json.dump(data, f, indent=4)
    
    def load_data(self):
        if not os.path.exists("bank_data.json"):
            return
        
        try:
            with open("bank_data.json", "r") as f:
                data = json.load(f)
                
                for customer_data in data.get("customers", []):
                    customer = Customer(
                        customer_data["customer_id"],
                        customer_data["name"],
                        customer_data["email"],
                        customer_data["phone"]
                    )
                    
                    for account_data in customer_data.get("accounts", []):
                        account = Account(
                            account_data["account_number"],
                            customer,
                            account_data["balance"],
                            account_data.get("account_type", "Savings")
                        )
                        
                        for transaction_data in account_data.get("transactions", []):
                            transaction = Transaction(
                                transaction_data["amount"],
                                transaction_data["transaction_type"],
                                transaction_data["account_number"],
                                transaction_data.get("related_account")
                            )
                            transaction.timestamp = datetime.fromisoformat(transaction_data["timestamp"])
                            account.transactions.append(transaction)
                        
                        customer.add_account(account)
                    
                    self.add_customer(customer)
        except Exception as e:
            print(f"Error loading data: {e}")

class UserManager:
    def __init__(self):
        self.users = {}
        self.load_users()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username, password, customer_id):
        if username in self.users:
            return False
        self.users[username] = {
            "password": self.hash_password(password),
            "customer_id": customer_id
        }
        self.save_users()
        return True
    
    def authenticate(self, username, password):
        if username not in self.users:
            return None
        if self.users[username]["password"] == self.hash_password(password):
            return self.users[username]["customer_id"]
        return None
    
    def save_users(self):
        with open("users.json", "w") as f:
            json.dump(self.users, f)
    
    def load_users(self):
        if not os.path.exists("users.json"):
            return
        try:
            with open("users.json", "r") as f:
                self.users = json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")

# Frontend Implementation
class BankingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Online Banking System")
        self.root.geometry("800x600")
        
        self.bank = Bank()
        self.user_manager = UserManager()
        self.current_customer = None
        self.current_account = None
        
        self.create_login_frame()
    
    def clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def create_login_frame(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Online Banking System", font=("Arial", 20)).pack(pady=20)
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        self.username_entry = tk.Entry(frame)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Register", command=self.create_register_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
    
    def create_register_frame(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Register New User", font=("Arial", 20)).pack(pady=20)
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Username:").grid(row=0, column=0, padx=10, pady=5)
        self.reg_username = tk.Entry(frame)
        self.reg_username.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Password:").grid(row=1, column=0, padx=10, pady=5)
        self.reg_password = tk.Entry(frame, show="*")
        self.reg_password.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Customer ID:").grid(row=2, column=0, padx=10, pady=5)
        self.reg_customer_id = tk.Entry(frame)
        self.reg_customer_id.grid(row=2, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Full Name:").grid(row=3, column=0, padx=10, pady=5)
        self.reg_name = tk.Entry(frame)
        self.reg_name.grid(row=3, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Email:").grid(row=4, column=0, padx=10, pady=5)
        self.reg_email = tk.Entry(frame)
        self.reg_email.grid(row=4, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Phone:").grid(row=5, column=0, padx=10, pady=5)
        self.reg_phone = tk.Entry(frame)
        self.reg_phone.grid(row=5, column=1, padx=10, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Register", command=self.register).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=self.create_login_frame).pack(side=tk.LEFT, padx=5)
    
    def create_main_menu(self):
        self.clear_frame()
        
        tk.Label(self.root, text=f"Welcome, {self.current_customer.name}", font=("Arial", 20)).pack(pady=20)
        
        # Account selection if multiple accounts exist
        if len(self.current_customer.accounts) > 1:
            account_frame = tk.Frame(self.root)
            account_frame.pack(pady=10)
            
            tk.Label(account_frame, text="Select Account:").pack(side=tk.LEFT)
            
            self.account_var = tk.StringVar()
            self.account_var.set(self.current_customer.accounts[0].account_number)
            
            account_menu = tk.OptionMenu(account_frame, self.account_var, 
                                        *[acc.account_number for acc in self.current_customer.accounts],
                                        command=self.select_account)
            account_menu.pack(side=tk.LEFT, padx=10)
            
            self.current_account = self.current_customer.get_account(self.account_var.get())
        else:
            self.current_account = self.current_customer.accounts[0]
        
        # Display current account info
        account_info_frame = tk.Frame(self.root)
        account_info_frame.pack(pady=10)
        
        tk.Label(account_info_frame, 
                text=f"Account: {self.current_account.account_number} | Balance: ${self.current_account.get_balance():.2f}",
                font=("Arial", 12)).pack()
        
        # Main buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        buttons = [
            ("Deposit", self.create_deposit_frame),
            ("Withdraw", self.create_withdraw_frame),
            ("Transfer", self.create_transfer_frame),
            ("Transaction History", self.show_transaction_history),
            ("Logout", self.logout)
        ]
        
        for text, command in buttons:
            tk.Button(button_frame, text=text, command=command, width=15).pack(pady=5)
    
    def create_deposit_frame(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Deposit Funds", font=("Arial", 20)).pack(pady=20)
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Amount:").grid(row=0, column=0, padx=10, pady=5)
        self.deposit_amount = tk.Entry(frame)
        self.deposit_amount.grid(row=0, column=1, padx=10, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Deposit", command=self.process_deposit).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=self.create_main_menu).pack(side=tk.LEFT, padx=5)
    
    def create_withdraw_frame(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Withdraw Funds", font=("Arial", 20)).pack(pady=20)
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Amount:").grid(row=0, column=0, padx=10, pady=5)
        self.withdraw_amount = tk.Entry(frame)
        self.withdraw_amount.grid(row=0, column=1, padx=10, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Withdraw", command=self.process_withdraw).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=self.create_main_menu).pack(side=tk.LEFT, padx=5)
    
    def create_transfer_frame(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Transfer Funds", font=("Arial", 20)).pack(pady=20)
        
        frame = tk.Frame(self.root)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Recipient Account Number:").grid(row=0, column=0, padx=10, pady=5)
        self.recipient_account = tk.Entry(frame)
        self.recipient_account.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(frame, text="Amount:").grid(row=1, column=0, padx=10, pady=5)
        self.transfer_amount = tk.Entry(frame)
        self.transfer_amount.grid(row=1, column=1, padx=10, pady=5)
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Transfer", command=self.process_transfer).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=self.create_main_menu).pack(side=tk.LEFT, padx=5)
    
    def show_transaction_history(self):
        self.clear_frame()
        
        tk.Label(self.root, text="Transaction History", font=("Arial", 20)).pack(pady=20)
        
        # Create a frame for the listbox and scrollbar
        list_frame = tk.Frame(self.root)
        list_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Create a scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a listbox to display transactions
        transaction_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=80, height=15)
        transaction_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar
        scrollbar.config(command=transaction_list.yview)
        
        # Add transactions to the listbox
        for transaction in self.current_account.get_transaction_history():
            transaction_list.insert(tk.END, str(transaction))
        
        # Back button
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Back", command=self.create_main_menu).pack()
    
    def select_account(self, account_number):
        self.current_account = self.current_customer.get_account(account_number)
        self.create_main_menu()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        customer_id = self.user_manager.authenticate(username, password)
        if customer_id is None:
            messagebox.showerror("Error", "Invalid username or password")
            return
        
        self.current_customer = self.bank.find_customer(customer_id)
        if self.current_customer is None:
            messagebox.showerror("Error", "Customer not found")
            return
        
        self.create_main_menu()
    
    def register(self):
        username = self.reg_username.get()
        password = self.reg_password.get()
        customer_id = self.reg_customer_id.get()
        name = self.reg_name.get()
        email = self.reg_email.get()
        phone = self.reg_phone.get()
        
        if not all([username, password, customer_id, name, email, phone]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if self.bank.find_customer(customer_id) is not None:
            messagebox.showerror("Error", "Customer ID already exists")
            return
        
        # Create new customer with a default account
        new_customer = Customer(customer_id, name, email, phone)
        new_account = Account(f"ACC-{customer_id}", new_customer, 0.0)
        new_customer.add_account(new_account)
        self.bank.add_customer(new_customer)
        
        if not self.user_manager.register_user(username, password, customer_id):
            messagebox.showerror("Error", "Username already exists")
            return
        
        messagebox.showinfo("Success", "Registration successful! Please login.")
        self.create_login_frame()
    
    def process_deposit(self):
        try:
            amount = float(self.deposit_amount.get())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            self.current_account.deposit(amount)
            self.bank.save_data()
            
            messagebox.showinfo("Success", f"Deposited ${amount:.2f} successfully")
            self.create_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def process_withdraw(self):
        try:
            amount = float(self.withdraw_amount.get())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            self.current_account.withdraw(amount)
            self.bank.save_data()
            
            messagebox.showinfo("Success", f"Withdrew ${amount:.2f} successfully")
            self.create_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def process_transfer(self):
        try:
            recipient_account_number = self.recipient_account.get()
            amount = float(self.transfer_amount.get())
            
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            recipient_account = self.bank.find_account(recipient_account_number)
            if recipient_account is None:
                raise ValueError("Recipient account not found")
            
            if recipient_account.account_number == self.current_account.account_number:
                raise ValueError("Cannot transfer to the same account")
            
            self.current_account.transfer(amount, recipient_account)
            self.bank.save_data()
            
            messagebox.showinfo("Success", 
                              f"Transferred ${amount:.2f} to account {recipient_account_number}")
            self.create_main_menu()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def logout(self):
        self.current_customer = None
        self.current_account = None
        self.create_login_frame()

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = BankingApp(root)
    root.mainloop()