import os
from steampy.client import SteamClient
from steampy.utils import GameOptions
from steampy.market import Currency
from time import sleep
import json
import math

MARKET_FEE = 0.05        # The market fee percentage (I think)
MINIMUM_FEE = 0.01       # The minimum a card should sell for
REDUCTION = 0.90         # The percentage reduction that cards will be reduced by from the lowest listing price
SKIP_ITEM_BACKOFF = 120  # Skip the item if the backoff is greater than or equal to this number
STARTING_BACKOFF = 4     # The number of seconds the backoff should start at
BACKOFF_MULT = 1.6       # The multiplier to increase backoff time every failure
CURRENCY_CHAR = '£'      # The character/string denoting the currency to use in output

# If one of these exist somewhere inside the 'message' returned from an unsuccessful 'sellitem' API call 
# then the call will be retried
RETRY_MESSAGE_CONDITIONS = ['refresh the page']
REQUIRED_KEYS = {'api_key', 'account_name', 'steamid', 'shared_secret', 'identity_secret'}


def truncate_to_price(price: float) -> str:
    return str(math.trunc(price * 100.0) / 100.0)

def truncate_to_price_pennies(price: float) -> str:
    return str(int(price * 100.0))

def get_steam_price(sale_price: float, pennies: bool = True) -> str:
    steam_price = (sale_price / (1 + MARKET_FEE)) - MINIMUM_FEE
    return truncate_to_price_pennies(steam_price) if pennies else truncate_to_price(steam_price) if steam_price > MINIMUM_FEE else MINIMUM_FEE

# Open keys.json file
keys = None
if os.path.exists('keys.json') and os.path.isfile('keys.json'):
    with open('keys.json', 'r') as keys_file:
        keys: dict = json.load(keys_file)
else:
    # I used this: https://github.com/steamguard-totp/steamguard-shared-secret to get required information from the Android Steam Authenticator
    print('You must create a keys.json which contains', REQUIRED_KEYS)

# Check if there are any missing keys within keys.json
keys_key_set = set(keys.keys())
if len(keys_key_set.intersection(REQUIRED_KEYS)) != len(REQUIRED_KEYS):
    [print(f'Missing {req} in keys.json') for req in REQUIRED_KEYS - keys_key_set.intersection(REQUIRED_KEYS)]
    exit(0)


print(f'Keys file:\n{json.dumps(keys, indent=4, sort_keys=True)}')

with SteamClient(keys['api_key'], keys['account_name'], input('Enter password: '), 'keys.json') as client:
    # Get all items from Steam inventory
    steam_inventory: dict = client.get_my_inventory(GameOptions.STEAM)
    # Get market listings
    market_listing_ids = [listing['description']['id'] for listing in client.market.get_my_market_listings()['sell_listings'].values()]
    # Filter out everything but marketable trading cards that are not already listed
    trading_cards = list(filter(lambda item: any(['trading card' in tag['localized_tag_name'].lower() for tag in item['tags']]) and item['marketable'] and item['id'] not in market_listing_ids, steam_inventory.values()))

    total_money = 0.0
    listed_cards = 0
    starting_wallet_balance = client.get_wallet_balance()
    print(f'\nCurrent wallet balance: {CURRENCY_CHAR}{starting_wallet_balance}')

    if len(trading_cards):
        print('CP = Current lowest sell price on market')
        print('SP = Price that card is going to be listed for')
        print('RecP = Money that you will recieve once/if card is sold')
        print(f'Starting to sell {len(trading_cards)} trading card{"s" if len(trading_cards) - 1 else ""}:')
        for i, card in enumerate(trading_cards):
            # Get the lowest price the card is currently selling for, the price the card should be sold at and the money which you will recieve from a bought listing
            lowest_price = float(client.market.fetch_price(card['market_hash_name'], GameOptions.STEAM, Currency.GBP)['lowest_price'][1:])
            sell_price = float(truncate_to_price(lowest_price * REDUCTION))
            money_to_recieve_pounds, money_to_recieve_pennies = get_steam_price(sell_price, False), get_steam_price(sell_price)

            print(f"\t{i + 1}: {card['name']}, {card['type']}. CP = {CURRENCY_CHAR}{lowest_price}, SP = {CURRENCY_CHAR}{sell_price}, RecP = {CURRENCY_CHAR}{money_to_recieve_pounds}")

            backoff = STARTING_BACKOFF
            while backoff < SKIP_ITEM_BACKOFF:
                # Create a sell order using the previously calculated price and then increase the total money to gain from all sold cards
                sell_resp = client.market.create_sell_order(card['id'], GameOptions.STEAM, money_to_recieve_pennies)
                if sell_resp['success']:
                    # Break out of inner loop if the card is successfully listed
                    listed_cards += 1
                    total_money += float(money_to_recieve_pounds)
                    sleep(STARTING_BACKOFF)  # 20 requests every 60 seconds + 1 second redundency
                    break
                elif any([cond in str(sell_resp['message']).lower() for cond in RETRY_MESSAGE_CONDITIONS]):
                    # Keep retrying if the response contains 'refresh the page'
                    print('\t\t{}Waiting for {:.2f} seconds before trying again...'.format("Got a retry condition. " if backoff == STARTING_BACKOFF else "", backoff))
                    sleep(backoff)
                    backoff *= BACKOFF_MULT
                else:
                    print(f'\t\tError occured: {sell_resp}')
                    break
            else:
                print('\t\tCould not sell card. Skipping...')

        finishing_wallet_balance = client.get_wallet_balance()
        print(f'Total: {listed_cards} cards listed. Stand to gain {CURRENCY_CHAR}{truncate_to_price(total_money)}')
        print(f'Finishing wallet balance: {CURRENCY_CHAR}{finishing_wallet_balance}. Already gained: {CURRENCY_CHAR}{truncate_to_price(float(finishing_wallet_balance) - float(starting_wallet_balance))}')
    else:
        print('No trading cards to sell...')
