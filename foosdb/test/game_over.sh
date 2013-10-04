#!/bin/bash
curl -X POST -H "Content-Type: application/json" -d '@no_players.json' http://localhost:5000/players
