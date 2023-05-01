import mysql.connector as mysql
import os
# top secrekt xD
# GRANT ALL ON *.* TO 'honecker'@'localhost' IDENTIFIED BY '123' WITH GRANT OPTION;
# CREATE DATABASE honeckerdb;

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'database': DB_NAME
}


def initdb():
    conn = mysql.connect(**config)
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS Quotes('
              'id INT NOT NULL AUTO_INCREMENT,'
              'name VARCHAR(255) NOT NULL,'
              'quote VARCHAR(5000) NOT NULL,'
              'addedby VARCHAR(255) NOT NULL,'
              'timestamp VARCHAR(255) NOT NULL,'
              'PRIMARY KEY (id) )')

    c.execute('CREATE TABLE IF NOT EXISTS Stasi('
              'Username VARCHAR(255) NOT NULL,'
              'Credits INT NOT NULL,'
              'PRIMARY KEY (Username)')

    c.execute('CREATE TABLE IF NOT EXISTS Dokaukset('
              'id INT NOT NULL AUTO_INCREMENT,'
              'date DATE NOT NULL,'
              'reason VARCHAR(500) NOT NULL,'
              'addedby VARCHAR(255) NOT NULL,'
              'timestamp TIMESTAMP NOT NULL,'
              'PRIMARY KEY (id)')

    conn.commit()
    conn.close()
