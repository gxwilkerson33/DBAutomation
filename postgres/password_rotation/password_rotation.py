# this script is to call the sql code that will rotate the passwords
# this script will then update the associated applications/users
#   - for applications we will simulate this with updating env variables on the server
#   - for users we will send and email with encrypted? crendentials
#  this script should be called in some automation tool (ansible, cron?)

import psycopg2 as pg2
import os

connection = pg2.connect(database="edb", user="enterprisedb",
                         password="edb", host="34.232.67.249", port=5444)

cursor = connection.cursor()


def rotateAndUpdatePasswords():
    # db cluster superuser credentials
    password = os.getenv("PGPASSWORD")
    host = os.getenv("PGHOST")

    # all users that are not the superuser
    getAllUsers = "select pg_user.usename from pg_catalog.pg_user where not pg_user.usename = 'enterprisedb';"

    cursor.execute(getAllUsers)

    # Fetch all rows from database
    allDbUsers = cursor.fetchall()

    # for each user in the db cluster:
    # create tmp user
    # update the apps using that user
    # change password of original user
    # config  app to original user
    # drop temp user
    for i in allDbUsers:
        usename = i[0]
        tempUseName, tempPass = createTempUser(usename)
        updateConfigForAppsUsingUser(usename, tempUseName, tempPass)
        newPass = alterUserQuery(usename)
        updateConfigForAppsUsingUser(tempUseName, usename, newPass)
        dropTempUser(tempUseName)


def alterUserQuery(usename: str):
    """ alter user function """
    newPassword = "newRandomPassword6"
    cursor.execute(f"alter user {usename} with password '{newPassword}'")
    connection.commit()
    return newPassword


def createTempUser(usename):
    """ create temp user function """
    tempUserQuery = f"create user {usename}_temp with login password 'temp_password' in role {usename};"
    cursor.execute(tempUserQuery)
    connection.commit()
    return f"{usename}_temp", "temp_password"


def updateConfigForAppsUsingUser(current, new, password):
    """ 
    function to swap credentials that apps are using 

    Parameters:
        current: the curent usename being used by the application
        new: the usename to update the application to use
        password: the new password to use
    """

    # for now we will jsut update local env vars. In a real world scenario we will need to
    # fetch info from cmdb to update all servers/apps with new credentials based on what current usename is passed in

    # todo: update some env vars for the web app to use

    os.environ["webapppassword"] = password
    os.environ["webappuser"] = new


def dropTempUser(tempUseName):
    """ drop the temp user that was created for password rotation """
    dropUserQuery = f"drop user {tempUseName};"
    cursor.execute(dropUserQuery)
    connection.commit()


if __name__ == '__main__':
    rotateAndUpdatePasswords()
