# steam-card-seller
A python script which uses [steampy](https://github.com/bukson/steampy#usage) to sell all trading cards in your Steam inventory

---

## Setup

You need to have the [steampy](https://github.com/bukson/steampy#usage) library installed (`pip install -r requirements.txt`) and setup. By setup this means you must somehow have obtained your `steamid`, `shared_secret` and `identity_secret` from Steam mobile authenticator. I used [this tool](https://github.com/steamguard-totp/steamguard-shared-secret) to do this; but there are other ways described on the steampy github repo page.<br/>

After you have done this you must create a file `keys.json` with the following structure:
```json
{
    "api_key": "YOUR_STEAM_API_KEY",  // From https://steamcommunity.com/login/home/?goto=%2Fdev%2Fapikey
    "account_name": "YOUR_STEAM_USERNAME",
    "steamid": "YOUR_STEAM_ID_64",  // From SteamGuard/Other
    "shared_secret": "YOUR_SHARED_SECRET",  // From SteamGuard
    "identity_secret": "YOUR_IDENTITY_SECRET"  // From SteamGuard
}
```

## Config

The script is setup to sell your cards at **90% of the current lowest market listing**. But this and other parameters can be tweaked by changing variables within the script itself (they can be found towards the top of the file). They are commented to explain what they do.

## Running

Simply run `python sell_cards.py` and then enter your Steam password when prompted

## Future

Probably not going to update the script so much as it does what I want it to do but feel free to fork. Some nice additions would be command line arguments to change parameters or config files.
