# POAP Reddit Bot: Code distribution for POAP events
<img src="assets/poap-logo.svg" width="100" height="100"> <img src="assets/reddit-logo.png" width="100" height="100"> 

# Table of Contents
- [Usage](#usage)
  * [Attendees](#attendees)
  * [Admin via Reddit](#admin-via-reddit)
      - [Create Event](#create-event)
      - [Update Event](#update-event)
      - [Get Event](#get-event)
      - [Create Claims](#create-claims)
  * [Admin via API](#admin-via-api)
- [Setup](#setup)
  * [Clone](#clone)
  * [Configuration](#configuration)
  * [Deploy](#deploy)
    + [Docker](#docker)
    + [Python](#python)

# Usage
## Attendees
Once you've created and configured your event with the bot, all you need to do is distribute the secret code to attendees. Let them know that they just need to private message the bot with the code and it will give them their claim link. Below is a template you can use which includes a link they can click to initiate the message automatically!

> This message contains a link to claim the POAP for <YOUR EVENT NAME\>. POAP is the Proof of Attendance Protocol, a platform that issues ERC-721 tokens on the xDai platform to show that you were present at an event.
>
> To claim the POAP for this event, [click on this link and submit the message](https://www.reddit.com/message/compose?to=<YOUR REDDIT BOT\>&subject=claim&message=<EVENT CODE\>). In a few minutes, you will receive a response from the bot that includes your claim link (or an error message).
>
> There are some important caveats to consider:
>
> \* No one should EVER ask for your private key or seed phrase. Guard these items with all of your might. When you receive a POAP claim link, you will be prompted to enter your wallet address, this wallet address is public.
>
> \* We highly suggest that you use an unfunded Ethereum wallet to claim POAPs. It's not good practice to link your POAP badges to your assets.
>
> \* Collecting POAPs is cool, but when you have enough, the wallet can easily be linked to you. This is GOOD and fun, but you don't want to dox your assets.
>
> \* POAPs tools do not interface well with hardware wallets, we recommend using a native metamask wallet for easy POAP management.
> 
> \* Your reddit account must be <YOUR EVENT ACCOUNT AGE MINIMUM\> and have <YOUR EVENT KARMA MINUMUM\> karma to claim this badge.

## Admin via Reddit
Administration of the bot can be performed using commands issued via Reddit private messages (not the newer reddit chat feature). The permission model for this is currently rudimentary. It consists of only a whitelist of reddit usernames controlling access to these commands. This whitelist can only be updated via the API.

To issue a command simply send a private message to the bot user following the formats outlined below. The following link will show you an example: [Example Command](https://www.reddit.com/message/compose?to=/u/YourPOAPBot&subject=command&message=create_event%20event_id%20event_name%20event_code%202021-05-01T00%3A00%3A00%202021-05-02T00%3A00%3A00%2030%2010)

The bot is strict about the format of these commands.
#### Create Event
```
create_event event_id event_name event_code start_date expiry_date minimum_age minimum_karma
```
#### Update Event
```
update_event event_id event_name event_code start_date expiry_date minimum_age minimum_karma
```
#### Get Event
```
get_event event_id
```
#### Create Claims
```
create_claims event_id code1,code2,code3
```
... more commands coming

## Admin via API

todo

# Setup
## Clone
First, clone the repository and change into the directory
```bash
git clone https://github.com/badinvestment/poap-reddit-bot.git
cd poap-reddit-bot
```

## Configuration

Configure [settings.yaml](settings.yaml) with reddit auth information


```yaml
reddit:
  auth:
    username: <reddit_username> # It's recommended to create a dedicated account, but you can use a personal account
    password: <reddit_password>
    client_id: <app_client_id>
    client_secret: <app_client_secret>
    user_agent: "POAPbot by /u/Bad_Investment https://github.com/badinvestment/poap-reddit-bot" # Optionally change this, but you don't need to

db:
  url: sqlite:///poap.db # Optionally rename sqlite db file (Postgres support coming soon)

poap:
  url: https://poap.xyz/claim/ # Optionally change POAP claim link. This link is forced when adding claims via Reddit DMs
```

## Deploy

Both of the below methods will start a webserver on your machine and by default expose the API at [localhost:8000](http://localhost:8000)

To interact with the API, the OpenAPI (Swagger) interface is available at [localhost:8000/docs](http://localhost:8000/docs)

ReDoc is also available at [localhost:8000/redoc](http://localhost:8000/redoc)

### Docker

To start the app server using docker-compose, run:
```bash
docker-compose up
```

### Python
To start the app server directly, run:
```bash
pip3 install -r requirements.txt # setup a virtual environment first, if desired
uvicorn poapbot.app:app #optional flags: --host 0.0.0.0 --port 8000
```
