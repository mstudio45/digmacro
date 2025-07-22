import time

def TookTimer(time_table):
    start_time = time.time()
    
    try: yield
    finally: time_table.append(time.time() - start_time)