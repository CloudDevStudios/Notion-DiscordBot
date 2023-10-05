import requests
import json
import os

database = os.environ["DATABASE_TOKEN"]
print(database)
url = f"https://api.notion.com/v1/databases/{str(database)}/query"

def doesItExist(link):
  payload = json.dumps({
    "filter": {
      "property": "URL",
      "url":{
        "equals": link
      }
    }
  })
  headers = {
    'Authorization': str(os.environ["AUTH_KEY"]),
    'Notion-Version': '2021-05-13',
    'Content-Type': 'application/json'
  }
  response = requests.post(url, headers=headers, data=payload)
  try:
    result = response.json()["results"]
  except:
    return False
  return len(result) != 0

def amIThere(file):
  filesUploaded = []
  with open("./dataUploaded.txt") as log:
      filesUploaded = [line.strip() for line in log]
  print(filesUploaded)

  return file in filesUploaded
