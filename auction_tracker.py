import requests
from bs4 import BeautifulSoup
import time
import json
from flask import Flask, render_template, request

app = Flask(__name__)

database = {}  # database from file
fresh_scrap = {}  # freshly read advertisements
to_save = {}  # database ready to be overwritten after comparison with freshly read advertisements


# checking the number of pages with results
def checkPagesCount(x):
    temp_page = requests.get(x)
    temp_soup = BeautifulSoup(temp_page.content, 'html.parser')
    pages = temp_soup.find_all('li', {"data-testid":"pagination-list-item"})
    temp_list = []
    if len(pages) == 0:
        return 1
    else:
        for i in pages:
            element = i['aria-label']
            page_number = int(element[5:])
            temp_list.append(page_number)
            page_count = temp_list[-1]
        return page_count


# finding auctions
def findAuctions(x):
    temp_page = requests.get(x)
    temp_soup = BeautifulSoup(temp_page.content, 'html.parser')
    auctions = temp_soup.find_all('article', class_='ooa-yca59n')
    for auction in auctions:
        # finding title
        for i in auction('h1', class_='ooa-1ed90th'):
            title = i.string
            # print(title)
        
        # finding subtitle
        for i in auction('p', class_='ooa-1tku07r'):
            subtitle = i.string
            # print(subtitle)

        # finding mileage
        for i in auction('dd', {"class":"ooa-1omlbtp", "data-parameter":"mileage"}):
            mileage = i.text
            # print(mileage)

        # finding fuel type
        for i in auction('dd', {"class":"ooa-1omlbtp", "data-parameter":"fuel_type"}):
            fueltype = i.text
            # print(fueltype)

        # finding gearbox
        for i in auction('dd', {"class":"ooa-1omlbtp", "data-parameter":"gearbox"}):
            gearbox = i.text
            # print(gearbox)

        # finding year of production
        for i in auction('dd', {"class":"ooa-1omlbtp", "data-parameter":"year"}):
            year = int(i.text)
            # print(year)
            
        # finding price
        for i in auction('h3', class_='ooa-1n2paoq'):
            pre_price = i.string
            price = int(pre_price.replace(" ", ""))
            # print(price)

        # finding currency
        for i in auction('p', class_='ooa-8vn6i7'):
            currency = i.string
            # print(currency)

        # finding auction url
        for i in auction('div', hidden=True):
            for a in i('a'):
                auction_url = a['href']
                # print(auction_url)

        fresh_scrap[auction_url] = {
            "title":title,
            "subtitle":subtitle,
            "mileage":mileage,
            "fueltype":fueltype,
            "gearbox":gearbox,
            "year":year,
            "price":price,
            "currency":currency,
            "link":auction_url,
            "searchedwith": x
        }
    return fresh_scrap


def read_database():
    try:
        with open("database.json", 'r') as file:
            file_content = json.load(file)
        return file_content
    except FileNotFoundError:
        return {}
    
    
def save_database():
    with open("database.json", "w") as f:
        json_save = json.dump(fresh_scrap, f, indent=4)
        f.write = json_save


def start_tracker(x):
    global fresh_scrap
    fresh_scrap = {}
    cnt = checkPagesCount(x)
    freshscrap = findAuctions(x)
    counter = cnt
    # print(f"jest {cnt} stron")
    for num in range(cnt+1):
        if num == 0:
            pass
        else:
            www = f"{x}?page={num}"
            findAuctions(www)
            counter -= 1
            print(f"pozostalo {counter} stron")
            if counter > 0:
                print("kolejna strona za 2sek")
                time.sleep(1)
                print("kolejna strona za 1sek")
                time.sleep(1)
    return freshscrap


@app.route("/")
def homepage():
    database = read_database()
    return render_template("main.html", scrap=database)


@app.route("/track", methods=["POST"])
def track():
    if request.method == "POST":
        # preparing otomoto link
        make = request.form["make"]
        model = request.form["model"]
        pre_year_from = request.form["year_from"]
        year_from = f"/od-{pre_year_from}?"
        pre_year_to = request.form["year_to"]
        year_to = f"search%5Bfilter_float_year%3Ato%5D={pre_year_to}"
        pre_fuel = request.form["fuel"]
        fuel = f"search%5Bfilter_enum_fuel_type%5D={pre_fuel}&"
        pre_price_from = request.form["price_from"]
        price_from = f"search%5Bfilter_float_price%3Afrom%5D={pre_price_from}&"
        pre_price_to = request.form["price_to"]
        price_to = f"search%5Bfilter_float_price%3Ato%5D={pre_price_to}&"

        url = f"https://www.otomoto.pl/osobowe/{make}/{model}{year_from}{fuel}{price_from}{price_to}{year_to}"

        start_tracker(url)

        return render_template("posttrack.html", scrap=fresh_scrap)


@app.route("/save", methods=["POST"])
def save():
    save_database()
    time.sleep(2)
    read_database()
    return render_template("postsave.html")


@app.route("/refresh", methods=["POST"])
def refresh():
    database = read_database()
    if request.method == "POST":
        for i in database:
            url = database[i]["searchedwith"]
        
        start_tracker(url)

    return render_template("postrefresh.html", scrap=fresh_scrap, dbs=database)


if __name__ == "__main__":
    # app.run(debug=True)
    app.run()
