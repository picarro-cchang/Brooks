Instructions for using the node app that is investigator

mongo node-login seedAdmin.js

This gives you an admin user called admin@picarro.com who can add other users.
The password is a secret.  
Hint: the password is awesome 

Run the app with 

    export NODE_ENV=development; node app

Using the development environment assumes you have a mongo instance running on your local environment at port 27017.

You can view the config file in app/config.js if you want to play with environment settings.

