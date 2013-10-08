#!/bin/bash
sleep 4
curl -X POST -H "Content-Type: application/json" -d '@score_red_wins.json' http://localhost:5000/score
sleep 4
curl -X POST -H "Content-Type: application/json" -d '@score4.json' http://localhost:5000/score

