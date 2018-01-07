# Docker

Docker is a great way to run "containerized" applications easily and without installing tons of stuff into your computer.

If you are not familiar or don't feel confortable with Python, pip or any of the other the other stuff involved in launching a RocketMap server, Docker is probably the easiest approach for you.

## Prerequisites

* [Docker](https://www.docker.com/products/docker)
* Google Maps API Key

## Introduction

The quickest way to get RocketMap up and running with docker is quite simple. However you need to setup an external mysql database to make it work so be sure to read the tutorial until the "Advanced Docker Setup"

## Simple Docker Setup

### Starting the server

In order to start the map, you've got to run your docker container with a few arguments, such as authentication type, account, password, desired location and steps. If you don't know which arguments are necessary, you can use the following command to get help:

```
docker run --rm frostthefox/rocketmap -h
```

To be able to access the map in your machine via browser, you've got to bind a port on your host machine to the one wich will be exposed by the container (default is 5000). The following docker run command is an example of to launch a container with a very basic setup of the map, following the instructions above:

```
docker run -d --name pogomap -p 5000:5000 \
  frostthefox/rocketmap \
    -a ptc -u username -p password \
    -k 'your-google-maps-key' \
    -l 'lat, lon' \
    -st 5
```

If you would like to see what are the server's outputs (console logs), you can run:

```
docker logs -f pogomap
```

Press `ctrl-c` when you're done.

### Stopping the server

In the step above we launched our server in a container named `pogomap`. Therefore, to stop it as simple as running:

```
docker stop pogomap
```

After stopping a named container, if you would like to launch a new one re-using such name, you have to remove it first, or else it will not be allowed:

```
docker rm pogomap
```

### Local access

Given that we have bound port 5000 in your machine to port 5000 in the container, which the server is listening to, in order to access the server from your machine you just got to access `http://localhost:5000` in your preferred browser.

### External access

If external access is necessary, there are plenty of ways to expose you server to the web. In this guide we are going to approach this using a [ngrok](https://ngrok.com/) container, which will create a secure introspected tunnel to your server. This is also very simple to do with Docker. Simply run the following command:

```
docker run -d --name ngrok --link pogomap \
  wernight/ngrok \
    ngrok http pogomap:5000
```

After the ngrok container is launched, we need to discover what domain you've been assigned. The following command can be used to obtain the domain:

```
docker run --rm --link ngrok \
  appropriate/curl \
    sh -c "curl -s http://ngrok:4040/api/tunnels | grep -o 'https\?:\/\/[a-zA-Z0-9\.]\+'"
```

That should output something like:

```
http://random-string-here.ngrok.io
https://random-string-here.ngrok.io
```

Open that URL in your browser and you're ready to rock!

## Updating Versions

In order to update your RocketMap docker image, you should stop/remove all the containers running with the current (outdated) version (refer to "Stopping the server"), pull the latest docker image version, and restart everything. To pull the latest image, use the following command:

```
docker pull frostthefox/rocketmap
```

If you are running a ngrok container, you've got to stop it as well. To start the server after updating your image, simply use the same commands that were used before, and the containers will be launched with the latest version.

## Running on docker cloud

If you want to run RocketMap on a service that doesn't support arguments like docker cloud or ECS, you'll need to pass settings via variables below is an example:

```bash
  docker run -d -P \
    -e "POGOM_AUTH_SERVICE=ptc" \
    -e "POGOM_USERNAME=UserName" \
    -e "POGOM_PASSWORD=Password" \
    -e "POGOM_LOCATION=Seattle, WA" \
    -e "POGOM_GMAPS_KEY=SUPERSECRET" \
    frostthefox/rocketmap
```

## Advanced Docker Setup

In this session, we are going to approach a docker setup that allows data persistence. To do so, we are going to use the docker image for [MySQL](https://hub.docker.com/_/mysql/) as our database, and have our server(s) connect to it. This could be done by linking docker containers. However, linking is considered a [legacy feature](https://docs.docker.com/engine/userguide/networking/default_network/dockerlinks/#/legacy-container-links), so we are going to use the docker network approach. We are also going to refer to a few commands that were used in the "Simple Docker Setup" session, which has more in-depth explanation about such commands, in case you need those.

### Creating the Docker Network

The first step is very simple, we are going to use the following command to create a docker network called `pogonw`:

```
docker network create pogonw
```

### Launching the database

Now that we have the network, we've gotta launch the database into it. As noted in the introduction, docker containers are disposable. Sharing a directory in you machine with the docker container will allow the MySQL server to use such directory to store its data, which ensures the data will remain there after the container stops. You can create this directory wherever you like. In this example we going to create a dir called `/path/to/mysql/` just for the sake of it.

```
mkdir /path/to/mysql/
```

After the directory is created, we can lauch the MySQL container. Use the following command to launch a container named `db` into our previously created network, sharing the directory we just created:

```
docker run --name db --net=pogonw -v /path/to/mysql/:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=yourpassword  -d mysql:5.6.32
```

The launched MySQL server will have a single user called `root` and its password will be `yourpassword`. However, there is no database/schema that we can use as the server will be empty on the first run, so we've gotta create one for RocketMap. This will be done by executing a MySQL command in the server. In order to connect to the server, execute this command:

```
docker exec -i db mysql -pyourpassword -e 'CREATE DATABASE pogodb'
```

That will do the trick. If you want to make sure the database was created, execute the following command and check if `pogodb` is listed:

```
docker exec -i db mysql -pyourpassword -e 'SHOW DATABASES'
```

### Relaunching the database

If the `db` container is not running, simply execute the same command that was used before to launch the container and the MySQL server will be up and running with all the previously stored data. You won't have to execute any MySQL command to create the database.

### Launching the RocketMap server

Now that we have a persistent database up and running, we need to launch our RocketMap server. To do so, we are going to use a slightly modified version of the docker run command from the "Simple Docker Setup" session. This time we need to launch our server inside the created network and pass the necessary database infos to it. Here's an example:

```
docker run -d --name pogomap --net=pogonw -p 5000:5000 \
  frostthefox/rocketmap \
    -a ptc -u username -p password \
    -k 'your-google-maps-key' \
    -l 'lat, lon' \
    -st 5 \
    --db-host db \
    --db-port 3306 \
    --db-name pogodb \
    --db-user root \
    --db-pass yourpassword
```

This will launch a container named `pogomap`. Just like before, in order to check the server's logs we can use:

```
docker logs -f pogomap
```

If you want more detailed logs, add the `--verbose` flag to the end of the docker run command.

If everything is fine, the server should be up and running now.

### Launching workers

If you would like to launch a different worker sharing the same db, to scan a different area for example, it is just as easy. We can use the docker run command from above, changing the container's name, and the necessary account and coordinate infos. For example:

```
docker run -d --name pogomap2 --net=pogonw \
  frostthefox/rocketmap \
    -a ptc -u username2 -p password2 \
    -k 'your-google-maps-key' \
    -l 'newlat, newlon' \
    -st 5 \
    --db-host db \
    --db-port 3306 \
    --db-name pogodb \
    --db-user root \
    --db-pass yourpassword
    -ns
```

The difference here being: we are launching with the `-ns` flag, which means that this container will only run the searcher and not the webserver (front-end), because we can use the webserver from the first container. That also means we can get rid of `-p 5000:5000`, as we dont need to bind that port anymore.

If for some reason you would like this container to launch the webserver as well, simply remove the `-ns` flag and add back the `-p`, with a different pairing as your local port 5000 will be already taken, such as `-p 5001:5000`.

### External Access

Just like before, we can use ngrok to provide external access to the webserver. The only thing we need to change in the command from the previous session is the `--link` flag, instead we need to launch ngrok in our network:

```
docker run -d --name ngrok --net=pogonw \
  wernight/ngrok \
    ngrok http pogomap:5000
```

To obtain the assigned domain from ngrok, we also need to execute the previous command in our network instead of using links:

```
docker run --rm --net=pogonw \
  appropriate/curl \
    sh -c "curl -s http://ngrok:4040/api/tunnels | grep -o 'https\?:\/\/[a-zA-Z0-9\.]\+'"
```

### Inspecting the containers

If at any moment you would like to check what containers are running, you can execute:

```
docker ps -a
```

If you would like more detailed information about the network, such as its subnet and gateway or even the ips that were assigned to each running container, you can execute:

```
docker network inspect pogonw
```

### Setting up notifications

If you have a docker image for a notification webhook that you want to be called by the server/workers, such as [PokeAlarm](https://github.com/kvangent/PokeAlarm), you can launch such container in the 'pogonw' network and give it a name such as 'hook'. This guide won't cover how to do that, but once such container is configured and running, you can stop your server/workers and relaunch them with the added flags: `-wh`, `--wh-threads` and `--webhook-updates-only`. For example, if the hook was listening to port 4000, and we wanted 3 threads to post updates only to the hook:

```
docker run -d --name pogomap --net=pogonw -p 5000:5000 \
  frostthefox/rocketmap \
    -a ptc -u username -p password \
    -k 'your-google-maps-key' \
    -l 'lat, lon' \
    -st 5 \
    --db-host db \
    --db-port 3306 \
    --db-name pogodb \
    --db-user root \
    --db-pass yourpassword \
    -wh 'http://hook:4000' \
    --wh-threads 3 \
    --webhook-updates-only
```
