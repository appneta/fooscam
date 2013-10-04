#!/bin/bash
curl -X POST -H "Content-Type: application/json" -d '@score.json' http://localhost:5000/score
