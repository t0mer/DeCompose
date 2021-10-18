*Please :star: this repo if you find it useful*

<p align="left"><br>
<a href="https://www.paypal.com/paypalme/techblogil?locale.x=he_IL" target="_blank"><img src="http://khrolenok.ru/support_paypal.png" alt="PayPal" width="250" height="48"></a>
</p>



# DeCompose
DeCompose is [FastAPI](https://fastapi.tiangolo.com/) based web application helps us to generate docker-compose file from existing containers.
With a very simple UI you can generate docker-compose file for any existing container (Running or not),
Just nevigate to DeCompose address and start generating.

DeCompose source code is available on GitHub via [https://github.com/t0mer/DeCompose](https://github.com/t0mer/DeCompose)

[![Face Registring](https://github.com/t0mer/DeCompose/blob/main/decompose.png?raw=true "Face Registring")](https://github.com/t0mer/DeCompose/blob/main/decompose.png?raw=true "Face Registring")

## DeCompose Features
- Generating docker-compose to online editor.
- Generating docker-compose to file.
- Swagger api documentation.

## Swagger api documentation.
DeCompose includes API and Swagger so you can automate the docker-compose generating. this gives you the abillity 
to backup your compose files remotely.

[![Face Registring](https://github.com/t0mer/DeCompose/blob/main/decompose%20swagger.png?raw=true "Face Registring")](https://github.com/t0mer/DeCompose/blob/main/decompose%20swagger.png?raw=true "Face Registring")

The API contains three get methods:
- /api/containers - Returns list of existing containers.
- /api/generate - Generates docker-compose and returns it as string.
- /api/download - Generates docker-compose and returns it as file.

# Installation


#### Deepstack Trainer Installation
Deepstack Trainer installation is very easy using docker-compose:
```
version: "3.7"

services:
  decompose:
    image: techblog/decompose
    container_name: decompose
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8080:8080"   
```


# Components and Libraries used in DeCompose
* [Docker autocompose](https://github.com/Red5d/docker-autocompose)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Bootstrap](https://getbootstrap.com/docs/5.0/getting-started/introduction/)
* [jQuery-ace](https://cheef.github.io/jquery-ace/)
