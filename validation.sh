
if [ $# -ne 1 ]; then
    echo need one argument as d4j buggy projects base dir! For example, ./D4J/projects/
    exit 1
fi
baseDir=$1
log=validation.log
pwd=`pwd`

# this is set to resume the validation
# Cli_25 patch-8 infinite loop
# Cli_8 patch-10 infinite loop
# Csv_1 patch-86 stuck
# Jsoup_49 patch-1 stuck

shouldSkip(){
    array=( "JacksonDatabind_70" "Cli_8" "Jsoup_45" "JacksonDatabind_57" "Jsoup_49" "JacksonDatabind_16" "Codec_3" "Codec_10" "Codec_18" "Jsoup_40" "Cli_11" "Codec_4" "JacksonDatabind_99" "Jsoup_41" "Csv_11" "Jsoup_47" "Compress_25" "Cli_17" "Jsoup_17" "Cli_25" "Jsoup_24" "Cli_28" "Jsoup_2" "JacksonDatabind_37" "Jsoup_15" "Cli_40" "Compress_19" "JacksonDatabind_1" "Jsoup_37" "Jsoup_26" "Compress_38" "Collections_26" "Codec_7" "Codec_9" "JacksonCore_5" "Csv_12" "JacksonDatabind_27" "Jsoup_43" "JacksonDatabind_107" "Jsoup_46" "Csv_1" "Jsoup_33" "Codec_17" "JacksonDatabind_34" "JacksonDatabind_82" "Jsoup_25" "JacksonCore_8" "JacksonDatabind_17" "JacksonXml_5" "JacksonCore_26" "Compress_1" "JacksonDatabind_97" "JacksonCore_11" "Codec_16" "JacksonDatabind_96" "Jsoup_39" "Jsoup_32" "Jsoup_35" "JacksonDatabind_71" )
    for element in ${array[@]}; do
        if [ "$element" = "$1" ]; then
            return 0
        fi
    done
    return 1
}

# to run again those stuck validation
shouldRun(){
    # array=( "Cli_25" "Cli_8" "Csv_1" "Jsoup_49" )
    array=( "Codec_2" "Compress_23" "Csv_14" "Csv_4" "Gson_11" "Gson_13" "Gson_15" "Gson_5" "JacksonCore_25" "JacksonDatabind_46" "Jsoup_34" "Jsoup_51" "Jsoup_86" )
    for element in ${array[@]}; do
        if [ "$element" = "$1" ]; then
            return 0
        fi
    done
    return 1
}

getSourceDir(){
    arg=$1
    id=${arg#*_}  # bug id
    name=${arg%_*}  # project name
    if [ $name = "Cli" ]; then
        if [ $id = "40" ]; then
            sourceDir="src/main/java/"
            return
        else 
            sourceDir="src/java/"
            return
        fi
    elif [ $name = "Codec" ]; then
        if [ $id -le 10 ]; then
            sourceDir="src/java/"
            return
        else 
            sourceDir="src/main/java/"
            return
        fi
    elif [ $name = "JxPath" ]; then
        sourceDir="src/java/"
        return
    elif [ $name = "Chart" ]; then
        sourceDir="source/"
        return
    else
        sourceDir="src/main/java/"
        return
    fi
}


# validation for each project
for proj in `ls $baseDir`; do
    # if [ ! -d $baseDir/$proj ] || shouldSkip $proj; then
    if [ ! -d $baseDir/$proj ] || ! shouldRun $proj; then
        continue
    fi
    cd $baseDir/$proj  # $proj: Chart_1
    echo -n > $log
    echo ====== Validation: $proj ====== >> $log
    echo ====== Validation: $proj ====== 

    # validaiton for each patch
    for patchId in `ls patches-pool`; do
        echo Validating patch-$patchId >> $log
        echo Validating $proj-$id patch-$patchId 
        # parse the path of patched java file
        cd patches-pool/$patchId
        patchPartialPath=`find . -name "*.java"`
        cd ../..
        # backup the original, firstly get source path
        getSourceDir $proj
        targetJavaFile=$sourceDir$patchPartialPath
        # if the target java file can not be found, then the source directory may be wrong
        if [ ! -f $targetJavaFile ]; then
            echo "[ERROR] The source directory may be wrongly identified: $targetJavaFile is not found"  >> $log
            continue
        fi
        [ ! -f $targetJavaFile.bak ] && cp $targetJavaFile $targetJavaFile.bak
        # replace 
        cp patches-pool/$patchId/$patchPartialPath $targetJavaFile
        echo testing...
        testResult=`timeout -k 10 180s defects4j test 2>&1`
        if [ "$?" -eq 124 ];then
            echo $proj patch-$patchId timed out! >> $log
        elif [[ $testResult == *"Failing tests: 0"* ]]; then
            echo $proj patch-$patchId is plausible patch! >> $log
        elif [[ $testResult == *"BUILD FAILED"* ]]; then
            echo $proj patch-$patchId fail to compile >> $log
        else 
            echo $proj patch-$patchId can not fix the bug >> $log
        fi
        cp $targetJavaFile.bak $targetJavaFile

    done
    cd $pwd

done