#!/bin/bash
rm dbback/*
sqlite3 foosball.db .dump | grep INSERT > dbback/db.sql
