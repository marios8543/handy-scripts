#!/usr/bin/env bash

function get_bottom_dir() {
        IFS='/';
        read -ra ADDR <<< "$PWD";
        echo "${ADDR[-1]}";
        IFS=' ';
}

function name_clean() {
        local _out=$(echo "$1" | sed -e 's/\[[^][]*\]//g');
        _out=$(echo "$_out" | sed -e 's/([^()]*)//g');
        _out=$(echo "$_out" | sed 's/_/ /g');
        echo $(echo "$_out" | xargs);
}

cd "$1";

bottom_dir=$(get_bottom_dir);
cleaned_dir=$(name_clean "$bottom_dir");
mkdir "$JF_DIR/$cleaned_dir";

for i in *; do
        cleaned_name=$(name_clean "$i");
        ln "$PWD/$i" "$JF_DIR/$cleaned_dir/$cleaned_name" >/dev/null 2>/dev/null;
done;

