#!/bin/bash

PID_list=(Chart Lang Math Time Mockito ) # no coverage for closure yet
for PID in "${PID_list[@]}"; do
  if [ $PID == "Chart" ]; then
    BID_list=( $(seq 1 26) )
  elif [ $PID == "Closure" ]; then
    BID_list=( $(seq 1 62) $(seq 64 92) $(seq 94 133) )
  elif [ $PID == "Lang" ]; then
    BID_list=( 1 $(seq 3 65) )
  elif [ $PID == "Math" ]; then
    BID_list=( $(seq 1 106) )
  elif [ $PID == "Mockito" ]; then
    BID_list=( $(seq 1 38) )
  elif [ $PID == "Time" ]; then
    BID_list=( $(seq 1 20) $(seq 22 27) )
  else
    echo "Unknown PID $PID in Defects4J 1.2.0, skipping..."
    continue
  fi

  for BID in "${BID_list[@]}"; do
    if [ -f patches/"$PID"_"$BID"/patches-pool/patches.info ]; then
      echo "patches.info already exists, skip $PID-$BID"
      continue
    elif [ -d patches/"$PID"_"$BID" ]; then
      echo "Incomplete patches pool for $PID-$BID, delete"
      rm -rf patches/"$PID"_"$BID"
    fi
    echo ====================================================
    echo "                     $PID $BID                      "
    echo ====================================================

    bugDataPath=/home/yicheng/research/d4jProj/
    bugID="$PID"_"$BID"
    defects4jHome=/home/yicheng/research/apr/experiments/defects4j/framework/bin/defects4j/
    time java -Xmx1g -cp "target/dependency/*" edu.lu.uni.serval.tbar.main.Main $bugDataPath $bugID $defects4jHome
  done
done

# bugDataPath=$1
# bugID=$2
# defects4jHome=$3

# java -Xmx1g -cp "target/dependency/*" edu.lu.uni.serval.tbar.main.Main $bugDataPath $bugID $defects4jHome