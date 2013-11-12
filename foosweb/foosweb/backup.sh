#!/bin/bash
mv dbback/db.sql dbback/db-`date +%F-%Hh-%Mm`.sql
sqlite3 foosball.db .dump | grep INSERT > dbback/db.sql
