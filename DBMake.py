import mysql.connector
import DBCredentials
import requests
from enum import Enum


class TableTypes(str, Enum):
    Restaurant = "restaurant"
    Products = "products"
    OptionGroups = "optiongroups"
    OptionIds = "optionids"
    ProductOptionGroups = "productoptiongroups"

class DBConnection:
    def __init__(self, host:str=DBCredentials.host, password:str=DBCredentials.password, username:str=DBCredentials.username, defaultDatabase:str="thuisbezorgd"):
        self.host:str = host
        self.user:str = username
        self.password:str = password
        self.database:str = defaultDatabase
        self.connection = self.getConnection()
        self.tableName = None

    def getConnection(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database)
        except:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password)
        return self.connection

    def execute(self, query:str, commit:bool = False):
        cursor = self.connection.cursor()
        cursor.execute(query)
        if commit:
            self.connection.commit()
        return cursor

    def executeMany(self, query:str, params, commit:bool = False):
        cursor = self.connection.cursor()
        cursor.executemany(query, params)
        if commit:
            self.connection.commit()
        return cursor

    def dropDatabase(self) -> None:
        self.execute(f"DROP DATABASE IF EXISTS {self.database}")

    def databaseExists(self) -> bool:
        cursor = self.execute(f"SHOW DATABASES LIKE '{self.database}'")
        return any(cursor.fetchall())

    def makeDatabase(self) -> bool:
        if not self.databaseExists():
            self.connection.cursor().execute(
                f"CREATE DATABASE {self.database}")
            return True
        return False

    def tableExists(self, table:str) -> bool:
        cursor = self.execute(f"SHOW TABLES LIKE '{table}'")
        return any(cursor.fetchall())

    def clearAllTables(self) -> None:
        for table in self.execute("SHOW TABLES").fetchall():
            self.execute(f"TRUNCATE TABLE {table[0]}", commit=True)

    def createTable(self, slug:str, chain:str,  type:TableTypes = TableTypes.Restaurant):
        statement = ""

        name = f"{slug.replace('-', '_')}"
        if len(name) > 34:
            name = name[:33] 
        name = f"{name}__{chain}" #Some ugly code, but tables have a length limit of 63 and because we add a maximum of 29 characters we cut it to 34 characters

        self.tableName = name

        match type:
            case TableTypes.Restaurant:
                statement = f"CREATE TABLE {name} (restaurantId VARCHAR(14), chain VARCHAR(8), name VARCHAR(128), slogan VARCHAR(250), slug VARCHAR(150), url VARCHAR(175), website VARCHAR(255), logo VARCHAR(175), address VARCHAR(200), UNIQUE KEY uniqueRestaurant (restaurantId))"
            case TableTypes.Products:
                statement = f"CREATE TABLE {name}__{type.value} (productId VARCHAR(16), name VARCHAR(128), category VARCHAR(200), description VARCHAR(1000), image VARCHAR(200), priceCents INT, UNIQUE KEY uniqueProductId (productId))"
            case TableTypes.ProductOptionGroups:
                statement = f"CREATE TABLE {name}__{type.value} (productId VARCHAR(16), optionGroup VARCHAR(32), PRIMARY KEY (`productId`, `optionGroup`))"  
            case TableTypes.OptionGroups:
                statement = f"""CREATE TABLE {name}__{type.value} (optionGroup VARCHAR(32), optionId VARCHAR(16), name VARCHAR(200), PRIMARY KEY (`optionGroup`, `optionId`))"""
            case TableTypes.OptionIds:
                statement = f"CREATE TABLE {name}__{type.value} (optionId VARCHAR(32), name VARCHAR(75), priceCents INT, UNIQUE KEY uniqueOptionId (optionId))"
            case _:
                return None

        if (not self.tableExists(f"{name}__{type.value}") and type is not TableTypes.Restaurant) or (type is TableTypes.Restaurant and not self.tableExists(name)):
            return self.execute(statement)

    def insertInto(self, tableType:TableTypes, data:list[dict]|dict):
        if type(data) == dict:
            data = [data] #list().append(data) is slower

        statement = ""
        match tableType:
            case TableTypes.Restaurant:
                statement = f"INSERT INTO {self.tableName} (restaurantId, chain, name, slogan, slug, url, website, logo, address) VALUES (%(restaurantId)s, %(chain)s, %(name)s, %(slogan)s, %(slug)s, %(url)s, %(website)s, %(logo)s, %(address)s)"
            case TableTypes.Products:
                statement = f"INSERT INTO {self.tableName}__{tableType.value} (productId, name, category, description, image, priceCents) VALUES (%(productId)s, %(name)s, %(category)s, %(description)s, %(image)s, %(priceCents)s)"
            case TableTypes.ProductOptionGroups:
                statement = f"INSERT INTO {self.tableName}__{tableType.value} (productId, optionGroup) VALUES (%(productId)s, %(optionGroup)s)"
            case TableTypes.OptionGroups:
                statement = f"INSERT INTO {self.tableName}__{tableType.value} (optionGroup, optionId, name) VALUES (%(optionGroup)s, %(optionId)s, %(name)s)"
            case TableTypes.OptionIds:
                statement = f"INSERT INTO {self.tableName}__{tableType.value} (optionId, name, priceCents) VALUES (%(optionId)s, %(name)s, %(priceCents)s)"
            case _:
                return None

        try:
            return self.executeMany(statement, data, commit=True)
        except mysql.connector.errors.IntegrityError as e:
            print(e)
            return None
        except mysql.connector.errors.DataError as e:
            print(e, data)
            raise Exception