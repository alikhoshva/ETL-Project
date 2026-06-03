from .base_reader import BaseReader

class CSVReader(BaseReader):
    def read_file(self, file_path):
        print(f"Extracting CSV from {file_path}")
        # Stub: Implement pandas or csv.DictReader logic here
        # Return raw data extracted from the CSV
        return [] 
