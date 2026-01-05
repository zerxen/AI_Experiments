#!/bin/bash
ssh-keygen -E md5 -lf ./iol_rsa.pub | sed 's/://g' | sed 's/MD5//g' | awk '{print $2}' | tr '[:lower:]' '[:upper:]'