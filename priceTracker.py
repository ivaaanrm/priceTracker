from bs4 import BeautifulSoup
import pandas as pd
import requests
import gspread
import unicodedata
import smtplib, ssl
import logging
import credentials_user


######### Amazon web scraping  #############
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})

# returns (title, price, stars)
def get_product_info(url):
    try:
        page = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(page.content, features="lxml")
        try:
            title = soup.find(id='productTitle').text.strip()
            price_str = soup.find(id='corePrice_feature_div').find("span", class_='a-offscreen').get_text().strip('€')
            try:
                stars = soup.find(id='acrPopover').find("span", class_="a-icon-alt").get_text().strip()
            except:
                stars = None
            #print(f"Titulo:\n{title}\nPrecio: {price_str}\n{stars}")
        except:
            return None, None, None
        
        try:
            price = unicodedata.normalize("NFKD", price_str)
            price = price.replace(',', '.')
            price = float(price)
        except:
            return None, None, None
    except:
        return None, None, None

    return title, price, stars



def send_email(sender_email, password, receiver_email, message):
    smtp_server = "smtp.gmail.com"
    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        try:
            server.login(sender_email, password)
            res = server.sendmail(sender_email, receiver_email, message)
            print('email send!')
        except Exception as e:
            logging.exception('No se ha podido enviar', e)



# products = ((real_price, target))
def alert_product_under_target(products):
    products_below_limit = []
    for product in products:
        if product[4]:
            products_below_limit.append(product)

    if products_below_limit:
        message = "Subject: Alerta de precio!\n\n"
        message += "El seguimineto de tu producto está por debajo del target.\n\n"
        for title, price, stars, target, under_target, url in products_below_limit:
            message += f"{title}\n\n"
            message += f"Precio Actual:\t\t{price}€\n"
            message += f"Target:\t\t{target}€\n"
            # message += f"Descuento:\t\t\t{(1-price/target)*100}"
            message += f"{url}\n\n\n"
        #print(message)
        message = message.encode('utf-8')
        send_email(sender_email, password, receiver_email, message)



def connect_to_google_sheets(credentials):
    gc = gspread.service_account(filename=credentials)
    sh = gc.open_by_key(credentials_user.API_GOOGLE_KEY)
    return sh.sheet1



# gets url from the sheet and add the title and price
def update_products(df):
    products = set() # maybe no hace falta
    urls = df['urls']
    # urls = worksheet.col_values(5)[1:] # devuelve las urls de todos los productos del excel
    i  = 0
    for url in urls:
        print(f"scraping product ... {i} ")
        title, price, stars = get_product_info(url)
        df.loc[i, ['producto', 'precio', 'stars']] = [title, price, stars]
        # print(df.loc[i, ['target']].values == '')
        # print(f"valor del target:\t{df.loc[i, ['target']].values}")
        if df.loc[i, ['target']].values == '' or float(df.loc[i, ['target']].values) < price:
            df.loc[i, ['under_target']] = False
        else:
            df.loc[i, ['under_target']] = True
        i += 1
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    return df.values.tolist()




# Datos para enviar el email
sender_email = credentials_user.USER_EMAIL
receiver_email = credentials_user.RECEIVER_EMAIL
password = credentials_user.PASSWORD

# Conexion al spreadsheet de google
credentials = '/Users/ivan/Desktop/python/price_tracker/credentials.json'
worksheet = connect_to_google_sheets(credentials)
df = pd.DataFrame(worksheet.get_all_records())

products = update_products(df)

print(products)
alert_product_under_target(products)
