# this web application is to be used as a demo that the application 
# never looses connection to the db during password rotation
# simple flask app that reads some data

# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
from flask import Flask
import psycopg2 as pg2
 
# Flask constructor takes the name of 
# current module (__name__) as argument.
app = Flask(__name__)
 
# The route() function of the Flask class is a decorator, 
# which tells the application which URL should call 
# the associated function.
@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def hello_world():
    return 'Hello World'

@app.route('/categories')
def getAllCategories():

    getCategoriesQuery = "select * from edbuser.categories;"

    connection = pg2.connect(
        database="edbstore", user="webappuser", password="webappuser", host="54.144.132.79", port=5444)

    cursor = connection.cursor()

    cursor.execute(getCategoriesQuery)

    # Fetch all rows from database
    record = cursor.fetchall()

    return f"Data from Database:- {record}"
 
# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run()


