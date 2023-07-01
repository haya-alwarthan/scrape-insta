import http.client
import urllib
import json
import scrapy
conn = http.client.HTTPSConnection("api.webscraping.ai")

api_params = {
  'api_key': '32977205-62f6-4698-8045-f940356f090a',
  'proxy': 'residential',
  'js': 'false',
  'timeout': 25000,
  'url': 'https://www.instagram.com/nike/?__a=1&__d=1'
}
conn.request("GET", f"/html?{urllib.parse.urlencode(api_params)}")

res = conn.getresponse()
json_raw = res.read().decode("utf-8")
json_object = json.loads(json_raw)

print(json.dumps(json_object, indent=1))