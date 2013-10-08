#!/bin/bash
sleep 1
curl -X POST -H "Content-Type: application/json" -d '@lessplayers.json' http://localhost:5000/players
