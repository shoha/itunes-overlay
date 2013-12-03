itunes-overlay
==============

A small Python program which uses the iTunes COM and socketIO to serve an entirely customizable "now playing" overlay for video streams.


How to Use
==============

Run dist/itunes_song_info_threaded.exe

iTunes will launch automatically if it was not already running. The program will serve index.html at localhost:8080. To display it as an overlay you can use [Faruton's CLR Browser Source](https://obsproject.com/forum/viewtopic.php?f=11&t=6714) plugin for OBS (settings should look like [this](http://i.imgur.com/8xxgmnq.png) , or screen region a browser pointed to localhost:8080 and then chroma/color key.