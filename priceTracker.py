from bs4 import BeautifulSoup
import pandas as pd
import requests
import gspread
import unicodedata
import smtplib, ssl
import logging 
import credentials_user


sender_email = credentials_user.USER_EMAIL
receiver_email = credentials_user.RECEIVER_EMAIL
password = credentials_user.PASSWORD
credentials = credentials_user.PATH_CREDENTIALS


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
    products_below_limit = [product for product in products if product[4]]

    if products_below_limit:
        message = "Subject: Alerta de precio!\n\n"
        message += "El seguimineto de tu producto está por debajo del target.\n\n"
        for title, price, stars, target, under_target, url in products_below_limit:
            message += f"{title}\n\n"
            message += f"Precio Actual:\t\t{price}€\n"
            message += f"Target:\t\t{target}€\n"
            message += f"{url}\n\n\n"

        message = message.encode('utf-8')
        send_email(sender_email, password, receiver_email, message)



def connect_to_google_sheets(credentials):
    gc = gspread.service_account(filename=credentials)
    sh = gc.open_by_key(credentials_user.API_GOOGLE_KEY)
    return sh.sheet1



# gets url from the sheet and add the title and price
def update_products(df, ws):
    urls = df['urls']
    i  = 0
    for url in urls:
        print(f"scraping product ... {i} ")
        title, price, stars = get_product_info(url)
        df.loc[i, ['producto', 'precio', 'stars']] = [title, price, stars]
    
        if df.loc[i, ['target']].values == '' or float(df.loc[i, ['target']].values) < price:
            df.loc[i, ['under_target']] = False
        else:
            df.loc[i, ['under_target']] = True
        i += 1

    ws.update([df.columns.values.tolist()] + df.values.tolist())
    return df.values.tolist()



def main():
    # Conexion al spreadsheet de google
    worksheet = connect_to_google_sheets(credentials)
    df = pd.DataFrame(worksheet.get_all_records())
    products = update_products(df, worksheet)
    alert_product_under_target(products)



if __name__ == '__main__':
    main()
