# -*- coding: utf-8 -*-
import urllib.request as ur
from bs4 import BeautifulSoup
import re
import datetime
from pymongo import MongoClient
from Meal.Ingredients import Ingredients

mensa_urls = [
    {
        "url": "http://www.studentenwerk-potsdam.de/mensa-golm.html",
        "uni": "Uni Potsdam",
        "mensa": "Mensa Golm"
    },
    {
        "url": "http://www.studentenwerk-potsdam.de/de/mensa-griebnitzsee.html",
        "uni": "Uni Potsdam",
        "mensa": "Mensa Griebnitzsee"
    },
    {
        "url": "http://www.studentenwerk-potsdam.de/mensa-am-neuen-palais.html",
        "uni": "Uni Potsdam",
        "mensa": "Mensa am Neuen Palais"
    }
]

ingredients_lookup = {
    "1": "colouring",
    "2": "preservative",
    "3": "antioxidant",
    "4": "flavour_enhancer",
    "5": "sulfur",
    "6": "blackened",
    "7": "waxed",
    "8": "phosphate",
    "9": "sweetener",
    "11": "aspartam",
    "13": "lactoprotein",
    "14": "egg_white",
    "20": "quinine",
    "21": "caffeine",
    "22": "milk_powder",
    "23": "whey_powder",
    "KF": "cocoa",
    "TL": "rennet",
    "AL": "alcohol",
    "GE": "gelatin",
    "A": "gluten",
    "B": "crustaceans",
    "C": "eggs",
    "D": "fish",
    "E": "peanuts",
    "F": "soy",
    "G": "milk",
    "H": "edible_nuts",
    "I": "celeriac",
    "J": "mustard",
    "K": "sesame",
    "L": "sulfite",
    "M": "lupin",
    "N": "molluscs"
}

ingredients_pattern = re.compile(r'\d{1,2}|[A-Z]{1,2}(?=\))')


def clean(text):
    """
    Remove stuff that could be in the text.
    """
    new = text.replace("\r", "")
    new = new.replace("\t", "")
    new = new.replace("\n", "")
    new = new.replace("- ", "-")
    new = new.replace(",", ", ")

    new = new.replace("  ", " ")
    new = new.replace("  ", " ")
    new = new.replace("  ", " ")

    return new


def check_page(url):
    page = BeautifulSoup(ur.urlopen(url).read(), "html.parser")
    number_of_menu_rows = len(page.find_all("td", attrs={"class": "text1"}))

    table = page.find("table", attrs={"class": "bill_of_fare"})

    title = []
    ingredients = []
    texts = []
    for row in table.find_all('tr'):
        for cell in row.find_all('td'):
            if 'class' in cell.attrs:
                for cell_class in cell['class']:
                    if cell_class == 'head':
                        title.append(cell.text)
                    elif 'text' in cell_class:
                        texts.append(clean(cell.text))
                    elif 'label' in cell_class:
                        ingredients_store = Ingredients()
                        for i in re.findall(ingredients_pattern, cell.text):
                            if i in ingredients_lookup:
                                ingredients_store.contains(ingredients_lookup[i])

                        for img in cell.find_all("img"):
                            image_url = img.attrs['src']
                            if "hahn" in image_url:
                                ingredients_store.contains_chicken()
                            elif "mais.png" in image_url:
                                ingredients_store.contains_vegetarian()
                            elif "sau" in image_url:
                                ingredients_store.contains_pork()
                            elif "kuh" in image_url:
                                ingredients_store.contains_beef()
                            elif "fisch" in image_url:
                                ingredients_store.contains_fish()
                            elif "lamm" in image_url:
                                ingredients_store.contains_lamb()
                            elif "mais2" in image_url:
                                ingredients_store.contains_vegan()
                            elif "vital" in image_url:
                                ingredients_store.contains_vital()

                        ingredients.append(ingredients_store)

    assert len(title) == len(texts) == len(ingredients)

    list_of_offers = []
    for i in range(len(title)):
        json = {
            "name": title[i],
            "text": texts[i],
            "ingredients": ingredients[i].get_ingredients(),
            "diets": ingredients[i].get_diets(),
        }
        print(json)
        list_of_offers.append(json)

    return list_of_offers

insert_these = []
for mensa in mensa_urls:
    try:
        meals = check_page(mensa["url"])
        for meal in meals:
            json = {
                "meal" : meal["text"],
                "title" : meal["name"],
                "ingredients" : meal["ingredients"],
                "diets" : meal["diets"],
                "mensa" : mensa["mensa"],
                "uni" : mensa["uni"],
                "createdAt" : datetime.datetime.utcnow()
            }
            insert_these.append(json)
    except Exception as e:
        print("Error!")
        print(e.with_traceback())
        pass

if len(insert_these) > 0:
    MongoClient('mongodb://localhost:3001/')['meteor']['offers'].insert_many(insert_these)
