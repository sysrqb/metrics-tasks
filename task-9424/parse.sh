#!/bin/bash
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

# get latest consensus info
curl -s -o data.json "https://onionoo.torproject.org/details?running=true&type=relay"

# find relays_published date and time
relays_published=`grep "relays_published" data.json | cut -d "\"" -f4`

# first seen (for lifetime)
for first_seen in `grep first_seen data.json | cut -d "\"" -f4`
do
    echo $relays_published,"first_seen",$first_seen
done

# last restarted (for uptime)
for last_restarted in `grep last_restarted data.json | cut -d "\"" -f4`
do
    echo $relays_published,"last_restarted",$last_restarted
done
IFS=$SAVEIFS
