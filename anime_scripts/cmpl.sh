#!/usr/bin/env bash

name="$1";
category="$2";
content_path="$3";
root_path="$4";
save_path="$5";
file_number="$6";
size="$7";
current_tracker="$8";
hash="$9";

export JF_DIR=/Anime/Jellyfin-Anime
cd /scripts

bash notif.sh "$name";

if [[ "$category" == "Anime" ]]; then
	echo "Running jellyfin namer and subtitle converter";
	if [[ -d "$root_path" ]]; then
		bash subtitle-converter.sh "$root_path";
		bash jellyfin-namer.sh "$root_path";
	else
		bash subtitle-converter.sh "$save_path";
		bash jellyfin-namer.sh "$save_path";
	fi
fi
