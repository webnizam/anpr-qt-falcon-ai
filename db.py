import json
import os
import pandas as pd
import csv
from datetime import datetime
from collections import Counter
    
class DatabaseManager:
    def __init__(self, file_path='db.csv'):
        self.file_path = file_path
        if not os.path.exists(file_path):
            pd.DataFrame(columns=['created_at', 'plate_number']).to_csv(self.file_path, index=False)
        try:
            self.data_frame = pd.read_csv(self.file_path)
        except Exception as e:
            print(e)
            self.data_frame = pd.DataFrame(columns=['created_at', 'plate_number'])
            
        print(self.data_frame)
        
        
    def add_record(self, record):
        df = pd.DataFrame({'created_at':[datetime.now()], 'plate_number':[str(record)]})
        self.data_frame = pd.concat([self.data_frame, df], ignore_index=True)
        self.data_frame.to_csv(self.file_path, index=False)
        
    def check_if_exists(self, keyword):
        found = []
        # print(f'{list(map(lambda x: x[1],self.data_frame.values.tolist()))=}')
        for key in keyword.split():
            if len(key) > 2:
                found.append( str(key) in [str(item[1]) for item in  self.data_frame.values.tolist()])
            
        if True in found:
            return True
        else:
            return False
    
    def remove_record(self, record):
        # self.
        print(f'{record=}')
        records = self.data_frame.index[self.data_frame['plate_number'] == record].tolist()
        print(records)
        for index in records:
            self.data_frame = self.data_frame.drop(index)
            
        self.data_frame.to_csv(self.file_path, index=False)
    
    def update_record(self, index, record):
        pass
    
    def get_all_records(self):
        return json.loads(self.data_frame.to_json(orient='records'))
        