# POAP Reddit Bot: Code distribution for POAP events
<img src="assets/poap-logo.svg" width="100" height="100"> <img src="assets/reddit-logo.png" width="100" height="100"> 

# Setup
```bash
git clone https://github.com/badinvestment/poap-reddit-bot.git
cd poap-reddit-bot
```

Configure [settings.yaml](settings.yaml) with reddit auth information


```yaml
reddit:
  auth:
    username: <reddit_username>
    password: <reddit_password>
    client_id: <app_client_id>
    client_secret: <app_secret>
    user_agent: "POAPbot by /u/Bad_Investment https://github.com/badinvestment/poap-reddit-bot"
```

## Docker

Coming soon

## Python
To start the app server, run:
```bash
pip3 install -r requirements.txt # setup a virtual environment first, if desired
uvicorn app:app #optional flags: --host 0.0.0.0 --port 8000
```
This will start a webserver on your machine and by default expose the API at [localhost:8000](http://localhost:8000)

To interact with the API, the OpenAPI (Swagger) interface is available at [localhost:8000/docs](http://localhost:8000/docs)

ReDoc is also available at [localhost:8000/redoc](http://localhost:8000/redoc)