import requests
from bs4 import BeautifulSoup
from database import SessionLocal, engine
import models
import json
import validators
from functionality.security import *
db = SessionLocal()


class SearchData:
    id = ""
    title = ""
    url = ""

    def __init__(self, id, title, url):
        self.id = id
        self.title = title
        self.url = url


def getTitle(url):
    try:
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")
        title_tag = soup.find("title")
        return title_tag.get_text()
    except:
        return None


def checkURL(url):
    return bool(validators.url(url))


def getTags(args):
    url = args[0]
    # Tag provided
    final_tag = []
    list_of_tags = []

    # Multiple
    for tag in args[1:]:
        # Adding the arguments to list_of_tags
        list_of_tags.append(tag)
        for tag in list_of_tags:
            # Splitting the arguments to get the tags
            tag_list = tag.split(",")
            for single_tag in tag_list:
                if single_tag.strip() == "":
                    pass
                # Appending tag to the final_tag dict
                print(single_tag.strip().lower())
                if {"name": single_tag.strip().lower()} not in final_tag:
                    final_tag.append({"name": single_tag.strip().lower()})
    return final_tag if final_tag else [{"name": "misc"}]


def getSearchTagsPayload(tags):
    final_tag = []
    list_of_tags = []

    # Multiple
    for tag in tags:
        # Adding the arguments to list_of_tags
        list_of_tags.append(tag)

        for tag in list_of_tags:
            # Splitting the arguments to get the tags
            tag_list = tag.split(",")
            final_tag.extend(
                {
                    "property": "Tag",
                    "multi_select": {"contains": single_tag.strip().lower()},
                }
                for single_tag in tag_list
                if single_tag.strip() != ""
            )
    return final_tag

def getResults(url, payload, headers):
    response = requests.post(url, headers=headers, data=payload)
    return response.json()

def searchTag(notion_db_id, notion_api_key, tags):
    # Search for a tag
    url = f"https://api.notion.com/v1/databases/{notion_db_id}/query"
    payload = json.dumps({"filter": {"and": tags}})
    headers = {
        "Authorization": notion_api_key,
        "Notion-Version": "2021-05-13",
        "Content-Type": "application/json",
    }

    data = getResults(url, payload, headers)
    query_results = data["results"]
    no_of_results = len(query_results)

    search_results = []
    if no_of_results == 0:
        # No results found
        return search_results
    for result in query_results:
        # Create Search Object for each result
        search_object = SearchData(
            id=result["id"],
            url=result["properties"]["URL"]["url"].strip(),
            title=result["properties"]["Title"]["rich_text"][0]["plain_text"].strip(),
        )
        search_results.append(search_object)

    while data["next_cursor"]:
        # pagination
        payload = json.dumps({"filter": {"and": tags}, "cursor": data["next_cursor"]})
        data = getResults(url, payload, headers)
        query_results = data["results"]
        no_of_results = len(query_results)
        if no_of_results == 0:
            return search_results
        for result in query_results:
            # Create Search Object for each result
            search_object = SearchData(
                id=result["id"],
                url=result["properties"]["URL"]["url"].strip(),
                title=result["properties"]["Title"]["rich_text"][0]["plain_text"].strip(),
            )
            search_results.append(search_object)
    return search_results


def getGuildData():
    guilds = db.query(models.Clients).all()
    return {str(guild.guild_id): guild for guild in guilds}


def getPrefixes():
    guilds = db.query(models.Clients).all()
    return {str(guild.guild_id): guild.prefix for guild in guilds}


def checkIfGuildPresent(guildId):
    return bool(
        guild := db.query(models.Clients)
        .filter(models.Clients.guild_id == guildId)
        .first()
    )


def getQueryForTitle(args):
    if len(args) <= 0:
        # no data received
        return None
    query = "".join(f"{arg} " for arg in args)
    return query.strip()


def deserialize(data):
    return models.Clients(
        data["guild_id"],
        data["notion_api_key"],
        data["notion_db_id"],
        data["tag"],
        data["prefix"],
    )

def fixDatabase():
    # update database
    guilds = db.query(models.Clients).all()
    data = {}
    for guild in guilds:
        data[str(guild.guild_id)] = guild
        # encrypt api key and db key
        guild.notion_api_key = encrypt(guild.notion_api_key)
        guild.notion_db_id = encrypt(guild.notion_db_id)
        # update
        db.commit()
    return data


def getGuildInfo():
    # read guild_data.json
    guilds = db.query(models.Clients).all()
    # check if the records are encrypted
    data = {}
    for guild in guilds:
        if getKey(guild.notion_db_id) and getKey(guild.notion_api_key):
            # all good
            obj = models.Clients(
                guild.guild_id,
                getKey(guild.notion_api_key),
                getKey(guild.notion_db_id),
                guild.tag,
                guild.prefix
            )
            print(obj.notion_api_key)
            print(obj.notion_db_id)
            data[str(guild.guild_id)] = obj
        else:
            # database rescue 
            print("Database not encrypt! Start encryption")
            print("Database fixed")
            fixDatabase()
            return getGuildInfo()
            
    print(data)
    return data

def doesItExist(link, api_key, db_id):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload = json.dumps({"filter": {"property": "URL", "url": {"equals": link}}})
    headers = {
        "Authorization": api_key,
        "Notion-Version": "2021-05-13",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, data=payload)
    try:
        result = response.json()["results"]
    except:
        return False
    return len(result) != 0


def getFileTags(args):
    # Tag provided
    final_tag = []
    list_of_tags = []

    # Multiple
    for tag in args:
        # Adding the arguments to list_of_tags
        list_of_tags.append(tag)

        for tag in list_of_tags:
            # Splitting the arguments to get the tags
            tag_list = tag.split(",")
            final_tag.extend(
                {"name": single_tag.strip().lower()}
                for single_tag in tag_list
                if single_tag.strip() != ""
            )
    return final_tag if final_tag else [{"name": "misc"}]
