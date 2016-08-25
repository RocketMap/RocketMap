SSL Certificate Windows
===================

Disclaimer: **If you can use letsencrypt, then do so, it is the preffered method for Linux users, Also If you can get achme set up and running on Windows, then use that. If not this guide is for you.**

Part 1: Register at StartSSL
----------------------------

Step 1 browse to: 

[StartSSL](https://www.startssl.com/ "StartSSL")

Step 2 click on Sign-Up: 

![Sign Up](http://i.imgur.com/NyQX4sz.png)

Step 3 Choose your country and pick an email address to receive a verification code at. **This email should not be disposable**:

![Pick An Email](http://i.imgur.com/mEFkrTL.png)

Step 4 Enter the verification code that they sent you to your non disposeable email:

![Verification Code](http://i.imgur.com/ytrNdCY.png)

Step 5 Now for the sake of easiness lets let the system generate the CSR for us. So in this step pick and confirm a password and then click submit:

![Password](http://i.imgur.com/lUIZZru.png)

Step 6 You should now be at this screen so click download files:

![Download](http://i.imgur.com/CpLTN52.png)

Step 7 A wild certificate is downloaded, you need this to login to www.startssl.com so lets click on it:

![Cert](http://i.imgur.com/diTLLCC.png)

Step 8 Click next:

![Next](http://i.imgur.com/la99fsw.png)

Step 9 Cleck next again:

![Next](http://i.imgur.com/6m11o9c.png)

Step 10 Now enter your password that you chose at www.startssl.com and press next:

![Password](http://i.imgur.com/4YzlTYO.png)

Step 11 Click next again:

![Next](http://i.imgur.com/sI8geV4.png)

Step 12 Now click finish:

![Import](http://i.imgur.com/68oIhUR.png)

Step 13 You should now see that the import was successful:

![Winning](http://i.imgur.com/MuW0IXx.png)

Step 14 Click login now:

![Login](http://i.imgur.com/49xEGjq.png)

Step 15 You will see a box like this come up with your certificate in it that you just imported. Click it then click okay. If prompted for a password enter your password that you used when createing it.

![Pick Cert](http://i.imgur.com/BnuIX2I.png)

Part 2: Validate Domain
-----------------------

Step 16 Click on validations wizard:

![Click it](http://i.imgur.com/cVzQ1aj.png)

Step 17 It should be on Domain Validation, if so click continue:

![Continue](http://i.imgur.com/WEulmXt.png)

Step 18 Enter a domain that you have access to an email address for (webmaster, or admin@domain.com) and press continue:

![Continue](http://i.imgur.com/8G7EZZd.png)

Step 19 Pick whichever email you have access to and then click send verification code, check your email and paste your verification code then press Validation:

![Receive email](http://i.imgur.com/52fg1V1.png)

Part 3 Get Your Certificate
---------------------------

Step 20 Once validated click certificates wizard:

![Click It](http://i.imgur.com/Xm7Vljx.png)

Step 21 We should be already on Web Server, if not click it then click continue:

![Continue](http://i.imgur.com/Krp8etS.png)

Step 22 You will now see a box like in this image and you will type your validated domain name, if you want to host from a subdomain that is fine too:

![Look at box](http://i.imgur.com/S9zneIS.png)

Step 23 We will generate our own CSR for this step, open bash, cmd, or git shell on your desktop and enter `openssl req -newkey rsa:2048 -keyout yourname.key -out yourname.csr` just like that for simplicity:

![Look I Did it too](http://i.imgur.com/UrIwfdi.png)

Step 24 It will ask you questions (first being a pass phrase and to confirm that phrase), fill everything out to the best of your ability, if you dont know the answer to something use `.`:

![Questions](http://i.imgur.com/YSNXXc5.png)

Step 25 When the script is done it will dump the files (yourname.key and yourname.csr) on your desktop:

![Files Have Appeared](http://i.imgur.com/WIlGc3P.png)

Step 26 Open yourname.csr with a text editor, I use sublime:

![Open It](http://i.imgur.com/Gf1p8ne.png)

Step 27 Copy and paste it all into [StartSSL](http://StartSSl.com) in the box asking you for the CSR and press submit:

![CSR](http://i.imgur.com/yH3fv0q.png)

Step 28 It will show you a screen like this, if it says "Click here" then click on the "here" and it will download the certificates in a zipped folder:

![Seriously click here](http://i.imgur.com/1mlGieq.png)

Step 29 Wild certificate zip has appeared:

![Dat zip file though](http://i.imgur.com/ZVbz6Xj.png)

Part 4 Create the .PEM File For the Server
------------------------------------------

Step 30 Unzip that folder and open it up then unzip the other server folder and open that up it will have the intermediate, root and the certificate within it:

![Folders](http://i.imgur.com/D2LZuZ8.png)

Step 31 We will now combine these certs into one file in a certain way 

 - Open **your_domain_name.crt** in a text editor and copy it to a **new file**
 - Open the **intermediate certificate** in a text editor copy it and paste it in the file directly below **your_domain_name.crt**
 - Repeat the same exact thing with the **root certificate** and save this file as `cert.pem` (save it on your desktop) it should look similar to the image below:

![Similar](http://i.imgur.com/M5gol0s.png)

Step 32 Now the server needs yourname.key to be unencrypted to be able to function in SSL mode. So we will go back to shell on our desktop and type this `openssl rsa -in yourname.key -out private.key`:

![Look I Did It](http://i.imgur.com/Ncr0Piy.png)

Step 32 Enter the passphrase, if everything went well you will see this:

![I hope you remember it](http://i.imgur.com/u4SyvDm.png)

Step 33 We are pretty much done now you should have these two files on your desktop:

![Pretty files](http://i.imgur.com/g3Gz2Z3.png)

Part 5 Setup the Server
-----------------------
Step 34 Copy and paste these two files to your config folder open your config.ini in a text editor thats not notepad.exe and make the ssl lines look similar to mine (copy the path to each file into your config.ini):

![Similar](http://i.imgur.com/LGlYeRY.png)

Step 35 You should now be able to run the server in SSL mode if you followed this guide and if I didnt mess up somewhere along the way:

![Winning](http://i.imgur.com/c4Lacsx.png)

Step 36 Profit!
