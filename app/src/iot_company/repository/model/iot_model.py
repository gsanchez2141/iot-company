import logging
from dataclasses import dataclass, field
from typing import List
from typing import Optional, Tuple

@dataclass
class MessageDTO:
    region: str
    origin_coord: str
    destination_coord: str
    datetime: str
    datasource: str #= field(init=False)

    def __post_init__(self):
        if not isinstance(self.region, str) or len(self.region) > 255:
            raise ValueError("Invalid 'region' value")

        if not isinstance(self.datasource, str) or len(self.datasource) > 255:
            raise ValueError("Invalid 'datasource' value")

    @classmethod
    def model_validate(cls, data: dict) -> Optional['MessageDTO']:
        try:
            return cls(
                region=data['region'],
                origin_coord=data['origin_coord'],
                destination_coord=data['destination_coord'],
                datetime=data['datetime'],
                datasource=data['datasource']
            )
        except Exception as e:
            print(f"Error validating message: {e}")
            return None


@dataclass
class MessagesBatchDTO:
    messages: List[MessageDTO]

    def __post_init__(self):
        for message in self.messages:
            if not isinstance(message, MessageDTO):
                raise ValueError("Invalid message in 'messages' list")

    @classmethod
    def model_validate(cls, data: dict) -> Optional['MessagesBatchDTO']:
        try:
            return cls(
                messages=[MessageDTO.model_validate(message_data) for message_data in data['messages']]
            )
        except Exception as e:
            logging.error(f"Error validating messages batch: {e}")
            return None