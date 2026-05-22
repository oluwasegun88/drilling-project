import math
from datetime import datetime

class DataCleanUp:

    def sanitize_firestore_data(self, data):
        """
        Recursively sanitize Firestore data for JSON serialization.
        Converts NaN/Infinity to None.
        """

        if isinstance(data, dict):
            return {
                key: self.sanitize_firestore_data(value)
                for key, value in data.items()
            }

        elif isinstance(data, list):
            return [self.sanitize_firestore_data(item) for item in data]

        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None
            return data

        elif isinstance(data, datetime):
            return data.isoformat()

        return data
