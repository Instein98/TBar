pwd=`pwd`
fixedD4jRepo="/home/yicheng/research/apr/experiments/uniapr-consistency/d4j_fixed_projects"  # only contains 2.0 projects
origD4jRepo="/home/yicheng/research/apr/experiments/uniapr-consistency/d4j_projects/"
validationRepo="./D4J/projects"
reportPath=$pwd"/validation.report"

report(){
    echo "$1" >> $reportPath
}

shouldSkip(){
    array=( "Cli_25" "Cli_8" "Csv_1" "Jsoup_49" )
    for element in ${array[@]}; do
        if [ "$element" = "$1" ]; then
            return 0
        fi
    done
    return 1
}

echo -n > $reportPath

for proj in `ls $validationRepo`; do
    cd $pwd
    if [ ! -d $validationRepo/$proj ]; then
    # if [ ! -d $validationRepo/$proj ] || shouldSkip $proj; then
    # if [ ! -d $validationRepo/$proj ] || ! shouldRun $proj; then
        continue
    fi
    report ""
    report "======================== $proj ========================"

    cd $validationRepo/$proj  # $proj: Chart_1

    projName=${proj%_*}  # Chart
    projId=${proj#*_}  # 1
    sourceDir=`defects4j export -p dir.src.classes`  # src/java
    modifiedClass=`defects4j export -p classes.modified`  # org.apache.commons.cli.CommandLine
    tmpPath=`echo $modifiedClass | sed 's|\.|/|g'`  # org/apache/commons/cli/CommandLine
    if [ ! -f validation.log ]; then
        report "[Error] No validation result found!!!"
        continue
    fi
    plausibleNum=`cat validation.log | grep plausible | wc -l`
    nonPlausibleNum=`cat validation.log | grep "can not fix" | wc -l`  # can be compiled but fail to fix
    cantCompileNum=`cat validation.log | grep "fail to compile" | wc -l`
    timeoutNum=`cat validation.log | grep "timed out" | wc -l`


    # show correct fix
    fixedJavaFile=$fixedD4jRepo/$projName/$projId/$sourceDir/$tmpPath.java
    buggyJavaFile=$origD4jRepo/$projName/$projId/$sourceDir/$tmpPath.java
    correctFix=`diff $buggyJavaFile $fixedJavaFile`
    report "****** Correct Fix (right side is the fixed file) ******"
    report "$correctFix"
    report ""

    report "# Plausible: $plausibleNum"
    report "# Non-plausible: $nonPlausibleNum  (can compile)"
    report "# Fail-to-compile: $cantCompileNum"
    report "# Timeout: $timeoutNum  (timeout threshold is set to 180s)"
    report ""


    for patchIdx in `cat validation.log | grep plausible | cut -d' ' -f2 | sed 's/patch-\(.*\)/\1/'`; do
        report "************************ plausible patch: $patchIdx ************************"
        patchFix=`diff $buggyJavaFile patches-pool/$patchIdx/$tmpPath.java`
        report "$patchFix"
        report ""
    done
done