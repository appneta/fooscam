#!/bin/bash
./game_on.sh
./fuzzy.sh
./score_test.sh
./game_over_by_players_left.sh
sleep 3
./game_on.sh
./fuzzy.sh
./score_test.sh
./game_on.sh
./game_over_by_score_to_zero_red.sh
sleep 3
./game_on.sh
./score_test.sh
./game_over_by_players_left.sh
sleep 3
./game_on.sh
./score_test.sh
./game_over_by_score_to_zero_blue.sh
sleep 3
