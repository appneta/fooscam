#!/bin/bash
sleep 4
curl -X POST -H "Content-Type: application/json" -d '@players.json' http://localhost:5000/players
