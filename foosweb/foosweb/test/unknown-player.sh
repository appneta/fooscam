#!/bin/bash
sleep 4
curl -X POST -H "Content-Type: application/json" -d '@unknown-player.json' http://localhost:5000/players
