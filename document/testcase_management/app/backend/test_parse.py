import json

def parse_zmind_numbers(zmind_numbers):
    if isinstance(zmind_numbers, str):
        try:
            return json.loads(zmind_numbers)
        except:
            return []
    return zmind_numbers or []

# Test
test_data = '["3211231231"]'
print(parse_zmind_numbers(test_data))

test_data2 = '["456456", "7579879879"]'
print(parse_zmind_numbers(test_data2))