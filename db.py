import openpyxl
import os
from datetime import datetime

HEADER = ['Категория курса', 'Статус курса', 'Дата создания темы', 'Название темы',
          'Количество просмотров', 'Количество просмотров деленное на количестство дней на сайте',
          'Цена', 'Взнос', 'Цена деленная на взнос', 'Количество Складчиков в основном списке',
          'Количество просмотров деленное на количество складчиков', 'Хэштеги']


def create_file(file_name):
    wb = openpyxl.Workbook()
    ws = wb.active
    for column in range(1, len(HEADER) + 1):
        ws.cell(row=1, column=column).value = HEADER[column - 1]
    wb.save(file_name)


def add_skladchina(data: dict, file_name):
    if not os.path.isfile(file_name):
        create_file(file_name)
    wb = openpyxl.load_workbook(file_name)
    ws = wb.active
    max_row = ws.max_row
    ws.cell(row=max_row + 1, column=1).value = data['rubric']
    ws.cell(row=max_row + 1, column=2).value = data['status']
    ws.cell(row=max_row + 1, column=3).value = data['date'].strftime("%d.%m.%Y")
    ws.cell(row=max_row + 1, column=4).value = data['name']
    views = float(data['views'].replace('.', ''))
    ws.cell(row=max_row + 1, column=5).value = views
    days_on_site = (datetime.now()-data['date']).days
    ws.cell(row=max_row + 1, column=6).value = views/days_on_site
    price = float(data['price'].replace(' руб', ''))
    ws.cell(row=max_row + 1, column=7).value = price
    deposit = float(data['deposit'].replace(' руб', ''))
    ws.cell(row=max_row + 1, column=8).value = deposit
    ws.cell(row=max_row + 1, column=9).value = price/deposit
    main = float(data['main'].replace('.', ''))
    ws.cell(row=max_row + 1, column=10).value = main
    ws.cell(row=max_row + 1, column=11).value = views/main
    ws.cell(row=max_row + 1, column=12).value = ', '.join(data['hash_tags'])
    wb.save(file_name)


if __name__ == '__main__':
    create_file('data.xlsx')
