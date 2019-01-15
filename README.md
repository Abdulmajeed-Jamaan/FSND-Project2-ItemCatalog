# Item Catalog - Udacity
### Full Stack Web Development ND
_______________________
## About
 This work, is a part of the Full Stack ND, this will combine your knowledge of building dynamic websites with persistent data storage to create a web application that provides a compelling service to your users and learn how to develop a RESTful web application using the Python framework Flask along with implementing third-party OAuth authentication. You will then learn when to properly use the various HTTP methods available to you and how these methods relate to CRUD (create, read, update and delete) operations..

 the database have three tables :
   - User.
   - Item.
   - Category.

_______________________
## Prerequisites
  - download and install python (https://www.python.org/downloads/).
  - download and install virtual box (https://www.virtualbox.org/wiki/Downloads).
  - download and install vagrant (https://www.vagrantup.com/downloads.html).
  - go to directory of the file using git bash.
  - run vagrant up.
  - run vagrant ssh.

## Run the code
  - inside the VM go to Catalog directory.
  - run seeder.py file.
  - run application.py file.
  - run http://localhost:5000 on your chrome browser.

_______________________
## Files
  - application.py main file .
  - seeder.py temporary data file.
  - database_setup.py database file.
  - client_secrets.py OAuth file.
  - templates file for html files.

_______________________

## How to login with third party
  - click on google sign in button on the top right.
  - login to your google account.
  - then it will create new account for you (if you never signed in before).
  - then it will refresh the page directly .
  - after refresh there will be logout button at the same place

_______________________

## JSON Links
- for all categories with their items : /catalog/JSON
- for all items in the category : /catalog/<string:category_title>/items/JSON
- for specific item in category : /catalog/<string:category_title>/<string:item_title>/JSON
