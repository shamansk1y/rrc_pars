import pandas as pd

# Загрузка CSV-файла
df = pd.read_csv('copa.csv')

# Создание объекта Excel-файла
excel_file = 'copa.xlsx'

# Сохранение данных в Excel
df.to_excel(excel_file, index=False)
