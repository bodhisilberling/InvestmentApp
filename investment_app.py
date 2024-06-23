
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog, QFileDialog
import sys
import yfinance as yf
import pandas as pd

# Database Setup
conn = sqlite3.connect('investment_app.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS investments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    symbol TEXT NOT NULL,
    shares REAL NOT NULL,
    purchase_price REAL NOT NULL,
    purchase_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()

class InvestmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Investment Tracker")
        self.setGeometry(100, 100, 800, 600)
        
        self.username = None
        self.user_id = None
        
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        self.main_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.main_layout.addWidget(self.password_input)
        
        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.login)
        self.main_layout.addWidget(self.login_button)
        
        self.register_button = QPushButton("Register", self)
        self.register_button.clicked.connect(self.register)
        self.main_layout.addWidget(self.register_button)
        
        self.investment_table = QTableWidget(self)
        self.main_layout.addWidget(self.investment_table)
        
        self.add_investment_button = QPushButton("Add Investment", self)
        self.add_investment_button.clicked.connect(self.add_investment)
        self.main_layout.addWidget(self.add_investment_button)
        
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.load_investments)
        self.main_layout.addWidget(self.refresh_button)
        
        self.summary_button = QPushButton("Portfolio Summary", self)
        self.summary_button.clicked.connect(self.show_summary)
        self.main_layout.addWidget(self.summary_button)
        
        self.export_button = QPushButton("Export Data", self)
        self.export_button.clicked.connect(self.export_data)
        self.main_layout.addWidget(self.export_button)
        
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = sqlite3.connect('investment_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.user_id = user[0]
            self.username = username
            QMessageBox.information(self, "Login", "Login successful")
            self.load_investments()
        else:
            QMessageBox.warning(self, "Login", "Invalid username or password")
    
    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        conn = sqlite3.connect('investment_app.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            QMessageBox.information(self, "Register", "Registration successful")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Register", "Username already exists")
        conn.close()
    
    def add_investment(self):
        if not self.user_id:
            QMessageBox.warning(self, "Add Investment", "Please login first")
            return
        
        symbol, ok1 = QInputDialog.getText(self, "Add Investment", "Enter Stock Symbol:")
        shares, ok2 = QInputDialog.getDouble(self, "Add Investment", "Enter Number of Shares:")
        price, ok3 = QInputDialog.getDouble(self, "Add Investment", "Enter Purchase Price:")
        date, ok4 = QInputDialog.getText(self, "Add Investment", "Enter Purchase Date (YYYY-MM-DD):")
        
        if ok1 and ok2 and ok3 and ok4:
            conn = sqlite3.connect('investment_app.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO investments (user_id, symbol, shares, purchase_price, purchase_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, symbol, shares, price, date))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Add Investment", "Investment added successfully")
            self.load_investments()
    
    def load_investments(self):
        if not self.user_id:
            return
        
        conn = sqlite3.connect('investment_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, shares, purchase_price, purchase_date FROM investments WHERE user_id = ?', (self.user_id,))
        investments = cursor.fetchall()
        conn.close()
        
        self.investment_table.setRowCount(len(investments))
        self.investment_table.setColumnCount(5)
        self.investment_table.setHorizontalHeaderLabels(['Symbol', 'Shares', 'Purchase Price', 'Purchase Date', 'Current Value'])
        
        for row, investment in enumerate(investments):
            symbol, shares, purchase_price, purchase_date = investment
            shares = float(shares)
            
            # Get current stock price
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'][0]
            current_value = shares * current_price
            
            self.investment_table.setItem(row, 0, QTableWidgetItem(symbol))
            self.investment_table.setItem(row, 1, QTableWidgetItem(str(shares)))
            self.investment_table.setItem(row, 2, QTableWidgetItem(str(purchase_price)))
            self.investment_table.setItem(row, 3, QTableWidgetItem(purchase_date))
            self.investment_table.setItem(row, 4, QTableWidgetItem(f"${current_value:.2f}"))
    
    def show_summary(self):
        if not self.user_id:
            QMessageBox.warning(self, "Portfolio Summary", "Please login first")
            return
        
        conn = sqlite3.connect('investment_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT symbol, shares, purchase_price FROM investments WHERE user_id = ?', (self.user_id,))
        investments = cursor.fetchall()
        conn.close()
        
        total_investment = 0
        total_value = 0
        
        for investment in investments:
            symbol, shares, purchase_price = investment
            shares = float(shares)
            total_investment += shares * purchase_price
            
            # Get current stock price
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'][0]
            total_value += shares * current_price
        
        profit_loss = total_value - total_investment
        
        QMessageBox.information(self, "Portfolio Summary", f"Total Investment: ${total_investment:.2f}\nCurrent Value: ${total_value:.2f}\nProfit/Loss: ${profit_loss:.2f}")
    
    def export_data(self):
        if not self.user_id:
            QMessageBox.warning(self, "Export Data", "Please login first")
            return
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        
        if file_name:
            conn = sqlite3.connect('investment_app.db')
            cursor = conn.cursor()
            cursor.execute('SELECT symbol, shares, purchase_price, purchase_date FROM investments WHERE user_id = ?', (self.user_id,))
            investments = cursor.fetchall()
            conn.close()
            
            df = pd.DataFrame(investments, columns=['Symbol', 'Shares', 'Purchase Price', 'Purchase Date'])
            df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Export Data", "Data exported successfully")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InvestmentApp()
    window.show()
    sys.exit(app.exec_())
