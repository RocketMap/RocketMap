# Amazon ECS

> **Warning** -- Most cloud providers have been IP blocked from accessing the API

Amazon ECS is essentially managed docker allowed you to run multi-container environments easily with minimal configuration. In this guide we'll create an ECS Task that will run a single RocketMap container with a MariaDB container for persisting the data

## Requirements

* AWS Account
* AWS ECS Cluster with at least one instance assigned
    * t2.micro type is sufficient for this setup

## Process

In the AWS ECS console create a Task Definition with the JSON below. You will need to set the following values:

* `POGOM_USERNAME` - username for pokemongo
* `POGOM_PASSWORD` - password for pokemongo
* `POGOM_AUTH_SERVICE` - Define if you are using google or ptc auth
* `POGOM_LOCATION` - Location to search
* `POGOM_DB_USER` - Database user for MariaDB
* `POGOM_DB_PASS` - Database password for MariaDB

```json
{
    "taskRoleArn": null,
    "containerDefinitions": [
        {
            "volumesFrom": [],
            "memory": 128,
            "extraHosts": null,
            "dnsServers": null,
            "disableNetworking": null,
            "dnsSearchDomains": null,
            "portMappings": [
                {
                    "hostPort": 80,
                    "containerPort": 5000,
                    "protocol": "tcp"
                }
            ],
            "hostname": null,
            "essential": true,
            "entryPoint": null,
            "mountPoints": [],
            "name": "pokemongomap",
            "ulimits": null,
            "dockerSecurityOptions": null,
            "environment": [
                {
                    "name": "POGOM_DB_TYPE",
                    "value": "mysql"
                },
                {
                    "name": "POGOM_LOCATION",
                    "value": "Seattle, WA"
                },
                {
                    "name": "POGOM_DB_HOST",
                    "value": "database"
                },
                {
                    "name": "POGOM_NUM_THREADS",
                    "value": "1"
                },
                {
                    "name": "POGOM_DB_NAME",
                    "value": "pogom"
                },
                {
                    "name": "POGOM_PASSWORD",
                    "value": "MyPassword"
                },
                {
                    "name": "POGOM_GMAPS_KEY",
                    "value": "SUPERSECRET"
                },
                {
                    "name": "POGOM_AUTH_SERVICE",
                    "value": "ptc"
                },
                {
                    "name": "POGOM_DB_PASS",
                    "value": "somedbpassword"
                },
                {
                    "name": "POGOM_DB_USER",
                    "value": "pogom"
                },
                {
                    "name": "POGOM_USERNAME",
                    "value": "MyUser"
                }
            ],
            "links": [
                "database"
            ],
            "workingDirectory": null,
            "readonlyRootFilesystem": null,
            "image": "frostthefox/rocketmap",
            "command": null,
            "user": null,
            "dockerLabels": null,
            "logConfiguration": null,
            "cpu": 1,
            "privileged": null
        },
        {
            "volumesFrom": [],
            "memory": 128,
            "extraHosts": null,
            "dnsServers": null,
            "disableNetworking": null,
            "dnsSearchDomains": null,
            "portMappings": [],
            "hostname": "database",
            "essential": true,
            "entryPoint": null,
            "mountPoints": [],
            "name": "database",
            "ulimits": null,
            "dockerSecurityOptions": null,
            "environment": [
                {
                    "name": "MYSQL_DATABASE",
                    "value": "pogom"
                },
                {
                    "name": "MYSQL_RANDOM_ROOT_PASSWORD",
                    "value": "yes"
                },
                {
                    "name": "MYSQL_PASSWORD",
                    "value": "somedbpassword"
                },
                {
                    "name": "MYSQL_USER",
                    "value": "pogom"
                }
            ],
            "links": null,
            "workingDirectory": null,
            "readonlyRootFilesystem": null,
            "image": "mariadb:10.1.16",
            "command": null,
            "user": null,
            "dockerLabels": null,
            "logConfiguration": null,
            "cpu": 1,
            "privileged": null
        }
    ],
    "volumes": [],
    "family": "rocketmap"
}
```


If you would like to add workers you can easily do so by adding another container with the additional variable `POGOM_NO_SERVER` set to `true`. You have to let one of the RocketMap containers start first to create the database, an easy way to control this is to create a link from the worker to the primary one as it will delay the start.

Once the Task is running you'll be able to access the app via the Instances IP on port 80.
