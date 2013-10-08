CREATE TABLE "games" (
    "id" INTEGER NOT NULL,
    "red_off" INTEGER,
    "red_def" INTEGER,
    "blue_off" INTEGER,
    "blue_def" INTEGER,
    "winner" TEXT,
    "blue_score" TEXT,
    "red_score" TEXT,
    "started" INTEGER,
    "ended" INTEGER,
    PRIMARY KEY (id)
);

CREATE TABLE "players" (
    "id" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE "state" (
    "id" INTEGER NOT NULL,
    "game_on" BOOLEAN NOT NULL,
    "red_off" INTEGER,
    "red_def" INTEGER,
    "blue_off" INTEGER,
    "blue_def" INTEGER,
    "red_score" INTEGER,
    "blue_score" INTEGER,
    "game_started" INTEGER,
    "fuzzy" BOOLEAN
);
