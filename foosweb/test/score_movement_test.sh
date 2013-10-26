#!/bin/bash
sleep 4 
curl -X POST -H "Content-Type: application/json" -d '@score1.json' http://localhost:5000/score
sleep 4
curl -X POST -H "Content-Type: application/json" -d '@score2.json' http://localhost:5000/score
