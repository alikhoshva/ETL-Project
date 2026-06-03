from .base_reader import BaseReader

class JSONReader(BaseReader):
    def read_file(self, file_path):
        print(f"Extracting JSON from {file_path}")
        # Stub: Implement json.load logic here
        # Return raw data extracted from the JSON
        return []
