print("hello")

from pathlib import Path
from datetime import datetime
import re 
import duckdb
import time
# & "path/python.exe" -m venv .venv    
# uv pip install duckdb numpy pandas


PATH_SOURCE = Path(__file__).parent
PATH_TRANS = PATH_SOURCE / 'invent_trans'
PATH_STOCK = PATH_SOURCE / 'stock'


def main() -> None:
    start_time = time.time()
     # 1. Задаем стартовую дату (2025-05-01) и конечную (2025-07-31)
    # stock_start = duckdb.sql(f"SELECT * FROM '{PATH_STOCK}/stock_2025_04_30.csv' LIMIT 5").df()
    # print(stock_start)
    # invent_trans = duckdb.sql(f"SELECT * FROM '{PATH_TRANS}/invent_trans_2025_05.csv' LIMIT 5").df()
    # print(invent_trans)
    # use_date= datetime.now().strftime('%Y-%m-%d')
    start_stock_files = sorted(PATH_STOCK.glob('stock_*.csv'))[-1]
    invent_trans_files = sorted(PATH_TRANS.glob('invent_trans_*.csv'))

    duckdb.sql(f"CREATE TEMP TABLE temp_start_stock_table AS SELECT * FROM '{start_stock_files}'")
    
    for file in invent_trans_files:
        duckdb.sql(f"CREATE TEMP TABLE temp_invent_trans_table AS SELECT * FROM '{file}'")
        # выдаёт кусок текста послностью совпадающий с шаблоном 
        file_date = re.search(r'\d{4}_\d{2}', file.name).group(0).replace('_','-')
        year=int(file_date.split('-')[0])
        month=int(file_date.split('-')[1])
        num_days=get_days_in_month(year, month)
        for i in range (1,num_days):
            if i <10:
                use_date=f"{file_date}-0{i}"
            else:
                use_date=f"{file_date}-{i}"
            
            output_file = PATH_STOCK / f"stock_{use_date.replace('-','_')}.csv"
            # print(output_file)
            result=duckdb.sql("copy (select item_id, location_id, trans_date, SUM(qty), SUM(cost_amount) from ("
                              "select * from temp_start_stock_table union all select * from temp_invent_trans_table)"
                              f"group by item_id, location_id, trans_date) TO '{str(output_file)}' (format csv, header true, delimiter ';');")

            
            # result=duckdb.sql(f"COPY (SELECT * FROM temp_invent_trans_table WHERE trans_date = '{use_date}') TO '{output_file}' (format csv, header true, delimiter ';');")
            # result=duckdb.sql(f"SELECT * FROM temp_invent_trans_table where trans_date = '{use_date}'").df()
            # result.to_csv(output_file, index=False, sep=';')
        duckdb.sql("drop table if exists temp_invent_trans_table")
    duckdb.sql("DROP TABLE IF EXISTS temp_start_stock_table")

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Общее время : {execution_time:.2f} секунд.")
    # 2. Оптимально: С помощью DuckDB один раз агрегируем тяжелые 4ГБ файлы движений 
    # из папки PATH_TRANS во временную легкую таблицу в памяти.
    
    # 3. Запускаем цикл по дням (от старта к концу):
        # - Берем файл 'вчера' из папки PATH_STOCK
        # - Берем изменения за 'сегодня' из нашей легкой таблицы
        # - Считаем новые остатки
        # - Сохраняем новый файл 'сегодня' в папку PATH_STOCK
    pass

def get_days_in_month(year: int, month: int) -> int:
    match month:
        case 4 | 6 | 9 | 11:
            return 30
        case 1 | 3 | 5 | 7 | 8 | 10 | 12:
            return 31
        case 2:
            # високосный год
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            return 28
        case _:
            raise ValueError("Неверный номер месяца")
        


if __name__ == "__main__":
    try:
        main()
    except Exception as e :
        print(f'Oops... Something wrong! {e}')
