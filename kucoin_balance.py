def kukoin_run():
    
    # First importing the needed libraries:

    import pandas as pd
    import numpy as np


    import os
    import requests
    import json
    import base64
    import time
    import base64
    import hmac
    import hashlib

    # Now importing the env file so the script can access the KuCoin API keys:
    import env

    # Defining the api keys with their own variables:
    api_key = env.kc_api_key
    api_s = env.kc_secret_api
    api_pp = env.kc_passphrase
    api_uid = env.kc_uid

    # creating the api keys for use in the calls:
    api_key = env.kc_api_key
    api_secret = env.kc_secret_api
    api_passphrase = env.kc_passphrase
    url = 'https://api.kucoin.com/api/v1/accounts'
    now = int(time.time() * 1000)
    str_to_sign = str(now) + 'GET' + '/api/v1/accounts'
    signature = base64.b64encode(
        hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": str(2)
    }

    # Getting the base response with the top level account values:
    response = requests.request('get', url, headers=headers)


    # Creating the account dataframe using the response request I just created:
    df = pd.DataFrame.from_dict(response.json()['data'])

    # Column cleanup:
    df.drop(columns = 'id', inplace = True)

    # Getting prices for coins:


    coin_list = df['currency'].unique().tolist()

    # USDC and USDT don't work in this list because they are "equivalent" of USD, so it comes back as a NoneType, leading to a none-type error later if I don't remove them from the list at this point.
    coin_list.remove('USDC')
    coin_list.remove('USDT')
    # This for loop will create a list of prices by calling each crypto within my 'coin_list' list. 

    price_list = []
    for coin in coin_list:
        prices = float(requests.get(f'https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={coin}-USDT').json()['data']['price'])
    #     print(prices), print(type(prices))
        price_list.append(prices)

    # Now creating a dictionary of the coin prices:
    coin_dict = {"coin":coin_list, "price":price_list}

    # Dataframe from the dictionary:
    df_prices = pd.DataFrame(coin_dict)

    # creating a copy dataframe of the acct info (this step can be dropped in future)
    account = df[df['type'] == 'trade'].copy()
    account = account.reset_index(drop = True)
    account.rename(columns = {'type': "act_name"}, inplace = True)


    # Now should be able to join the two dataframes. I have to join the two dataframes first before I can multiply columns to create the "$ value" column which is the end goal here.

    # Merge, inner join:

    holdings = account.merge(df_prices, left_on = 'currency', right_on = 'coin', how = 'left')

    # Now changing the value types of the columns with numbers in them from objects to float64:
    holdings['balance'] = holdings.balance.astype(float)
    holdings['available'] = holdings.available.astype(float)
    holdings['holds'] = holdings.holds.astype(float)

    # Now working through adding calculated columns that I'll later select from if it doesn't return 'nan':

    holdings['value_tmp'] = round(holdings.price * holdings.balance, 2)

    holdings["dollar_value"] = np.where(holdings['value_tmp'].notnull(), holdings['value_tmp'], holdings['balance'])
    holdings.dollar_value = holdings.dollar_value.round(2)

    # Dropping extra columns:
    holdings.drop(columns = ['coin', 'value_tmp'], inplace = True)

    # Adding date column, and changing date to the dataframe index:
    # holdings.insert(0, 'date', pd.to_datetime('today').strftime('%Y-%m-%d'))
    holdings.insert(0, 'date', pd.to_datetime('now').replace(microsecond=0))
    holdings.date = pd.to_datetime(holdings.date)
    holdings = holdings.set_index('date').sort_index()

  

    # holdings.to_csv("data.csv")
    # holdings.to_csv("account_holdings_no_index.csv", index = False)
    
    # printing out result, and saving to csv and Excel.
    return holdings


    # holdings.to_excel("account_holdings_index.xlsx")
    # holdings.to_excel("account_holdings_no_index.xlsx", index = False)
    # print("CSV written successfully.")