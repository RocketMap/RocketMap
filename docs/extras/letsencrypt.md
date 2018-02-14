# Let's Encrypt with Certbot

This page is to assist you in generating a free SSL certificate from Let's Encrypt using the certbot client. Please note that this tutorial is for Linux based systems. Windows users must use the non-certbot method.

To begin, you will need to install certbot on your system. Use [this great page](https://certbot.eff.org/) provided by the EFF to figure out how you need to install certbot on your system. Please follow the instructions on the EFF site, otherwise you may end up with an outdated client, or a different one entirely.

After installing certbot, you can use one of many methods to obtain a certificate.

Before continuing, be sure to create backups of your web server configurations as it cannot be guaranteed that certbot will not break them.

## Webroot

Certbot can automatically detect your webserver's webroot, and complete the verification automatically, in addition to updating your webserver configuration itself.

For Nginx users:
```
sudo certbot --authenticator webroot --installer nginx
```
For Apache users:
```
sudo certbot --authenticator webroot --installer apache
```
Certbot will ask you which domain name you wish to activate HTTPS for. Select the appropriate domain, and allow the verification to complete.

If you see the following message:
```
Congratulations! Your certificate and chain have been saved at
   /etc/letsencrypt/live/example.com/fullchain.pem.
```
Congratulations! Your SSL certificate was successfully generated and installed.

If you want to update your webserver configuration manually, you should manually specify your webroot and domain, such as:
```
sudo certbot certonly --webroot -w /var/www/example.com/ -d example.com
```

## Standalone Webserver
You can also have Certbot generate a certificate using its own webserver. If you want to keep certbot's grubby hands off your webserver, this is the best method.

This method is slightly different from the webroot method, as it requires you to stop your webserver so that certbot can spin up its own. The best method to do this is with pre and post hooks. For example:

For Nginx users:
```
sudo certbot --authenticator standalone --installer nginx --pre-hook "service nginx stop" --post-hook "service nginx start"
```
For Apache users:
```
sudo certbot --authenticator standalone --installer apache --pre-hook "service apache2 stop" --post-hook "service apache2 start"
```

This is a much nicer method, as it consolidates everything into a single command and passes it all to certbot, which will take care of everything by itself. In addition, if you decide to setup automatic renewals, this will make your crontab considerably cleaner. However, if you wish, you can start/stop your webserver manually as such:

```
sudo service nginx/apache2 stop
[certbot command]
sudo service nginx/apache2 start
```

Note that these examples will automatically edit the webserver configuration. If you wish to update the configuration yourself, simply remove --installer apache/nginx from the command.

## Renewing Certificates
Let's Encrypt will send you emails when the certificate is reaching expiration. If your certificate is reaching expiration, you will need to renew it. The command for renewing certificates will vary depending on the method you used to generate the certificate.

If you used the webroot authenticator with automatic install, you can simply execute `sudo certbot renew`.

If you used the webroot authenticator with manual install, you can simply execute `sudo certbot renew --post-hook "service nginx restart"`. If you are using Apache2, replace "nginx" with "apache2".

If you used either of the standalone authenticators, you can use these commands:

For Nginx users:
```
sudo certbot renew --pre-hook "service nginx stop" --post-hook "service nginx start"
```
For Apache users:
```
sudo certbot renew --pre-hook "service apache2 stop" --post-hook "service apache2 start"
```

## Automatic Renewals
Setting up automatic renewals is very simple with cron. The example below runs the renewal task daily, you can change this to run weekly, but it is not recommended. To start, you need to become root on your system (if you aren't already), either by using `su` directly, or `sudo su`.

Afterwards, run `crontab -e`. This will open the crontab for the root user.

From here, you can input the following at the end of the file:
```
0 3 * * * certbotcommandhere
```

This will run the renewal at 3am system time every day. Replace `certbotcommandhere` with the command given under the "Renewing Certificates" section. Remove sudo from the beginning of the commands, as the cron job will be running as root. Save and quit the file.

You have now setup automatic renewal of your Let's Encrypt certificate.
