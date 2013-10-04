fooscam
=======

the spit and bailing wire which holds the foosball monitoring system together

![screenshot](https://github.com/appneta/fooscam/blob/master/fooscam.png?raw=true)

foosdb - the web app which montiors games and tracks stats

* foosweb.py - flask webapp to monitor status of table

foostools - the opencv projects to analyze video stream and update foosweb

* readScore - study the colourful cubes, their meanings are difficult to know 
* detectPlayers - read the low fi QR codes players throw down to id themselves for stat tracking
