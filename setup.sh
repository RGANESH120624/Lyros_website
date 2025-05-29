#!/bin/bash

mkdir -p ~/.streamlit/

echo "\
[general]
email = \"redaganiganesh67@gmail.com\"
" > ~/.streamlit/credentials.toml

echo "\
[server]
headless = true
enableCORS = false
" > ~/.streamlit/config.toml
