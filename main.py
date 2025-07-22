from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QInputDialog, QMessageBox, QTableWidgetItem, QVBoxLayout, QLabel, QListWidgetItem, QFileDialog
from PyQt5.uic import loadUi
from sms import send_sms
from PyQt5.QtCore import QTimer, QDate, Qt
from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtGui import QPainter, QPixmap
from datetime import datetime, timedelta
from dbfunctions import get_user_fullname, get_user_id_by_phone
import sys
import re
import os
import dbfunctions
import random
import subprocess
import jdatetime
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from datetime import datetime, date
from PyQt5.QtChart import QChart, QChartView, QPieSeries


def fa_to_en(text):
    fa_digits = '۰۱۲۳۴۵۶۷۸۹'
    en_digits = '0123456789'
    return text.translate(str.maketrans(fa_digits, en_digits))

def show_messagebox(parent, title, text, icon=QMessageBox.Information):
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: rgb(0, 92, 137); color: white;
            font-size: 15px;
        }
        QPushButton {
            font: 16pt ".AppleSystemUIFont"; background-color:rgb(109, 171, 231); color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold; 
        }
        QPushButton:hover {
            background-color: rgb(109, 160, 200);
        }
    """)
    msg.exec_()

dbfunctions.create_tables()


class Main(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('./ui/mainpage.ui', self)

        self.signinbutton.clicked.connect(self.ShowSignInPage)
        self.signupbutton.clicked.connect(self.ShowSignUpPage)
        
    def ShowSignInPage(self):
        window2.show()
        self.close()

    def ShowSignUpPage(self):
        window3.show()
        self.close()


class SignInPage(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('./ui/signinpage.ui', self)
        self.backbutton.clicked.connect(self.ShowMainPage)
        self.signinbutton.clicked.connect(self.CheckUser)

    def ShowMainPage(self):
        window1.show()
        self.close()

    def CheckUser(self):
        def fa_to_en(text):
            fa_digits = '۰۱۲۳۴۵۶۷۸۹'
            en_digits = '0123456789'
            return text.translate(str.maketrans(fa_digits, en_digits))

        phone = fa_to_en(self.phonelineedit.text().strip())
        password = fa_to_en(self.passwordlineedit.text().strip())
        alluser = dbfunctions.check_user()

        if phone and password:
            for user in alluser:
                db_phone = user['phone']
                db_password = user['password']
                db_id = user['id']

                if db_phone == phone and db_password == password:
                    self.errorlabel.setText('✅ خوش آمدید')
                    global window5
                    window5 = WorkPage(db_id)
                    window5.show()
                    self.close()
                    return

            self.errorlabel.setText('شماره موبایل یا رمز عبور اشتباه است')
        else:
            self.errorlabel.setText('لطفاً اطلاعات را به صورت کامل وارد کنید')


class SignUpPage(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('./ui/signupage.ui', self)
        self.backbutton.clicked.connect(self.ShowMainPage)
        self.signupbutton.clicked.connect(self.AddUser)

    def ShowMainPage(self):
        window1.show()
        self.close()

    def AddUser(self):
        def fa_to_en(text):
            fa_digits = '۰۱۲۳۴۵۶۷۸۹'
            en_digits = '0123456789'
            return text.translate(str.maketrans(fa_digits, en_digits))

        fullname = self.fullnamelineedit.text()
        password = fa_to_en(self.passwordlineedit.text())
        repeat = fa_to_en(self.repeatlineedit.text())
        phone = fa_to_en(self.phonelineedit.text())
        alluser = dbfunctions.check_user()

        if all([fullname, password, repeat, phone]):
            if re.fullmatch(r'^(09[0-9]{9})$', phone):
                if len(password) >= 6:
                    if not re.fullmatch(r'[A-Za-z0-9@#$%^&+=!]{6,}', password):
                        self.errorlabel.setText('رمز عبور باید فقط شامل حروف و اعداد انگلیسی باشد')
                        return
                    if password == repeat:
                        for user in alluser:
                            if user['phone'] == phone:
                                self.errorlabel.setText('کاربری با این شماره موبایل از قبل موجود است')
                                return
                            
                        self.pending_user = {
                            'fullname': fullname,
                            'password': password,
                            'phone': phone
                        }
                        window4.set_otp(self)
                        window4.show()
                        self.close()
                    else:
                        self.errorlabel.setText('رمز عبور با تکرار آن مطابقت ندارد')
                else:
                    self.errorlabel.setText('رمز عبور باید حداقل ۶ کاراکتر باشد')
            else:
                self.errorlabel.setText('شماره موبایل معتبر نیست')
        else:
            self.errorlabel.setText('لطفاً همه فیلدها را پر کنید')


class OtpPage(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('./ui/otppage.ui', self)

        self.generated_code = None
        self.signup_page = None
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer)
        self.remaining_seconds = 0

        self.confirmbutton.clicked.connect(self.verify_code)
        self.resendbutton.clicked.connect(self.resend_code)
        self.backbutton.clicked.connect(self.go_back)

    def fa_to_en(self, text):
        fa_digits = '۰۱۲۳۴۵۶۷۸۹'
        en_digits = '0123456789'
        return text.translate(str.maketrans(fa_digits, en_digits))

    def set_otp(self, signup_page):
        self.signup_page = signup_page
        self.send_new_code()
        self.start_resend_timer()

    def send_new_code(self):
        self.generated_code = str(random.randint(1000, 9999))
        self.generated_time = datetime.now()
        phone = self.signup_page.phonelineedit.text()
        success = send_sms(phone, self.generated_code)

        if success:
            self.messageLabel.setText("کد تایید برای شما ارسال شد. لطفا آن را وارد نمایید")
        else:
            self.messageLabel.setText(" ارسال ناموفق بود ")

    def start_resend_timer(self):
        self.resendbutton.setEnabled(False)
        self.remaining_seconds = 120
        self.resendbutton.setText(f"ارسال مجدد ({self.remaining_seconds})")
        self.timer.start()

    def update_timer(self):
        self.remaining_seconds -= 1
        if self.remaining_seconds > 0:
            self.resendbutton.setText(f"ارسال مجدد ({self.remaining_seconds})")
        else:
            self.timer.stop()
            self.resendbutton.setText("ارسال مجدد")
            self.resendbutton.setEnabled(True)

    def resend_code(self):
        self.send_new_code()
        self.start_resend_timer()

    def verify_code(self):
        entered = self.otplineedit.text().strip()
        entered = self.fa_to_en(entered)

        if datetime.now() - self.generated_time > timedelta(minutes=2):
            self.confirmbutton.setText("⏰ کد منقضی شده")
            return

        if entered == self.generated_code:
            user = self.signup_page.pending_user
            from dbfunctions import insert_user, get_user_id_by_phone

            insert_user(user['fullname'], user['password'], user['phone'])
            user_id = get_user_id_by_phone(user['phone'])
            # اطمینان از اینکه user_id مقدار عددی است
            if isinstance(user_id, (list, tuple)):
                user_id = user_id[0]
            try:
                user_id = int(user_id)
            except Exception:
                show_messagebox(self, "خطا", "شناسه کاربر نامعتبر است!", QMessageBox.Warning)
                return

            self.confirmbutton.setText("✅ تأیید شد")
            global window5
            window5 = WorkPage(user_id)
            window5.show()
            self.close()
        else:
            self.confirmbutton.setText("❌ کد نادرست")

    def go_back(self):
        window3.show()
        self.close()


class WorkPage(QWidget):
    def __init__(self, user_id):
        super().__init__()
        loadUi("./ui/workpage.ui", self)

        # اطمینان از اینکه user_id مقدار عددی معتبر است
        try:
            user_id = int(user_id)
        except Exception:
            show_messagebox(self, "خطا", "شناسه کاربر نامعتبر است!", QMessageBox.Warning)
            user_id = None

        fullname = get_user_fullname(user_id) if user_id is not None else "--"
        self.fullnamelabel.setText(f"سلام {fullname} عزیز!")

        self.ConfirmEventButton.clicked.connect(self.ShowIncomePage)
        self.AccountsButton.clicked.connect(self.ShowAccountsPage)
        self.FinancialReportButton.clicked.connect(self.ShowFinancialReportPage)

    def ShowIncomePage(self):
        global income_window
        income_window = AddEventPage()
        income_window.show()

    def ShowAccountsPage(self):
        global account_window
        account_window = AddAccountPage()
        account_window.show()

    def ShowFinancialReportPage(self):
        global report_window
        report_window = FinancialReportPage()
        report_window.show()


class AddEventPage(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('./ui/addevent.ui', self)

        today_jalali = jdatetime.date.today()
        formatted_date = today_jalali.strftime('%Y/%m/%d')
        self.dateLineEdit.setText(formatted_date)
        self.dateLineEdit.setPlaceholderText('مثال: ۱۴۰۴/۰۴/۲۵')

        self.typeComboBox.setEditable(False)
        self.categoryComboBox.setEditable(True)
        self.accountComboBox.setEditable(False)
        self.typeComboBox.addItems(['درآمد', 'هزینه'])

        self.typeComboBox.currentIndexChanged.connect(self.update_category_combo)
        self.ConfirmEventButton.clicked.connect(self.save_event)
        self.backbutton.clicked.connect(self.close)
        self.CostLineEdit.textChanged.connect(self.format_amount)

        self.update_category_combo()
        self.load_accounts()

    def fa_to_en(self, text):
        fa_digits = '۰۱۲۳۴۵۶۷۸۹'
        en_digits = '0123456789'
        return text.translate(str.maketrans(fa_digits, en_digits))

    def is_valid_jalali_date(self, date_str):
        try:
            y, m, d = map(int, date_str.split("/"))
            jdatetime.date(y, m, d)
            return True
        except:
            return False

    def format_amount(self, text):
        raw = self.fa_to_en(text).replace(",", "")
        if raw.isdigit():
            formatted = "{:,}".format(int(raw))
            cursor_pos = self.CostLineEdit.cursorPosition()
            self.CostLineEdit.blockSignals(True)
            self.CostLineEdit.setText(formatted)
            self.CostLineEdit.blockSignals(False)
            delta = len(formatted) - len(raw)
            self.CostLineEdit.setCursorPosition(cursor_pos + delta)

    def update_category_combo(self):
        selected_type = self.typeComboBox.currentText().strip()
        db_type = 'income' if selected_type == 'درآمد' else 'expense'

        self.categoryComboBox.clear()
        conn = dbfunctions.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories WHERE type = ?", (db_type,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.categoryComboBox.addItem(row[0])

    def load_accounts(self):
        self.accountComboBox.clear()
        conn = dbfunctions.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts")
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            self.accountComboBox.addItem(row[0])

    def save_event(self):
        amount = self.fa_to_en(self.CostLineEdit.text().replace(",", "").strip())
        type_value = self.typeComboBox.currentText().strip()
        category_name = self.categoryComboBox.currentText().strip()
        account_name = self.accountComboBox.currentText().strip()
        date_text = self.fa_to_en(self.dateLineEdit.text().strip())
        description = self.textEdit.toPlainText().strip()

        if not all([amount, type_value, category_name, account_name, date_text]):
            show_messagebox(self, 'خطا', 'لطفاً همه فیلدهای اجباری را پر کنید', QMessageBox.Warning)
            return

        if not self.is_valid_jalali_date(date_text):
            show_messagebox(self, 'خطا', 'فرمت تاریخ نامعتبر است. مانند: ۱۴۰۴/۰۴/۲۵', QMessageBox.Warning)
            return

        if not amount.isdigit():
            show_messagebox(self, 'خطا', 'مبلغ باید فقط شامل عدد باشد', QMessageBox.Warning)
            return

        db_type = 'income' if type_value == 'درآمد' else 'expense'

        conn = dbfunctions.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM categories WHERE name = ? AND type = ?", (category_name, db_type))
        result = cursor.fetchone()
        category_id = result[0] if result else cursor.execute(
            "INSERT INTO categories (name, type) VALUES (?, ?)", (category_name, db_type)
        ).lastrowid

        cursor.execute("SELECT id FROM accounts WHERE name = ?", (account_name,))
        result = cursor.fetchone()
        account_id = result[0] if result else cursor.execute(
            "INSERT INTO accounts (name) VALUES (?)", (account_name,)
        ).lastrowid

        cursor.execute("""
            INSERT INTO transactions (amount, date, category_id, account_id, description)
            VALUES (?, ?, ?, ?, ?)
        """, (amount, date_text, category_id, account_id, description))

        conn.commit()
        conn.close()

        show_messagebox(self, 'ثبت شد', '✅ رویداد با موفقیت ثبت شد', QMessageBox.Information)
        self.close()


class AddAccountPage(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("./ui/addaccount.ui", self)

        self.addButton.clicked.connect(self.add_account)
        self.deleteButton.clicked.connect(self.delete_account)
        self.backbutton.clicked.connect(self.close)

        self.load_accounts()

    def load_accounts(self):
        self.accountListWidget.clear()
        conn = dbfunctions.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            item = QListWidgetItem(row[0])
            item.setTextAlignment(Qt.AlignRight)
            self.accountListWidget.addItem(item)

    def add_account(self):
        name = self.accountLineEdit.text().strip()
        if not name:
            show_messagebox(self, "⚠️ خطا", "لطفاً نام حساب را وارد کنید", QMessageBox.Warning)
            return

        conn = dbfunctions.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM accounts WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result:
            show_messagebox(self, "ℹ️", "این حساب قبلاً ثبت شده است", QMessageBox.Information)
        else:
            cursor.execute("INSERT INTO accounts (name) VALUES (?)", (name,))
            conn.commit()
            show_messagebox(self, "✅ ثبت شد", "حساب جدید با موفقیت اضافه شد", QMessageBox.Information)
            self.accountLineEdit.clear()
            self.load_accounts()

        conn.close()

    def delete_account(self):
        selected_item = self.accountListWidget.currentItem()
        if not selected_item:
            show_messagebox(self, "⚠️ خطا", "لطفاً یک حساب را برای حذف انتخاب کنید", QMessageBox.Warning)
            return

        account_name = selected_item.text()

        conn = dbfunctions.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM transactions
            WHERE account_id IN (
                SELECT id FROM accounts WHERE name = ?
            )
        """, (account_name,))
        count = cursor.fetchone()[0]

        if count > 0:
            show_messagebox(self, "⛔ امکان حذف نیست", "این حساب در تراکنش‌ها استفاده شده و قابل حذف نیست", QMessageBox.Warning)
        else:
            cursor.execute("DELETE FROM accounts WHERE name = ?", (account_name,))
            conn.commit()
            show_messagebox(self, "🗑️ حذف شد", "حساب با موفقیت حذف شد", QMessageBox.Information)
            self.load_accounts()

        conn.close()


class FinancialReportPage(QWidget):
    def __init__(self):
        super().__init__()
        loadUi('./ui/financialreport.ui', self)

        self.setLayoutDirection(Qt.RightToLeft)
        self.fromLineEdit.setPlaceholderText("مثال: ۱۴۰۴/۰۴/۰۱")
        self.toLineEdit.setPlaceholderText("مثال: ۱۴۰۴/۰۴/۳۰")
        self.exportToExcelButton.clicked.connect(self.export_to_excel)

        self.generateReportButton.clicked.connect(self.generate_report)
        self.backButton.clicked.connect(self.close)

        self.expenseChartLayout = QVBoxLayout(self.expenseChartContainer)
        self.incomeChartLayout = QVBoxLayout(self.incomeChartContainer)

    def fa_to_en(self, text):
        fa_digits = '۰۱۲۳۴۵۶۷۸۹'
        en_digits = '0123456789'
        return text.translate(str.maketrans(fa_digits, en_digits))

    def is_valid_jalali_date(self, date_str):
        try:
            y, m, d = map(int, date_str.split("/"))
            jdatetime.date(y, m, d)
            return True
        except:
            return False

    def convert_type_to_farsi(self, type_en):
        return "درآمد" if type_en == "income" else "هزینه"

    def generate_report(self):
        from_date = self.fa_to_en(self.fromLineEdit.text().strip())
        to_date = self.fa_to_en(self.toLineEdit.text().strip())

        if not from_date or not to_date:
            show_messagebox(self, "⚠️ خطا", "لطفاً بازه زمانی را کامل وارد کنید", QMessageBox.Warning)
            return

        if not self.is_valid_jalali_date(from_date) or not self.is_valid_jalali_date(to_date):
            show_messagebox(self, "⚠️ خطا", "تاریخ واردشده معتبر نیست. لطفاً مانند ۱۴۰۴/۰۴/۲۵ وارد کنید", QMessageBox.Warning)
            return

        conn = dbfunctions.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT SUM(t.amount)
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.type = 'income' AND t.date BETWEEN ? AND ?
        """, (from_date, to_date))
        income = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT SUM(t.amount)
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE c.type = 'expense' AND t.date BETWEEN ? AND ?
        """, (from_date, to_date))
        expense = cursor.fetchone()[0] or 0

        self.totalIncomeLabel.setText(f"{income:,} ریال")
        self.totalExpenseLabel.setText(f"{expense:,} ریال")
        self.netBalanceLabel.setText(f"{(income - expense):,} ریال")

        cursor.execute("""
            SELECT c.name, c.type, t.amount, t.date
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.date BETWEEN ? AND ?
            ORDER BY t.date ASC
        """, (from_date, to_date))
        rows = cursor.fetchall()
        self.categoryTable.setRowCount(len(rows))
        self.categoryTable.setColumnCount(4)
        self.categoryTable.setHorizontalHeaderLabels(["دسته", "نوع", "مبلغ", "تاریخ"])

        for i, (cat, typ, amt, date_str) in enumerate(rows):
            type_fa = self.convert_type_to_farsi(typ)
            amount_text = f"{amt:,} ریال"
            if typ == "expense":
                amount_text = f"({amount_text})"

            self.categoryTable.setItem(i, 0, QTableWidgetItem(cat))
            self.categoryTable.setItem(i, 1, QTableWidgetItem(type_fa))
            self.categoryTable.setItem(i, 2, QTableWidgetItem(amount_text))
            self.categoryTable.setItem(i, 3, QTableWidgetItem(date_str))
            for j in range(4):
                self.categoryTable.item(i, j).setTextAlignment(Qt.AlignCenter)

        cursor.execute("""
            SELECT a.name,
                   SUM(CASE WHEN c.type = 'expense' THEN -t.amount ELSE t.amount END)
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN categories c ON t.category_id = c.id
            WHERE t.date BETWEEN ? AND ?
            GROUP BY a.name
        """, (from_date, to_date))
        rows = cursor.fetchall()
        self.accountTable.setRowCount(len(rows))
        self.accountTable.setColumnCount(2)
        self.accountTable.setHorizontalHeaderLabels(["حساب", "موجودی"])

        for i, (acc, amt) in enumerate(rows):
            amount_text = f"{abs(amt):,} ریال"
            if amt < 0:
                amount_text = f"({amount_text})"
            self.accountTable.setItem(i, 0, QTableWidgetItem(acc))
            self.accountTable.setItem(i, 1, QTableWidgetItem(amount_text))
            for j in range(2):
                self.accountTable.item(i, j).setTextAlignment(Qt.AlignCenter)

        conn.close()
        self.show_expense_chart()
        self.show_income_chart()

    def show_expense_chart(self):
        while self.expenseChartLayout.count():
            child = self.expenseChartLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        data = {}
        for i in range(self.categoryTable.rowCount()):
            if self.categoryTable.item(i, 1).text() == "هزینه":
                cat = self.categoryTable.item(i, 0).text()
                amt_text = self.categoryTable.item(i, 2).text()
                amt_text = amt_text.replace("ریال", "").replace(",", "").replace("(", "").replace(")", "").strip()
                try:
                    amt = int(amt_text)
                    data[cat] = data.get(cat, 0) + amt
                except:
                    pass

        if not data:
            label = QLabel("هیچ هزینه‌ای برای نمایش در نمودار نیست")
            label.setAlignment(Qt.AlignCenter)
            self.expenseChartLayout.addWidget(label)
            return

        series = QPieSeries()
        for cat, amt in data.items():
            series.append(cat, amt)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignRight)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(150)
        self.expenseChartLayout.addWidget(chart_view)

    def show_income_chart(self):
        while self.incomeChartLayout.count():
            child = self.incomeChartLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        data = {}
        for i in range(self.categoryTable.rowCount()):
            if self.categoryTable.item(i, 1).text() == "درآمد":
                cat = self.categoryTable.item(i, 0).text()
                amt_text = self.categoryTable.item(i, 2).text()
                amt_text = amt_text.replace("ریال", "").replace(",", "").replace("(", "").replace(")", "").strip()
                try:
                    amt = int(amt_text)
                    data[cat] = data.get(cat, 0) + amt
                except:
                    pass

        if not data:
            label = QLabel("هیچ درآمدی برای نمایش در نمودار نیست")
            label.setAlignment(Qt.AlignCenter)
            self.incomeChartLayout.addWidget(label)
            return

        series = QPieSeries()
        for cat, amt in data.items():
            series.append(cat, amt)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignRight)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(150)
        self.incomeChartLayout.addWidget(chart_view)

    def export_to_excel(self):
        print("✅ دکمه خروجی اکسل کلیک شد!")

        try:
            if self.categoryTable.rowCount() == 0:
                show_messagebox(self, "⚠️ هشدار", "ابتدا گزارش‌گیری کنید تا داده‌ها برای خروجی آماده شوند.", QMessageBox.Warning)
                return

            # ساخت اکسل و شیت
            wb = Workbook()
            ws = wb.active
            ws.title = "گزارش دسته‌بندی"
            ws.sheet_view.rightToLeft = True  # ساختار راست‌چین

            # فونت BNazanin (باید روی سیستم نصب باشه)
            bnazanin_font = Font(name="BNazanin", size=12)

            # عنوان‌ها
            header = ["دسته", "نوع", "مبلغ", "تاریخ"]
            ws.append(header)
            for cell in ws[1]:
                cell.alignment = Alignment(horizontal="center")
                cell.font = bnazanin_font

            # داده‌ها
            for row in range(self.categoryTable.rowCount()):
                cat = self.categoryTable.item(row, 0).text()
                typ = self.categoryTable.item(row, 1).text()
                amt_text = self.categoryTable.item(row, 2).text()
                date_str = self.categoryTable.item(row, 3).text()

                # پاک‌سازی مبلغ: حذف «ریال»، پرانتز و تبدیل به عدد
                amt_clean = amt_text.replace("ریال", "").replace(",", "").replace("(", "").replace(")", "").strip()
                try:
                    amount_value = int(amt_clean)
                    if typ == "هزینه":
                        amount_value = -abs(amount_value)
                    else:
                        amount_value = abs(amount_value)
                except:
                    amount_value = amt_clean  # fallback

                # اضافه به اکسل
                ws.append([cat, typ, amount_value, date_str])

            # وسط‌چینی و فونت داده‌ها
            for data_row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                for cell in data_row:
                    cell.alignment = Alignment(horizontal="center")
                    cell.font = bnazanin_font

            # تنظیم عرض ستون‌ها
            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max_length + 3

            # مسیر و نام فایل امن
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            from_date_raw = self.fromLineEdit.text().strip()
            to_date_raw = self.toLineEdit.text().strip()
            from_date = self.fa_to_en(from_date_raw).replace("/", "-")
            to_date = self.fa_to_en(to_date_raw).replace("/", "-")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"گزارش مالی_{from_date}_تا_{to_date}_{timestamp}.xlsx"
            full_path = os.path.join(desktop_path, filename)

            # ذخیره فایل
            wb.save(full_path)

            # پیام موفقیت و باز کردن فایل
            show_messagebox(self, "✅ موفقیت", f"فایل اکسل با موفقیت روی دسکتاپ ذخیره شد:\n{full_path}", QMessageBox.Information)

            if os.name == "posix":
                subprocess.call(["open", full_path])
            elif os.name == "nt":
                os.startfile(full_path)

        except Exception as e:
            print("❌ خطا:", str(e))
            show_messagebox(self, "❌ خطا", f"خطا در ذخیره فایل اکسل:\n{str(e)}", QMessageBox.Critical)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    global window1, window2, window3, window4, window5
    window1 = Main()
    window2 = SignInPage()
    window3 = SignUpPage()
    window4 = OtpPage()
    window1.show()
    sys.exit(app.exec())
    