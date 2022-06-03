dir=D4J/projects/ # Store the buggy projects.

check_path(){
    str=""
    # source main
    if [ -d source ]; then
        str=$str:source
    elif  [ -d src/main/java ]; then
        str=$str:"/src/main/java/"
    elif  [ -d src/java ]; then
        str=$str:"/src/java/"
    elif  [ -d src ]; then
        str=$str:"/src/"
    fi

    # source test
    if [ -d src/test/java ]; then
        str=$str:"/src/test/java/"
    elif  [ -d src/test ]; then
        str=$str:"/src/test/"
    elif  [ -d tests ]; then
        str=$str:"/tests/"
    elif  [ -d test ]; then
        str=$str:"/test/"
    fi

    # class main
    if [ -d build/classes/main ]; then
        str=$str:"/build/classes/main/"
    elif  [ -d build/classes ]; then
        str=$str:"/build/classes/"
    elif  [ -d build ]; then
        str=$str:"/build/"
    elif  [ -d target/classes ]; then
        str=$str:"/target/classes/"
    fi

    # class test
    if [ -d build/classes/test ]; then
        str=$str:"/build/classes/test/"
    elif  [ -d target/test-classes ]; then
        str=$str:"/target/test-classes/"
    elif  [ -d target/tests ]; then
        str=$str:"/target/tests/"
    elif  [ -d build-tests ]; then
        str=$str:"/build-tests/"
    elif  [ -d build/tests ]; then
        str=$str:"/build/tests/"
    elif  [ -d build/test ]; then
        str=$str:"/build/test/"
    fi

    echo -n $str
}
# "/target/classes/"
# "/build/"
# "/build/classes/"
# "/build/classes/main/"

# "/build/classes/test/"
# "/build/test/"
# "/build-tests/"
# "/build/tests/"
# "/target/tests/"
# "/target/test-classes/"

# "/source/"
# "/src/"
# "/src/java/"
# "/src/main/java/"

# "/test/"
# "/tests/"
# "/src/test/"
# "/src/test/java/"

# for name in `cat oneLinePatchedProj.log`; do
array=( "Codec_2" "Compress_23" "Csv_14" "Csv_4" "Gson_11" "Gson_13" "Gson_15" "Gson_5" "JacksonCore_25" "JacksonDatabind_46" "Jsoup_34" "Jsoup_51" "Jsoup_86" )
for name in ${array[@]}; do
    proj=${name%_*}
    bug=${name#*_}

    [ ! -d ${dir}${proj}_${bug} ] && defects4j checkout -p $proj -v ${bug}b -w ${dir}${proj}_${bug}
	cd ${dir}${proj}_${bug}
    # rm -rf build
    # rm -rf target
    # rm -rf build-tests
	# defects4j compile
    # defects4j test > ../../../FailedTestCases/${proj}_${bug}.txt
    check_path
    echo -- ${proj}_${bug} 

	cd ../../../
done