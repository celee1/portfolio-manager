from PyQt5.QtWidgets import QApplication, QGridLayout, QAction, QLabel, QFrame, QMainWindow, QPushButton, QWidget, QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QBrush, QColor, QCursor
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
from requests.exceptions import ConnectionError
from sqlite3 import OperationalError
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import string
import json
import sys
import key

# dodat stupac price per item? Lako podijelit cijenu s kolicinom i to je to


matplotlib.use('Qt5Agg')


class PortfolioManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.db = sqlite3.connect(
            r"C:\Users\celes\OneDrive\Documents\Python_3.10\Projects\App_projects\portfolio_updater\portfolio.db")
        self.cursor = self.db.cursor()

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Portfolio Manager')
        self.setStyleSheet('background: #000000')

        # menu bar

        self.menu_bar = self.menuBar()
        self.menu_bar.setStyleSheet("color: #1eecc9")

        self.statusBar()

        summary_menu = self.menu_bar.addMenu('&Summary')

        summary_action = QAction(text='View summary', parent=self)
        summary_action.setStatusTip('View the summary of the portfolio')
        summary_action.triggered.connect(self.view_summary)
        summary_action.setShortcut('Ctrl+S')
        summary_menu.addAction(summary_action)

        transaction_menu = self.menu_bar.addMenu('&Transactions')

        transaction_action = QAction(
            text='Insert a transaction', parent=self)
        transaction_action.setStatusTip(
            'Insert a transaction with a new or an existing coin')
        transaction_action.triggered.connect(self.make_transaction)
        transaction_action.setShortcut('Ctrl+T')
        transaction_menu.addAction(transaction_action)

        show_transactions_action = QAction(
            text='Show transactions', parent=self)
        show_transactions_action.setStatusTip(
            'Show a table of all existing transactions')
        show_transactions_action.triggered.connect(self.show_transactions)
        show_transactions_action.setShortcut('Ctrl+D')
        transaction_menu.addAction(show_transactions_action)

        staking_menu = self.menu_bar.addMenu('&Staking')

        staking_action = QAction(
            text='Staking overview', parent=self)
        staking_action.setStatusTip(
            'See an overview of staking rewards per month')
        staking_action.setShortcut('Ctrl+O')
        staking_action.triggered.connect(self.open_staking)
        staking_menu.addAction(staking_action)

        staking_update_action = QAction(
            text='Update staking information', parent=self)
        staking_update_action.setStatusTip(
            'Update staked coin information')
        staking_update_action.setShortcut('Ctrl+U')
        staking_update_action.triggered.connect(self.update_staking)
        staking_menu.addAction(staking_update_action)

        loss_debt_menu = self.menu_bar.addMenu('&Loss and debt')

        loss_action = QAction('&Loss', self)
        loss_action.setStatusTip('View realised losses')
        loss_action.triggered.connect(self.view_losses)
        loss_debt_menu.addAction(loss_action)

        debt_action = QAction('&Debt', self)
        debt_action.setStatusTip('View existing debts')
        debt_action.triggered.connect(self.view_debts)
        loss_debt_menu.addAction(debt_action)

        graphs_menu = self.menu_bar.addMenu('&Graphs')
        graph_action = QAction('&Open graph', self)
        graph_action.setStatusTip('View historical daily data')
        graph_action.triggered.connect(self.open_graphs)
        graphs_menu.addAction(graph_action)

        top_x_menu = self.menu_bar.addMenu('&Top X cryptos')

        top_x_Action = QAction('&Top x cryptos', self)
        top_x_Action.setShortcut('Ctrl+X')
        top_x_Action.setStatusTip('Show a X number of top rated cryptos')
        top_x_Action.triggered.connect(self.show_x_cryptos)
        top_x_menu.addAction(top_x_Action)

        exit_menu = self.menu_bar.addMenu('&Exit')

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Close the app')
        exitAction.triggered.connect(self.close)
        exit_menu.addAction(exitAction)

        # central widget

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.show()

        self.grid = QGridLayout(self.central_widget)

        self.label1 = CentralLabel('Portfolio Manager')
        self.grid.addWidget(self.label1, 0, 0, 1, 3)

        self.asset_classes_button = PushButton(
            'Crypto information', action=self.open_assets)
        self.grid.addWidget(self.asset_classes_button, 1, 2)

        self.check_crypto_button = PushButton(
            'Check crypto', action=self.check_crypto)
        self.grid.addWidget(self.check_crypto_button, 1, 0)

    def get_column_names(self, table_name):
        columns = w.cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE name='{table_name}';").fetchall()[0][0]

        first_sections = columns.split(f'"{table_name}"')[
            1].split('PRIMARY KEY')[0]

        upper = string.ascii_uppercase
        other = ['', ' ', '(', ')', '\n', '\t', '"']

        almost_done = [
            item for item in first_sections if item not in upper and item not in other]

        return [item for item in ''.join(
            almost_done).split(',') if item != '']

    def show_table(self, table_name='overview'):
        columns = self.get_column_names(table_name)

        try:
            content = w.cursor.execute(
                f'SELECT * FROM {table_name}').fetchall()

        except OperationalError:
            msg = QMessageBox(QMessageBox.Warning,
                              'Error with columns', f'Columns: {columns}')
            msg.exec_()

        try:
            not_checked = [coin[0] for coin in self.cursor.execute(
                'SELECT * FROM not_checked').fetchall()]
            table = QTableWidget(len(content), len(content[0]), self)
            for i in range(len(content)):
                for j in range(len(content[0])):
                    item = QTableWidgetItem(content[i][j])
                    if j != len(content[0]) - 1:
                        if content[i][0] in not_checked:
                            item.setForeground(QBrush(QColor("#ff0000")))
                        else:
                            item.setForeground(QBrush(QColor("#1eecc9")))
                    else:
                        if float(content[i][j]) < 0:
                            item.setForeground(QBrush(QColor("#ff0000")))
                        elif float(content[i][j]) == 0:
                            item.setForeground(QBrush(QColor("#FFFF00")))
                        else:
                            item.setForeground(QBrush(QColor("#1eecc9")))

                    table.setItem(i, j, item)

            table.setHorizontalHeaderLabels(columns)

            return table

        except IndexError:
            msg = QMessageBox(QMessageBox.Warning, 'Table empty',
                              'Table empty, cannot show data')
            msg.exec_()

        return QTableWidget(0, 0, self)

    def show_graph(self, table_name='overview', amount='amount', asset='asset'):
        query = w.cursor.execute(
            f'SELECT {asset}, {amount} FROM "{table_name}"').fetchall()

        assets = [item[0] for item in query]
        try:
            amounts = [float(item[1]) for item in query]
        except ValueError:
            return False

        sc = MplCanvasPie(self, width=5, height=4, dpi=100)
        return [sc, amounts, assets, table_name.upper()]

    def check_crypto(self):
        self.checker = CoinChecker(w.cursor, w.db)
        if self.checker.checked:
            self.checker.update_staking()
            self.checker.update_crypto()
            self.checker.update_total_value_crypto()
            self.checker.update_perc_profit_loss_column()

    def open_assets(self):
        self.assets = AssetWindow()
        self.assets.show()

    def open_staking(self):
        self.staking = StakingWindow()
        self.staking.show()

    def make_transaction(self):
        self.transactions = TransactionWindow()
        self.transactions.show()

    def update_staking(self):
        self.update_staking_window = StakingUpdate()
        self.update_staking_window.show()

    def view_losses(self):
        self.debt_loss = DebtLossWindow('loss')
        self.debt_loss.show()

    def view_debts(self):
        self.debt_loss = DebtLossWindow('debt')
        self.debt_loss.show()

    def view_summary(self):
        self.summary = SummaryWindow()
        self.summary.show()

    def show_transactions(self):
        self.transactions_records = ShowTransactionsWindow()
        self.transactions_records.show()

    def open_graphs(self):
        self.graph_window = GraphWindow()
        self.graph_window.show()

    def show_x_cryptos(self):
        self.new_window = ShowCryptos()
        self.new_window.show()


class CoinChecker:
    def __init__(self, cursor, database):

        self.cursor = cursor
        self.database = database

        api_key = key.api_key
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
            'start': '1',
            'limit': '5000',
            'convert': 'EUR'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }

        try:
            response = requests.get(url, params=parameters, headers=headers)
            data = json.loads(response.text)['data']

            coin_info = {}
            not_checked = []

            coins = cursor.execute(
                'SELECT name, amount FROM crypto WHERE name != "crypto20" ORDER BY ticker;').fetchall()

            for coin in coins:
                coin_info[coin[0]] = float(coin[1])
                not_checked.append(coin[0])

            w.cursor.execute('DELETE FROM not_checked')

            for item in data:
                if item['name'].lower() in coin_info.keys():
                    name = item['name'].lower()
                    price = round(float(item['quote']['EUR']['price']), 4)
                    amount = round(coin_info[name] * price, 2)
                    cursor.execute(
                        f'UPDATE crypto SET current_value = "{amount}", current_price = "{price}" WHERE name = "{name}";')
                    cursor.execute(
                        f'UPDATE staking SET current_price = "{price}" WHERE name = "{name}";')
                    not_checked.remove(name)

            [w.cursor.execute(
                f'INSERT INTO not_checked VALUES ("{coin}");') for coin in not_checked]

            database.commit()

            self.checked = True

        except (KeyError, ConnectionError):
            msg = QMessageBox(QMessageBox.Warning, 'Error',
                              'Data could not be fetched')
            msg.exec_()

            self.checked = False

    def update_staking(self):

        cursor = self.cursor
        database = self.database

        staking_info = cursor.execute(
            'SELECT ticker, amount, apy, current_price FROM staking').fetchall()

        updated_values = [
            [round(float(item[3]) * float(item[1]) / 100 * float(item[2]) / 12, 3), item[0]] for item in staking_info]

        # formula = current value * amount / 100 * apy / 12 -- staking yield calculation

        for value in updated_values:
            cursor.execute(
                f'UPDATE staking set yield = {value[0]} WHERE ticker = "{value[1]}"')
        database.commit()

    def update_crypto(self):
        cursor = self.cursor
        database = self.database

        coins = cursor.execute(
            'SELECT DISTINCT(ticker), SUM(amount), SUM(amount_invested), coin FROM transactions GROUP BY ticker;').fetchall()

        amounts = [item[1] for item in coins]

        if '0' in amounts or 0 in amounts:
            for coin in coins:
                if float(coin[1]) == 0:
                    print(coin)
                    cursor.execute(
                        f'DELETE FROM transactions WHERE ticker = "{coin[0]}";')
                    loss = cursor.execute(
                        'SELECT amount FROM loss_debt WHERE type="loss";').fetchall()[0][0]
                    cursor.execute(
                        f'UPDATE loss_debt SET amount = "{float(loss) + coin[2]}" WHERE type = "loss";')

                    cursor.execute(
                        f'DELETE FROM crypto WHERE ticker = "{coin[0]}";')

                    database.commit()

        coins = cursor.execute(
            'SELECT DISTINCT(ticker), SUM(amount), SUM(amount_invested), coin FROM transactions GROUP BY ticker;').fetchall()

        coin_present = [item[0] for item in cursor.execute(
            'SELECT DISTINCT(ticker) FROM crypto;').fetchall()]

        for coin in coins:
            if coin[0] in coin_present:
                cursor.execute(
                    f'UPDATE crypto SET amount = "{round(coin[1], 4)}", amount_invested = "{round(coin[2], 4)}", dca_price = "{round(coin[2] / coin[1], 4)}" WHERE ticker = "{coin[0]}";')
            else:
                cursor.execute(
                    f'INSERT INTO crypto VALUES ("{coin[3]}", "{coin[0]}", "{round(coin[1], 4)}", "{round(coin[2], 4)}", "{round(coin[2], 4)}", "{round(coin[2] / coin[1], 4)}", "0", "0");')
        database.commit()

    def update_total_value_crypto(self):
        cursor = self.cursor
        database = self.database
        date = datetime.now().strftime('%Y/%m/%d, %H:%M:%S')

        current_value, amount_invested = cursor.execute(
            'SELECT ROUND(SUM(current_value), 4), ROUND(SUM(amount_invested), 4) FROM crypto').fetchall()[0]

        try:
            perc_profit = round(
                (current_value - amount_invested) / amount_invested * 100, 4)

        except ZeroDivisionError:
            perc_profit = 0

        cursor.execute(
            f'INSERT INTO total_value_crypto VALUES ("{current_value}", "{date}", "{perc_profit}");')
        database.commit()

    def update_perc_profit_loss_column(self):
        price = self.cursor.execute(
            'SELECT dca_price, current_price, ticker FROM crypto').fetchall()

        for item in price:
            try:
                ratio = float(item[1]) / float(item[0]) * 100
                if ratio > 1:
                    ratio = (ratio - 100)
                elif ratio < 1:
                    ratio = -(100 - ratio)
                else:
                    ratio = 100
                self.cursor.execute(
                    f'UPDATE crypto SET profit_loss = "{round(ratio, 2)}" WHERE ticker = "{item[2]}";')

            except ZeroDivisionError:
                pass

        self.database.commit()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MplCanvasPie(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvasPie, self).__init__(fig)

    def show_overview(self, amounts, assets, table_name='overview', table_title='overview'):
        def func(pct, allvals):
            absolute = int(np.round(pct/100.*np.sum(allvals)))
            return "{:.1f}%\n({:d} €)".format(pct, absolute)

        wedges, texts, autotexts = self.axes.pie(amounts, autopct=lambda pct: func(pct, amounts),
                                                 textprops=dict(color="w"))

        self.axes.legend(wedges, assets,
                         title=table_title,
                         loc="lower right",
                         bbox_to_anchor=(0.63, 0, 0.5, 0.5))

        plt.setp(autotexts, size=8, weight="bold")

        self.axes.set_title(table_name)

        self.show()


class AssetWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 1000, 1000)

        self.setWindowTitle('Asset class tables')
        self.setStyleSheet('background: #000000')
        self.showMaximized()

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.frame_2 = QFrame(self)

        self.grid.addWidget(self.frame_1, 0, 0)
        self.grid.addWidget(self.frame_2, 1, 0)

        self.grid_1 = QGridLayout(self.frame_1)
        self.grid_2 = QGridLayout(self.frame_2)

        self.label_1 = CentralLabel('Assets')
        self.grid_1.addWidget(self.label_1, 0, 0, 1, 2)

        self.close_button = PushButton('close window', 500, self.close)
        self.grid_2.addWidget(self.close_button, 5, 1)

        self.make_table()
        self.make_graph()

    def make_table(self):
        table = w.show_table(table_name='crypto')
        self.grid_1.addWidget(table, 1, 1, 2, 1)
        table.setMaximumWidth(1000)
        table.setMaximumHeight(500)
        table.show()

    def make_graph(self):

        self.db = sqlite3.connect(
            r"C:\Users\celes\OneDrive\Documents\Python_3.10\Projects\App_projects\portfolio_updater\portfolio.db")
        self.cursor = self.db.cursor()

        self.canvas = MplCanvas(self)

        info = [item for item in self.cursor.execute(
            f'SELECT value, date FROM total_value_crypto').fetchall()]
        value = [float(item[0]) for item in info]
        date = pd.to_datetime([item[1] for item in info])

        self.canvas.axes.plot(date, value)
        self.canvas.setMaximumHeight(500)
        self.grid_1.addWidget(self.canvas, 1, 0)
        self.canvas.show()

        graph = w.show_graph(table_name='crypto',
                             amount='current_value', asset='ticker')
        graph[0].setMaximumWidth(600)
        self.grid_1.addWidget(graph[0], 2, 0)
        cryptos = sum([float(item[0]) for item in w.cursor.execute(
            'SELECT current_value FROM crypto').fetchall()])
        graph[0].show_overview(
            graph[1], graph[2], f'{graph[3]}: {round(cryptos, 2)} € total value', 'cryptos')


class StakingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1000, 900)
        self.setWindowTitle('Staking information')
        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.grid.addWidget(self.frame_1, 0, 0)
        self.grid_1 = QGridLayout(self.frame_1)

        self.frame_2 = QFrame(self)
        self.grid.addWidget(self.frame_2, 1, 0)
        self.grid_2 = QGridLayout(self.frame_2)

        self.label_1 = Label('Staking overview', 400)
        self.grid_1.addWidget(self.label_1, 0, 0)

        self.label_2 = Label('Yields in EUR per month')
        self.grid_2.addWidget(self.label_2, 0, 0)

        self.label_3 = Label('APY rates per coin')
        self.grid_2.addWidget(self.label_3, 0, 1)

        self.show_info()

    def show_info(self):
        self.make_graph()
        self.show_apy()

    def make_graph(self):
        graph = w.show_graph(table_name='staking',
                             amount='yield', asset='ticker')
        self.grid_2.addWidget(graph[0], 1, 0)
        total_staking = sum([float(item[0]) for item in w.cursor.execute(
            'SELECT yield FROM staking').fetchall()])
        graph[0].show_overview(
            graph[1], graph[2], f'{graph[3]}: {round(total_staking, 2)} € per month', 'staking')

    def show_apy(self):
        self.canvas = MplCanvas(self)
        info = [item for item in w.cursor.execute(
            'SELECT ticker, apy FROM staking').fetchall()]
        ticker = [item[0] for item in info]
        apy = [float(item[1]) for item in info]
        self.canvas.axes.bar(ticker, apy)
        self.grid_2.addWidget(self.canvas, 1, 1)
        self.canvas.show()


class StakingUpdate(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1000, 900)
        self.setWindowTitle('Update staking information')
        self.setStyleSheet('background: #000000')

        self.grid_basic = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.grid_basic.addWidget(self.frame_1, 0, 0)

        self.grid_1 = QGridLayout(self.frame_1)

        self.main_label = CentralLabel('Update staking information')

        self.grid_1.addWidget(self.main_label, 0, 0)

        self.frame_2 = QFrame(self)
        self.grid_basic.addWidget(self.frame_2)

        self.grid = QGridLayout(self.frame_2)

        self.label_1 = Label('ticker', 400)
        self.grid.addWidget(self.label_1, 0, 0)

        self.edit_1 = LineEdit(400)
        self.grid.addWidget(self.edit_1, 0, 1)

        self.label_2 = Label('amount', 400)
        self.grid.addWidget(self.label_2, 1, 0)

        self.edit_2 = LineEdit(400)
        self.grid.addWidget(self.edit_2, 1, 1)

        self.label_3 = Label('apy', 400)
        self.grid.addWidget(self.label_3, 2, 0)

        self.edit_3 = LineEdit(400)
        self.grid.addWidget(self.edit_3, 2, 1)

        self.label_4 = Label('service_provider', 400)
        self.grid.addWidget(self.label_4, 3, 0)

        self.edit_4 = LineEdit(400)
        self.grid.addWidget(self.edit_4, 3, 1)

        self.label_5 = Label('yield', 400)
        self.grid.addWidget(self.label_5, 4, 0)

        self.edit_5 = LineEdit(400)
        self.grid.addWidget(self.edit_5, 4, 1)

        self.frame_3 = QFrame(self)
        self.grid_basic.addWidget(self.frame_3, 2, 0)
        self.grid_2 = QGridLayout(self.frame_3)

        self.button_1 = PushButton(
            'update staking', 300, self.update_existing_stake)
        self.grid_2.addWidget(self.button_1, 0, 0)

        self.button_2 = PushButton(
            'insert staking', 300, self.insert_new_stake)
        self.grid_2.addWidget(self.button_2, 0, 1)

        self.edit_1.setFocus()

    def insert_new_stake(self):
        w.cursor.execute(
            f'INSERT INTO staking VALUES ("{self.edit_1.text()}", "{self.edit_2.text()}", "{self.edit_3.text()}", "{self.edit_4.text()}", "{self.edit_5.text()}");')
        w.db.commit()

        [item.setText('')
         for item in self.children() if type(item) == LineEdit]
        CoinChecker(w.cursor, w.db).update_staking()

    def update_existing_stake(self):
        staking_info = [self.edit_1.text(), self.edit_2.text(
        ), self.edit_3.text(), self.edit_4.text(), self.edit_5.text()]
        existing_info = w.cursor.execute(
            f'SELECT * FROM staking WHERE ticker = "{self.edit_1.text()}";').fetchall()
        if staking_info[0] == '':
            msg = QMessageBox(QMessageBox.Warning, 'Ticker cannot be empty',
                              'Empty ticker, please fill in the ticker box')
            msg.exec_()
            return
        for i in range(len(staking_info)):
            if staking_info[i] == '':
                staking_info[i] = existing_info[0][i]

        w.cursor.execute(
            f'UPDATE staking SET amount = "{staking_info[1]}", apy = "{staking_info[2]}", service_provider = "{staking_info[3]}", yield = "{staking_info[4]}" WHERE ticker = "{staking_info[0]}"')
        w.db.commit()
        [item.setText('')
         for item in self.children() if type(item) == LineEdit]
        CoinChecker(w.cursor, w.db).update_staking()


class TransactionWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Transactions window')
        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)

        self.grid.addWidget(Label('coin'), 0, 0)

        self.edit_1 = LineEdit(300)
        self.grid.addWidget(self.edit_1, 0, 1)

        self.grid.addWidget(Label('ticker'), 1, 0)

        self.edit_2 = LineEdit(300)
        self.grid.addWidget(self.edit_2, 1, 1)

        self.grid.addWidget(Label('amount'), 2, 0)

        self.edit_3 = LineEdit(300)
        self.grid.addWidget(self.edit_3, 2, 1)

        self.grid.addWidget(Label('amount_invested'), 3, 0)

        self.edit_4 = LineEdit(300)
        self.grid.addWidget(self.edit_4, 3, 1)

        self.close_button = PushButton(
            'insert a transaction', 300, self.insert_a_transaction)
        self.grid.addWidget(self.close_button, 5, 2)

    def insert_a_transaction(self):
        texts = [self.edit_1.text().lower(), self.edit_2.text().upper(),
                 self.edit_3.text(), self.edit_4.text()]

        if '' in texts:
            msg = QMessageBox(
                QMessageBox.Warning, 'Incomplete input', 'Please fill out all the entries')
            msg.exec_()
            return

        try:
            float(texts[2])
            float(texts[3])

        except ValueError:
            msg = QMessageBox(QMessageBox.Warning, 'Entry invalid',
                              'Please use the correct number format with a decimal point')
            msg.exec_()
            return

        w.cursor.execute(
            f'INSERT INTO transactions VALUES ("{texts[0]}", "{texts[1]}", "{texts[2]}", "{texts[3]}");')
        w.db.commit()

        self.edit_1.setText('')
        self.edit_2.setText('')
        self.edit_3.setText('')
        self.edit_4.setText('')

        self.edit_1.setFocus()

        w.check_crypto()


class DebtLossWindow(QWidget):
    def __init__(self, mode):
        super().__init__()

        self.setGeometry(0, 0, 700, 400)

        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)

        self.mode = mode

        self.label_1 = Label(f'Existing {self.mode}:', 300)
        self.grid.addWidget(self.label_1, 0, 0)
        amount = w.cursor.execute(
            f'SELECT amount FROM loss_debt WHERE type = "{self.mode}"').fetchall()[0][0]
        self.label_2 = Label(amount, 300)
        self.grid.addWidget(self.label_2, 0, 1)

        self.edit_1 = LineEdit(300)
        self.grid.addWidget(self.edit_1, 1, 0)
        self.button_1 = PushButton('Change amount', 300, self.run_query)
        self.grid.addWidget(self.button_1, 1, 1)

    def run_query(self):
        w.cursor.execute(
            f'UPDATE loss_debt SET amount = "{self.edit_1.text()}" WHERE type = "{self.mode}"')
        w.db.commit()

        self.label_2.setText(self.edit_1.text())

        self.edit_1.setText('')
        self.edit_1.setFocus()


class SummaryWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 700, 400)

        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.grid_1 = QGridLayout(self.frame_1)

        self.grid.addWidget(self.frame_1, 0, 0)

        self.label_1 = Label('crypto', 300)
        self.grid_1.addWidget(self.label_1, 1, 0)
        self.label_2 = Label('loss', 300)
        self.grid_1.addWidget(self.label_2, 2, 0)
        self.label_3 = Label('debt', 300)
        self.grid_1.addWidget(self.label_3, 3, 0)

        self.label_4 = Label('amount', 300)
        self.grid_1.addWidget(self.label_4, 0, 1)
        self.label_5 = Label('amount_invested', 300)
        self.grid_1.addWidget(self.label_5, 0, 2)

        amount, amount_invested = w.cursor.execute(
            f'SELECT SUM(current_value), SUM(amount_invested) FROM crypto').fetchall()[0]

        self.label_6 = Label(str(round(amount, 2)), 300)
        self.grid_1.addWidget(self.label_6, 1, 1)

        self.label_7 = Label(str(round(amount_invested, 2)), 300)
        self.grid_1.addWidget(self.label_7, 1, 2)

        loss, debt = w.cursor.execute(
            f'SELECT amount FROM loss_debt').fetchall()

        loss = float(loss[0])
        debt = float(debt[0])

        self.label_8 = Label(str(round(loss, 2)), 300)
        self.grid_1.addWidget(self.label_8, 2, 2)

        self.label_9 = Label(str(round(debt, 2)), 300)
        self.grid_1.addWidget(self.label_9, 3, 1)

        self.label_10 = Label('total', 300)
        self.grid_1.addWidget(self.label_10, 4, 0)

        total_value = float(amount) - float(debt)
        self.label_11 = Label(str(round(total_value, 2)), 300)
        self.grid_1.addWidget(self.label_11, 4, 1)

        total_expenses = float(amount_invested) + loss
        self.label_11 = Label(str(round(total_expenses, 2)), 300)
        self.grid_1.addWidget(self.label_11, 4, 2)

        self.frame_2 = QFrame(self)
        self.frame_2.setStyleSheet('border: 2px solid #1eecc9')
        self.grid_2 = QGridLayout(self.frame_2)

        self.grid.addWidget(self.frame_2, 1, 0)

        self.label_12 = Label('net value', 300)
        self.grid_2.addWidget(self.label_12, 0, 0)

        abs_value = total_value - total_expenses
        self.label_13 = Label(str(round(abs_value, 2)), 300)
        self.grid_2.addWidget(self.label_13, 0, 1)

        perc_value = total_value / total_expenses * 100
        self.label_14 = Label(str(round(perc_value, 2)) + '%', 300)
        self.grid_2.addWidget(self.label_14, 0, 2)


class ShowTransactionsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Transactions records')
        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)

        self.table = self.show_table()
        if type(self.table) == QTableWidget:
            self.grid.addWidget(self.table, 0, 0)
        else:
            self.grid.addWidget(QLabel(self), 0, 0)

        self.set_table_width()

        try:
            max_h = sum([self.table.rowHeight(row)
                         for row in range(self.table.rowCount())]) + 40
            self.table.setMaximumHeight(max_h)
        except AttributeError:
            pass

    def get_column_names(self, table_name):
        columns = w.cursor.execute(
            f"SELECT sql FROM sqlite_master WHERE name='{table_name}';").fetchall()[0][0]

        first_sections = columns.split(f'"{table_name}"')[
            1].split('PRIMARY KEY')[0]

        upper = string.ascii_uppercase
        other = ['', ' ', '(', ')', '\n', '\t', '"']

        almost_done = [
            item for item in first_sections if item not in upper and item not in other]

        return [item for item in ''.join(
            almost_done).split(',') if item != '']

    def show_table(self, table_name='transactions'):
        columns = self.get_column_names(table_name)

        try:
            content = w.cursor.execute(
                f'SELECT * FROM {table_name}').fetchall()
        except OperationalError:
            msg = QMessageBox(QMessageBox.Warning,
                              'Error with columns', f'Columns: {columns}')
            msg.exec_()

        try:
            if len(content) == 0 and len(content[0]) == 0:
                msg = QMessageBox(QMessageBox.Warning,
                                  'Empty table', 'Table has no entries')
                msg.exec_()
                return None
            table = QTableWidget(len(content), len(content[0]), self)
            for i in range(len(content)):
                for j in range(len(content[0])):
                    item = QTableWidgetItem(content[i][j])
                    item.setForeground(QBrush(QColor("#1eecc9")))
                    table.setItem(i, j, item)

            table.setHorizontalHeaderLabels(columns)

            return table

        except IndexError:
            msg = QMessageBox(QMessageBox.Warning, 'Table empty',
                              'Table empty, cannot show data')
            msg.exec_()

    def set_table_width(self):
        try:
            width = self.table.verticalHeader().width()
            width += self.table.horizontalHeader().length()
            if self.table.verticalScrollBar().isVisible():
                width += self.table.verticalScrollBar().width()
            width += self.table.frameWidth() * 2
            self.table.setFixedWidth(width)
        except AttributeError:
            pass


class GraphWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Graphs Window')
        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)
        self.frame_1 = QFrame(self)
        self.grid_1 = QGridLayout(self.frame_1)
        self.grid.addWidget(self.frame_1, 0, 0)

        self.frame_2 = QFrame(self)
        self.frame_2.setMaximumHeight(150)
        self.grid.addWidget(self.frame_2)
        self.grid_2 = QGridLayout(self.frame_2)
        self.grid.addWidget(self.frame_2, 1, 0)

        self.label_1 = Label('Enter a ticker', 300)
        self.grid_1.addWidget(self.label_1, 0, 0)
        self.edit_1 = LineEdit(300)
        self.edit_1.setText('BTC')
        self.grid_1.addWidget(self.edit_1, 0, 1)

        self.label_2 = Label('Enter a currency', 300)
        self.grid_1.addWidget(self.label_2, 1, 0)
        self.edit_2 = LineEdit(300)
        self.edit_2.setText('EUR')
        self.grid_1.addWidget(self.edit_2, 1, 1)

        self.button_1 = PushButton('Make graph', 300, self.make_graph)
        self.grid_2.addWidget(self.button_1, 0, 0)

        self.button_2 = PushButton('1 month', 300, self.make_graph)
        self.button_3 = PushButton('6 months', 300, self.make_graph)
        self.button_4 = PushButton('1 year', 300, self.make_graph)

        self.buttons_shown = False

    def daily_price_historical(self, symbol, comparison_symbol, all_data=True, limit=1, aggregate=1, exchange=''):
        url = 'https://min-api.cryptocompare.com/data/histoday?fsym={}&tsym={}&limit={}&aggregate={}'\
            .format(symbol.upper(), comparison_symbol.upper(), limit, aggregate)
        if exchange:
            url += '&e={}'.format(exchange)
        if all_data:
            url += '&allData=true'

        try:
            page = requests.get(url)
            data = page.json()['Data']
            df = pd.DataFrame(data)
            df['timestamp'] = [datetime.fromtimestamp(d) for d in df.time]
            return df

        except ConnectionError:
            msg = QMessageBox(QMessageBox.Warning, 'Data not found',
                              'Error with internet connection')
            msg.exec_()

            return False

    def make_graph(self):
        try:
            df = self.daily_price_historical(
                self.edit_1.text().upper(), self.edit_2.text().upper())

            if type(df) != pd.DataFrame:
                return

            text = self.sender().text()
            now = datetime.now()

            if text == '1 year':
                time = 365
            elif text == '6 months':
                time = 180
            elif text == '1 month':
                time = 30
            else:
                time = 0

            now = (now - timedelta(days=time)).strftime("%Y-%m-%d")

            if text != 'Make graph':
                df = df[df["timestamp"] > now]

            self.canvas = MplCanvas(self)
            self.canvas.axes.plot(df.timestamp, df.close)
            self.grid_1.addWidget(self.canvas, 2, 0, 1, 3)
            self.canvas.show()

            self.canvas.axes.set_title(
                f'Historical price data for {self.edit_1.text().upper()} in {self.edit_2.text().upper()}')

            if self.buttons_shown != True:
                self.grid_1.addWidget(self.button_2, 3, 0)
                self.grid_1.addWidget(self.button_3, 3, 1)
                self.grid_1.addWidget(self.button_4, 3, 2)

        except AttributeError:
            msg = QMessageBox(QMessageBox.Warning, 'Data not found',
                              'Crypto with this symbol could not be found or not supported in this currency')
            msg.exec_()

            self.edit_1.setText('')
            self.edit_1.setFocus()


class ShowCryptos(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(0, 0, 900, 900)
        self.setWindowTitle('Crypto Rankings Window')
        self.setStyleSheet('background: #000000')

        self.grid = QGridLayout(self)

        self.frame_1 = QFrame(self)
        self.grid_1 = QGridLayout(self.frame_1)

        self.frame_2 = QFrame(self)
        self.grid_2 = QGridLayout(self.frame_2)

        self.grid.addWidget(self.frame_1, 0, 0)
        self.grid.addWidget(self.frame_2, 1, 0)

        self.grid_1.addWidget(Label('Num of cryptos: '), 0, 0)
        self.edit_1 = LineEdit(300)
        self.grid_1.addWidget(self.edit_1, 0, 1)
        self.grid_1.addWidget(PushButton('Look up', 300, self.get_data), 0, 2)

    def get_data(self):
        self.cursor = w.cursor
        self.database = w.db
        limit = self.edit_1.text()

        try:
            if float(limit) < 1:
                msg = QMessageBox(QMessageBox.Warning, 'Invalid limit',
                                  'Limit must be greater than or equal to one')
                msg.exec_()
                self.edit_1.setText('')
                return
        except ValueError:
            msg = QMessageBox(QMessageBox.Warning, 'Invalid input',
                              'Please enter a numerical input')
            msg.exec()
            return

        api_key = key.api_key
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
            'start': '1',
            'limit': limit,
            'convert': 'EUR'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }

        try:
            response = requests.get(url, params=parameters, headers=headers)
            data = json.loads(response.text)['data']
        except KeyError:
            msg = QMessageBox(QMessageBox.Warning, 'Error',
                              'Data could not be fetched')
            msg.exec_()

        info = {'name': [], 'symbol': [], 'price': [], 'id': [],
                'market_cap': [], 'market_dominance': []}

        for item in data:
            info['id'].append(item['id'])
            info['name'].append(item['name'])
            info['symbol'].append(item['symbol'])
            info['price'].append(round(item['quote']['EUR']['price'], 3))
            info['market_cap'].append(
                round(item['quote']['EUR']['market_cap'] / 1000000000, 3))
            info['market_dominance'].append(
                item['quote']['EUR']['market_cap_dominance'])

        self.table = QTableWidget(int(limit), 6)

        i = -1

        for item in info.keys():
            i += 1
            for j in range(len(info[item])):

                insertion = str(info[item][j])
                print(insertion)

                table_item = QTableWidgetItem(insertion)
                table_item.setForeground(QBrush(QColor("#1eecc9")))
                self.table.setItem(j, i, table_item)

        self.table.setHorizontalHeaderLabels(info.keys())

        self.grid_2.addWidget(self.table, 0, 0)


class LineEdit(QLineEdit):
    def __init__(self, width=0):
        super().__init__()
        self.base_stylesheet = ["*{border: 4px solid '#1eecc9';", "border-radius: 45px;",
                                "font-size: 20px;", "padding: 0 25px;", "color: '#1eecc9';}"]
        self.setStyleSheet(''.join(self.base_stylesheet))
        if width:
            self.setMaximumWidth(width)


class Label(QLabel):
    def __init__(self, text, width=0):
        super().__init__()
        self.base_stylesheet = [
            "*{color: #1eecc9;", "font-size: 25px;", "padding: 20 20 20 20px;}"]
        self.setStyleSheet(''.join(self.base_stylesheet))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText(text)
        if width:
            self.setMaximumWidth(width)


class CentralLabel(QLabel):
    def __init__(self, text):
        super().__init__()
        self.stylesheet = ['color: #1eecc9;', "font-size: 50px"]
        self.setStyleSheet(''.join(self.stylesheet))
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText(text)


class PushButton(QPushButton):
    def __init__(self, text, width=0, action=0):
        super().__init__()
        self.stylesheet = ["*{border: 4px solid '#1eecc9';", "border-radius: 45px;",
                           "font-size: 25px;", "color: '#1eecc9';", "padding: 30px;}", "*:hover{background: '#9604f5';}"]
        self.setStyleSheet(''.join(self.stylesheet))
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.setText(text)

        if width:
            self.setMaximumWidth(width)
        if action:
            self.clicked.connect(action)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = PortfolioManager()
    w.show()
    app.exec()
