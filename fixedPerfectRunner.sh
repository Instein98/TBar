#!/bin/bash

if [ `git rev-parse HEAD` != f1e1bec02cb3e6157ae57faa988adaad9c179d28 ]; then
    git checkout f1e1bec02cb3e6157ae57faa988adaad9c179d28
    mvn compile
fi

bugDataPath=$1
bugID=$2
defects4jHome=$3
isTestFixPatterns=$4

[ -f target/dependency/TBar-0.0.1-SNAPSHOT.jar ] && mv target/dependency/TBar-0.0.1-SNAPSHOT.jar target/TBar-0.0.1-SNAPSHOT.jar.bak

# java -Xmx1g -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=0.0.0.0:5005 -cp "target/dependency/*:target/classes" edu.lu.uni.serval.tbar.main.MainPerfectFL $bugDataPath $bugID $defects4jHome $isTestFixPatterns
java -Xmx1g -cp "target/dependency/*:target/classes" edu.lu.uni.serval.tbar.main.MainPerfectFL $bugDataPath $bugID $defects4jHome $isTestFixPatterns

# [ $? -ne 0 ] && echo "********** Did you run 'mvn compile'? **********"