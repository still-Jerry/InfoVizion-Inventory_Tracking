print("hello")

from pathlib import Path
from datetime import datetime
import re 
import duckdb
# & "path/python.exe" -m venv .venv    
# uv pip install duckdb numpy pandas


PATH_SOURCE = Path(__file__).parent
PATH_TRANS = PATH_SOURCE / 'invent_trans'
PATH_STOCK = PATH_SOURCE / 'stock'


def main() -> None:
     # 1. Задаем стартовую дату (2025-05-01) и конечную (2025-07-31)
    # stock_start = duckdb.sql(f"SELECT * FROM '{PATH_STOCK}/stock_2025_04_30.csv' LIMIT 5").df()
    # print(stock_start)
    # invent_trans = duckdb.sql(f"SELECT * FROM '{PATH_TRANS}/invent_trans_2025_05.csv' LIMIT 5").df()
    # print(invent_trans)

    # use_date= datetime.now().strftime('%Y-%m-%d')
    invent_trans_files = sorted(PATH_TRANS.glob('invent_trans_*.csv'))
    for file in invent_trans_files:
        # выдаёт кусок текста послностью совпадающий с шаблоном 
        file_date = re.search(r'\d{4}_\d{2}', file.name).group(0).replace('_','-')
        # print(use_date)
        
        # print(output_file)
        for i in range (1,31):
            
            if i <10:
                use_date=f"{file_date}-0{i}"
            else:
                use_date=f"{file_date}-{i}"
            result=duckdb.sql(f"SELECT * FROM '{file}' where trans_date = '{use_date}'").df()
            output_file = PATH_STOCK / f"stock_{use_date.replace('-','_')}.csv"
            result.to_csv(output_file, index=False, sep=';')
    # 2. Оптимально: С помощью DuckDB один раз агрегируем тяжелые 4ГБ файлы движений 
    # из папки PATH_TRANS во временную легкую таблицу в памяти.
    
    # 3. Запускаем цикл по дням (от старта к концу):
        # - Берем файл 'вчера' из папки PATH_STOCK
        # - Берем изменения за 'сегодня' из нашей легкой таблицы
        # - Считаем новые остатки
        # - Сохраняем новый файл 'сегодня' в папку PATH_STOCK
    pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e :
        print(f'Oops... Something wrong! {e}')
