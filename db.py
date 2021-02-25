import openpyxl
import os

XLS_FILE = 'data.xlsx'


def create_file():
    wb = openpyxl.Workbook()
    wb.save(XLS_FILE)


def add_skladchina(data: dict):
    if not os.path.isfile(XLS_FILE):
        wb = openpyxl.Workbook()
    else:
        wb = openpyxl.load_workbook(XLS_FILE)
    ws = wb.active
    max_row = ws.max_row
    ws.cell(row=max_row, column=1).value = data['rubric']
    ws.cell(row=max_row, column=2).value = data['status']
    ws.cell(row=max_row, column=3).value = data['name']
    ws.cell(row=max_row, column=4).value = data['date']
    ws.cell(row=max_row, column=5).value = data['price']
    ws.cell(row=max_row, column=6).value = data['deposit']
    ws.cell(row=max_row, column=7).value = data['main']
    ws.cell(row=max_row, column=8).value = data['rezerve']
    ws.cell(row=max_row, column=9).value = data['views']
    wb.save(XLS_FILE)
