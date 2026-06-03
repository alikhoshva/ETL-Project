from abc import ABC, abstractmethod

class BaseReader(ABC):
    
    @abstractmethod
    def read_file(self, file_path):
        """
        Extracts data from the given file path.
        Returns:
            raw_data: The extracted data in its raw format (e.g., list of dicts, pandas DataFrame).
        """
        pass
