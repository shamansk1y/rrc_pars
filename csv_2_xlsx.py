import pandas as pd

# Загрузка CSV-файла
df = pd.read_csv('soccer.csv')

# Создание объекта Excel-файла
excel_file = 'soccer.xlsx'

# Сохранение данных в Excel
df.to_excel(excel_file, index=False)
