curl -X 'POST' \
  'http://localhost:8000/hist?entities=Site&values=Revenue' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  --data @data.csv