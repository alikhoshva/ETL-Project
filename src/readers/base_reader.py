from abc import ABC, abstractmethod

class BaseReader(ABC):
    
    @abstractmethod
    def read_file(self, file_path, db_connection):
        """Every reader MUST implement this exact method."""
        pass
