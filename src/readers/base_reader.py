from abc import ABC, abstractmethod

class BaseReader(ABC):
    
    @abstractmethod
    def read_file(self, file_path):
        """
        Extracts data from the given file path.
        
        Args:
            file_path: The path to the file to extract data from.
            
        Returns:
            The extracted data in its raw format (e.g., list of dicts, Pandas DataFrame).
        """
        pass
