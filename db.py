import openpyxl
import os



def create_file(file_name):
    wb = openpyxl.Workbook()
    wb.save(file_name)


def add_skladchina(data: dict, file_name):
    if not os.path.isfile(file_name):
        wb = openpyxl.Workbook()
        max_row = 0
        ws = wb.active
    else:
        wb = openpyxl.load_workbook(file_name)
        ws = wb.active
        max_row = ws.max_row
    ws.cell(row=max_row+1, column=1).value = data['rubric']
    ws.cell(row=max_row+1, column=2).value = data['status']
    ws.cell(row=max_row+1, column=3).value = data['name']
    ws.cell(row=max_row+1, column=4).value = data['date']
    ws.cell(row=max_row+1, column=5).value = data['price']
    ws.cell(row=max_row+1, column=6).value = data['deposit']
    ws.cell(row=max_row+1, column=7).value = data['main']
    ws.cell(row=max_row+1, column=8).value = data['rezerve']
    ws.cell(row=max_row+1, column=9).value = data['views']
    wb.save(file_name)
