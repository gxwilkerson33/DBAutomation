# this script is written focused on postgres. Other databases may need more configuration. 
# this script rotates credentials on the db cluster
# this script will then update the associated applications/users
# this script should be called in some automation tool (ansible)

import psycopg2 as pg2
import secrets
import string
alphabet = string.ascii_letters + string.digits


# the design of using global connection and cursor objects needs review. This is just to show the general functionality.
# care should be taken in a production environment to manage connections to the DBs. 

# global connection for the script
# creds and config should be fetched from cmdb
# creds for cmdb can be passed in command line args or fetched from another cred management solution.
# This is dependant on what the org is already using and considers best practice
connection = pg2.connect(database="edb", user="enterprisedb",
                         password="edb", host="52.3.240.230", port=5444)

# global cursor for the script
cursor = connection.cursor()


def rotateAndUpdatePasswords():
    # all users that are not the superuser
    # should be fetched from cmdb
    getAllUsers = "select pg_user.usename from pg_catalog.pg_user \
        where not pg_user.usename = 'enterprisedb';"

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
        updateConfigForAppsUsingUser(tempUseName, tempPass)
        newPass = alterUserQuery(usename)
        updateConfigForAppsUsingUser(usename, newPass)
        dropTempUser(tempUseName)
        print(usename)
        print(newPass)

def updateConfigForAppsUsingUser(newUsername, password):
    """ 
    function to swap credentials that apps are using 

    Parameters:
        new: the usename to update the application to use
        password: the new password to use
    """

    # This is the more complex part of this script that will be specific to the org/systems using it. 
    # if apps are run in kubernetes we can update config maps and secrets
    # the goal here is to automate the rotation of the credentials with zero downtime of the application

    # for now we will jsut update local env vars using dbcreds.env. In a real world scenario we will need to
    # fetch info from cmdb? to update all servers/apps with new credentials based on what current usename is passed in
    f = open("postgres/password_rotation/dbcreds.env", "w")
    f.write(f"webapppassword={password}\nwebapp_user={newUsername}\ndbhost=52.3.240.230")
    f.close()


def alterUserQuery(usename: str):
    """
        The function generates a new secure password and alters the user with it. 
    """
    newPassword = generateRandomSecurePassword(20)
    query = f"alter user {usename} with password '{newPassword}'"
    executeAndCommitQuery(query)
    return newPassword

def createTempUser(usename):
    """ The function creates a temp user from the original user with a new secure password.
        returns: the temp username and password 
    """
    tempUser = f"{usename}_temp"
    tempPass = generateRandomSecurePassword(20)

    tempUserQuery = f"create user {tempUser} with login password '{tempPass}' in role {usename};"
    executeAndCommitQuery(tempUserQuery)

    return tempUser, tempPass

def dropTempUser(tempUseName):
    """ drop the temp user that was created for password rotation """
    dropUserQuery = f"drop user {tempUseName};"
    executeAndCommitQuery(dropUserQuery)

def generateRandomSecurePassword(length: int):
    """generates a random and secure password of letters and digits of given length"""
    return f"{''.join(secrets.choice(alphabet) for i in range(length))}"

def executeAndCommitQuery(query:str):
    """Executes and commits the given query"""
    cursor.execute(query)
    connection.commit()

if __name__ == '__main__':
    rotateAndUpdatePasswords()
