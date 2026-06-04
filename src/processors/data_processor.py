from core.logger import get_logger
import pandas as pd
from typing import List, Callable

logger = get_logger(__name__)

class DataProcessor:
    def __init__(self, validation_rules: List[Callable] = None):
        """
        Args:
            validation_rules: A list of functions. Each function must accept a 
                              Pandas DataFrame and return a Boolean Series (a mask).
        """
        # If no rules are provided, default to an empty list
        self.validation_rules = validation_rules or []
        
    def clean_data(self, raw_data: pd.DataFrame):
        logger.info("Transforming and cleaning data...")

        # Basic universal cleaning
        cleaned_data = raw_data.dropna().drop_duplicates()
        
        # If no rules were passed, everything is valid
        if not self.validation_rules:
            return cleaned_data.to_dict('records'), []

        # Start with a mask where EVERY row is considered True (Valid)
        overall_mask = pd.Series(True, index=cleaned_data.index)
        
        # Apply each rule dynamically
        for rule in self.validation_rules:
            # Combine the masks using bitwise AND (&)
            overall_mask = overall_mask & rule(cleaned_data)
            
        # Split the data based on the final combined mask
        valid_df = cleaned_data[overall_mask]
        invalid_df = cleaned_data[~overall_mask] 
        
        valid_records = valid_df.to_dict('records')
        invalid_records = invalid_df.to_dict('records')
        
        logger.info(f"Validation complete: {len(valid_records)} valid, {len(invalid_records)} invalid.")
        
        return valid_records, invalid_records
