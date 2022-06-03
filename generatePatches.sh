# Note: To generate patches, you need to modify:
# 1) tbar/src/main/java/edu/lu/uni/serval/tbar/utils/PathUtils.java
# 2) tbar/BugPositions.txt
# 3) run `defects4j test` and put the result in FailedTestCases dir

dir=D4J/projects/ # Store the buggy projects.
d4jPath=/home/yicheng/research/apr/experiments/defects4j/

# echo -n > patchGen.log
# for name in `cat oneLinePatchedProj.log`; do
#     echo generating patch for $name
#     ./fixedPerfectRunner.sh D4J/projects/ $name $d4jPath true >> patchGen.log 2>&1 
#     # ./fixedPerfectRunner.sh $dir $name $d4jPath true
#     echo
# done

echo -n > patchGen.log
array=( "Codec_2" "Compress_23" "Csv_14" "Csv_4" "Gson_11" "Gson_13" "Gson_15" "Gson_5" "JacksonCore_25" "JacksonDatabind_46" "Jsoup_34" "Jsoup_51" "Jsoup_86" )
for name in ${array[@]}; do
    echo generating patch for $name | tee -a patchGen.log
    ./fixedPerfectRunner.sh D4J/projects/ $name $d4jPath true >> patchGen.log 2>&1 
    # ./fixedPerfectRunner.sh $dir $name $d4jPath true
    echo  | tee -a patchGen.log
done