#!/bin/bash

bugDataPath=$1
bugID=$2
defects4jHome=$3
isTestFixPatterns=$4

java -Xmx1g -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=5005 -cp "target/dependency/*" edu.lu.uni.serval.tbar.main.MainPerfectFL $bugDataPath $bugID $defects4jHome $isTestFixPatterns