# Status Page

Keeping track of multiple processes and accounts can be a pain. To help, you can use the status page to view the status of each of your workers and their accounts.

## Setup

There are two steps to enable the status page:
1. Set a password for the status page by adding the `-spp` argument to each worker running the web service or by setting the `status-page-password` field in `config.ini`. A password is required to enable the status page.
2. Give each of your workers a unique "status name" to identify them on the status page by setting the `-sn` argument.

## Accessing
To view your status page, go to `<YourMapUrl>/status` (for example, `http://localhost:5050/status`) and enter the password you defined. The status of each of your workers will be displayed and continually update.

## Screenshots

![Example Login Page](https://i.imgur.com/TEBNprW.png)
![Example Status Page](https://i.imgur.com/ieu5w1V.png)
