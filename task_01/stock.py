print("hello")

from pathlib import Path
from datetime import datetime, timedelta
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
     
    invent_trans_files = sorted(PATH_TRANS.glob('invent_trans_*.csv'))
    
   
    
    for file in invent_trans_files:
        duckdb.sql(f"create OR REPLACE  TEMP TABLE temp_invent_trans_table AS SELECT * FROM '{file}' ")
        #забирает файл с новейшей датой в наименовании (последний отсортированный)
        start_stock_files = sorted(PATH_STOCK.glob('stock_*.csv'))[-1]
        duckdb.sql(f"CREATE OR REPLACE TEMP TABLE temp_start_stock_table AS SELECT * FROM '{start_stock_files}'")

        duckdb.sql(f"CREATE OR REPLACE TEMP TABLE temp_use_stock_table AS SELECT * FROM temp_start_stock_table limit 0")

        # выдаёт кусок текста послностью совпадающий с шаблоном 
        file_date = re.search(r'\d{4}_\d{2}', file.name).group(0).replace('_','-')
        year=int(file_date.split('-')[0])
        month=int(file_date.split('-')[1])
        num_days=get_days_in_month(year, month)
        flag = True #флаг для использования стартовой таблицы или забор информации из уже собранных данных
        for i in range (1,num_days):
            #костыль использованя формата даты - забираем из файла год и месяц , дни добавляем инкриментально 
            if i <10:
                use_date=f"{file_date}-0{i}"
            else:
                use_date=f"{file_date}-{i}"

           #переменная следующего дня , используется для расчёта остатков 
            next_date = (datetime.strptime(use_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

            output_file = PATH_STOCK / f"stock_{use_date.replace('-','_')}.csv"

            if flag:
                use_table="temp_start_stock_table"
                flag=False
            else:
                use_table="temp_use_stock_table"
            
            sqltext = f"""select item_id, location_id, trans_date, sum(qty) as qty,  sum(cost_amount) as cost_amount from 
                                            (select item_id, location_id, '{next_date}' as trans_date, sum(qty) as qty , sum(cost_amount) as cost_amount from temp_invent_trans_table 
                                            where trans_date = '{next_date}' group by 1,2, 3 UNION ALl 
                                            select item_id, location_id, trans_date, qty, cost_amount  from {use_table} ) GROUP by 1, 2, 3 """
            duckdb.sql("delete from temp_use_stock_table")
            duckdb.sql(f"insert into temp_use_stock_table {sqltext}")
            
            result=duckdb.sql(f"copy ({sqltext}) TO '{str(output_file)}' (format csv, header true, delimiter ';')")
          
        duckdb.sql("drop table if exists temp_invent_trans_table")
    duckdb.sql("DROP TABLE IF EXISTS temp_start_stock_table")
    #высчитываем скорость отработки функции 
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Общее время : {execution_time:.2f} секунд.")
    
    pass
#выводим необходимые дни месяца 
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
        

#обратабываем ошибки
if __name__ == "__main__":
    try:
        main()
    except Exception as e :
        print(f'Oops... Something wrong! {e}')
