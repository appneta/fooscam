#!/bin/bash
curl -X POST -H "Content-Type: application/json" -d '@score1.json' http://localhost:5000/score
