import asyncio
import json
from main import rule_based_parser

def test():
    query = 'Context (already known): {"from_city": "coimbatore", "to_city": null, "date": "tomorrow", "passengers": 1}\nUser says: rameswaram'
    
    # Test rule_based_parser directly
    print('RULE BASED:', json.dumps(rule_based_parser(query, []), indent=2))

test()
