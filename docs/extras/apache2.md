# Apache2 Reverse Proxy

If you do not want to expose RocketMap to the web directly or you want to place it under a prefix, follow this guide:

Assuming the following:

 * You are running RocketMap on the default port 5000
 * You've already made your machine available externally

1. Install [Apache2](https://httpd.apache.org/docs/current/install.html) -- plenty of tutorials on the web for this.
2. Enable the mods needed
   ```
   sudo a2enmod proxy proxy_http proxy_connect ssl rewrite
   ```
3. Create a file /etc/apache2/sites-available/rocketmap.conf
   ```
   sudo nano /etc/apache2/sites-available/rocketmap.conf`
   ```
   copy pasta:
   ```
   <VirtualHost *:80>

       ServerName rocketmap.yourdomain.com

       ProxyPass / http://127.0.0.1:5000/
       ProxyPassReverse / http://127.0.0.1:5000/

       RewriteCond %{HTTP_HOST} !^rocketmap\.yourdomain\.com$ [NC]
       RewriteRule ^/$ http://%{HTTP_HOST}/ [L,R=301]

       ErrorLog ${APACHE_LOG_DIR}/error.log
       CustomLog ${APACHE_LOG_DIR}/access.log combined

   </VirtualHost>

   <VirtualHost *:443>

       ServerName rocketmap.yourdomain.com

       ProxyPass / http://127.0.0.1:5000/
       ProxyPassReverse / http://127.0.0.1:5000/

       RewriteCond %{HTTP_HOST} !^rocketmap\.yourdomain\.com$ [NC]
       RewriteRule ^/$ http://%{HTTP_HOST}/ [L,R=301]

       ErrorLog ${APACHE_LOG_DIR}/error.log
       CustomLog ${APACHE_LOG_DIR}/access.log combined

       SSLCertificateFile /var/www/ssl_keys/yourcert.crt
       SSLCertificateKeyFile /var/www/ssl_keys/yourkey.key
       SSLCertificateChainFile /var/www/ssl_keys/yourintermediatecert.crt

   </VirtualHost>
   ```
   If you want your maps at `rocketmap.yourdomain.com`, keep it just like it is
   If you want your maps at `yourdomain.com/go/` (note the trailing slash!)
   ```
   (take out ServerName)
   ProxyPass /go/ http://127.0.0.1:5000/
   ProxyPassReverse /go/ http://127.0.0.1:5000/

   RewriteCond %{HTTP_HOST} !^yourdomain\.com/go/$ [NC]
   RewriteRule ^/go/$ http://%{HTTP_HOST}/go/ [L,R=301]
   ```
4. Test your Apache2 config: `sudo apachectl configtest`
5. Enable your new config: `sudo a2ensite rocketmap`
6. Reload your Apache2 service: `service apache2 reload`
7. You can now access it by going to: `http(s)://yourdomain.com/go` or `http(s)://rocketmap.yourdomain.com`
