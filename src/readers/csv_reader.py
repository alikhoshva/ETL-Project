from .base_reader import BaseReader

class CSVReader(BaseReader):
    def read_file(self, file_path, db_connection):
        return super().read_file(file_path, db_connection)
