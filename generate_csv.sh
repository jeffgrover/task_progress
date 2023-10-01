curl -X 'POST' \
  'http://localhost:8000/csv' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "end_date": "2024-03-01",
  "num_entities": 1000,
  "start_date": "2022-01-01",
  "test_date": "2023-02-01",
  "values": [
    {
      "max_value": 1000000,
      "min_value": 0,
      "name": "Revenue",
      "skew_percent": 10,
      "units": "$"
    },
    {
      "max_value": 1000,
      "min_value": 0,
      "name": "Units Sold",
      "skew_percent": 5,
      "units": "pc"
    }
  ]
}'
