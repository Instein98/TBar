import os, re
import shutil
import subprocess as sp
from pathlib import Path

processPool = []  # storing (cmd, cwd, process, logFileObj)
maxMultiProcess = 8

def runCmdAndWaitForFinish(cmd: list, cwd=None):
    process = sp.Popen(cmd, shell=False, stdout=sp.PIPE, stderr=sp.PIPE, cwd=cwd, universal_newlines=True)
    stdout, stderr = process.communicate()
    retCode = process.poll()
    return stdout, stderr, retCode

# Warning: if the logPath is not set, the process may stuck sometimes. See https://stackoverflow.com/a/39607358/11495796
def tryRunCmdWithProcessPool(cmd: list, logPath: str, cwd=None, insist=True):
    if len(processPool) >= maxMultiProcess:
        if insist:
            waitForProcessPoolSlotAvailable()
        else:
            return False
    stdout = sp.PIPE
    stderr = sp.PIPE
    logFileObj = None
    if logPath is not None:
        logFileObj = open(logPath, 'w')
        stdout = logFileObj
        stderr = logFileObj
    process = sp.Popen(cmd, shell=False, stdout=stdout, stderr=stderr, cwd=cwd, universal_newlines=True)  # shell=False by default
    cwd = '.' if cwd is None else cwd
    processPool.append((cmd, cwd, process, logFileObj))
    print("Process \"{}\"@\"{}\" has started and been added to the pool.".format(cmd, cwd))
    return True

def waitUntilMultiProcessLessThan(t):
    if len(processPool) >= t:
        print("[INFO] Waiting the number of parallel processes become less than " + str(t))
    while len(processPool) >= t:
        for cmd, cwd, process, logFileObj in processPool:
            retCode = process.poll()
            # haven't finished yet
            if retCode is None:
                continue
            else:
                print('=' * 10 + ' `{}` in "{}" Finished '.format(cmd, cwd) + '=' * 10)
                print('*' * 10 + ' RetCode: ' + str(retCode) + ' ' + ('*' * 10))
                # stdout, stderr = process.communicate()
                # print('*' * 10 + ' STDOUT ' + ('*' * 10))
                # if stdout is not None and len(stdout) > 0:
                    # print(stdout)
                # print('*' * 10 + ' STDERR ' + ('*' * 10))
                # if stderr is not None and len(stderr) > 0:
                    # print(stderr)
                print('=' * (20 + len(' `{}` in "{}" Finished '.format(cmd, cwd))))
                processPool.remove((cmd, cwd, process, logFileObj))
                if logFileObj is not None:
                    logFileObj.close()
                print('Found {} process in pool running'.format(len(processPool)))
                break

def waitForProcessPoolSlotAvailable():
    waitUntilMultiProcessLessThan(maxMultiProcess)

def waitForProcessPoolFinish():
    waitUntilMultiProcessLessThan(1)

# =============================================================================================

originalD4jProjDirPath = Path('../d4jProj').resolve()
tbarD4jProjDirPath = Path('tbarD4jProj').resolve()  # copy the project need to be fixed here
tbarD4jProjDirPath.mkdir(exist_ok=True)
bugPositionFile = Path('MutBenchBugPositions.txt').resolve()
patchesDirPath = Path('patches').resolve()
logDirPath = (Path('logs') / 'generation').resolve()
logDirPath.mkdir(exist_ok=True)
d4jHome = '/home/yicheng/research/apr/experiments/defects4j/'

def getFinishedProjPath():
    res = []
    for dir in originalD4jProjDirPath.iterdir():
        if dir.is_dir() and (dir / 'sampledMutIds.txt').exists():
            res.append(dir)
    return res

def file2Lines(filePath: Path):
    res = []
    with filePath.open() as f:
        for line in f:
            res.append(line.strip())
    return res

def getProjNameFromProjPath(projPath: Path):
    m = re.match(r'(\w+)-\d+f', projPath.stem)
    assert m is not None
    return m[1]

def getProjFormalNameFromProjSimpleName(name: str):
    formalNameWithCamel = ['JacksonCore', 'JacksonDatabind', 'JacksonXml', 'JxPath']
    for camelName in formalNameWithCamel:
        if name == camelName.lower():
            return camelName
    return name.title()

def getD4jProperty(projPath: Path, property: str):
    return sp.check_output("defects4j export -p {}".format(property), shell=True, universal_newlines=True, cwd=str(projPath)).strip()

def getD4jProjSrcRelativePath(projPath: Path):
    return getD4jProperty(projPath, 'dir.src.classes')

def genMutBenchBugPositions(targetFile=Path('./MutBenchBugPositions.txt')):
    positions = []
    for projPath in getFinishedProjPath():
        projSrcRelativePath = getD4jProperty(projPath, 'dir.src.classes')
        projName = getProjNameFromProjPath(projPath)
        mutLog = projPath / 'mutants.log'
        sampleTxt = projPath / 'sampledMutIds.txt'
        # print(str(projPath))
        assert mutLog.exists()
        assert sampleTxt.exists()
        mids = file2Lines(sampleTxt)
        minfos = file2Lines(mutLog)
        for mid in mids:
            info = minfos[int(mid)-1]
            assert info.startswith(mid + ":")
            m = re.match(r'.+:(.*?)@.*:(\d+):.+', info)
            assert m is not None
            buggyFileRelativePath = str(Path(projSrcRelativePath) / (m[1].replace('.', '/') + '.java'))
            buggyLineNum = m[2]
            positions.append('{}_{}@{}@{}'.format(projName, mid, buggyFileRelativePath, buggyLineNum))
    with targetFile.open(mode='w') as f:
        for line in positions:
            f.write(line + '\n')


def applyMutant(targetProjPath: Path, originalProjPath: Path, mid: str, srcRelativePath=None):
    # reset the targetProjPath
    sp.run('git checkout -- .', shell=True, universal_newlines=True, check=True, cwd=str(targetProjPath))
    # get the path of mutant java file
    mutantsDir = originalProjPath / 'mutants' / mid
    assert mutantsDir.exists()
    javaFileRelativePath = sp.check_output('find . -name *.java', shell=True, universal_newlines=True, cwd=str(mutantsDir)).strip()
    mutantPath = mutantsDir / javaFileRelativePath
    # get the patch of the java file to be replaced
    srcRelativePath = srcRelativePath if srcRelativePath is not None else getD4jProjSrcRelativePath(targetProjPath)
    fileToBeReplacedPath = targetProjPath / srcRelativePath / javaFileRelativePath
    shutil.copy(str(fileToBeReplacedPath), str(fileToBeReplacedPath) + '.bak')
    shutil.copy(str(mutantPath), str(fileToBeReplacedPath))
    sp.run("diff -s {} {}".format(str(fileToBeReplacedPath) + '.bak', str(fileToBeReplacedPath)), shell=True, universal_newlines=True)
    return str(fileToBeReplacedPath), javaFileRelativePath

def getMutFixedFileContent(projPath: Path, mutId: str, projSrcPath=None):
    mutLog = projPath / 'mutants.log'
    projSrcRelativePath = sp.check_output("defects4j export -p dir.src.classes", shell=True, universal_newlines=True, cwd=str(projPath), stderr=sp.DEVNULL).strip() if projSrcPath is None else projSrcPath
    shortPath = sp.check_output('find . -name "*.java"', shell=True, universal_newlines=True, cwd=str(projPath / 'mutants' / mutId)).strip()
    assert mutLog.exists()
    with mutLog.open() as log:
        for line in log:
            if line.startswith(mutId + ':'):
                m = re.match(r'.+:(.*?)@.*:(\d+):.+\n', line)
                if (m is None):
                    print("Mutant-{} has no match for '.+:(.*?)@.*:(\d+):.+\n' in line {}".format(mutId, line))
                assert m is not None
                lineNum = int(m[2])
                javaFilePath = projPath / (projSrcRelativePath + '/' + shortPath)
                with javaFilePath.open() as f:
                    return f.read()

def getMutLineNum(projPath: Path, mutId: str):
    mutLog = projPath / 'mutants.log'
    assert mutLog.exists()
    with mutLog.open() as log:
        for line in log:
            if line.startswith(mutId + ':'):
                m = re.match(r'.+:(\d+):.+\n', line)
                if (m is None):
                    print("Mutant-{} has no match for '.+:(\d+):[^:]+' in line {}".format(mutId, line))
                assert m is not None
                return int(m[1])

def getFileLine(path: Path, lineNum: int):
    cnt = 1
    with path.open() as f:
        for line in f:
            if cnt == lineNum:
                return line
            cnt += 1
    print("{} do not have line number {}".format(str(path), lineNum))
    return None

def getMutator(projPath: Path, mutId: str):
    mutLog = projPath / 'mutants.log'
    assert mutLog.exists()
    with mutLog.open() as log:
        for line in log:
            if line.startswith(mutId + ':'):
                m = re.match(r'\d+:(\w+):.*\n', line)
                assert m is not None
                return m[1]

def isExactlySameCode(a:str, b:str):
    tmp1 = ''.join(a.split())
    tmp2 = ''.join(b.split())
    return tmp1 == tmp2

def checkAllPatches():
    mutatorDict = {}
    resDict = {}
    for projPath in getFinishedProjPath():
        m = re.match(r'(\w+)-(\d+f)', projPath.stem)
        assert m is not None
        projName = m[1]
        # if projName != "jacksoncore":
        #     continue
        srcRelativePath=getD4jProjSrcRelativePath(projPath)
        print('='*15 + projName + '='*15)
        for dir in patchesDirPath.iterdir():
            if dir.is_dir() and dir.stem.startswith(projName):
                mid = dir.stem.split('_')[1]
                print('Checking ' + dir.stem)
                for idDir in (dir / 'patches-pool').iterdir():
                    if idDir.is_dir():
                        patchFilePath = sp.check_output("find . -name '*.java'", shell=True, universal_newlines=True, cwd=str(idDir)).strip()
                        patchFilePath = idDir / patchFilePath
                        # mutLineNum = getMutLineNum(projPath, mid)
                        # patchedLine = getFileLine(patchFilePath, mutLineNum)
                        with patchFilePath.open() as f:
                            patchFileContent  = f.read()
                        fixedJavaFileContent = getMutFixedFileContent(projPath, mid, projSrcPath=srcRelativePath)
                        if isExactlySameCode(patchFileContent, fixedJavaFileContent):
                            mutator = getMutator(projPath, mid)
                            if mutator not in mutatorDict:
                                mutatorDict[mutator] = []
                            mutatorDict[mutator].append(projPath.stem)
                            if projName not in resDict:
                                resDict[projName] = []
                            resDict[projName].append(mid)
                            print("{} fixed!".format(dir.stem))
                            break
    proj = [k for k in resDict]
    proj.sort()
    for key in proj:
        print("{} mutants of {} are correctly (exactly) fixed!".format(len(resDict[key]), key))
    mutators = [k for k in mutatorDict]
    mutators.sort()
    for m in mutators:
        print("{}: {}".format(m, len(mutatorDict[m])))

def getAllMutators():
    mutatorDict = {}
    for projPath in getFinishedProjPath():
        sampleTxt = projPath / 'sampledMutIds.txt'
        mids = file2Lines(sampleTxt)
        for mid in mids:
            mutator = getMutator(projPath, mid)
            if mutator not in mutatorDict:
                mutatorDict[mutator] = []
            mutatorDict[mutator].append(mid)
    mutators = [k for k in mutatorDict]
    mutators.sort()
    for m in mutators:
        print("{}: {}".format(m, len(mutatorDict[m])))

def main():
    for projPath in getFinishedProjPath():
        print('=' * 10 + str(projPath) + '=' * 10)
        srcRelativePath=getD4jProjSrcRelativePath(projPath)
        buildRelativePath=getD4jProperty(projPath, 'dir.bin.classes')
        sampleTxt = projPath / 'sampledMutIds.txt'
        assert sampleTxt.exists()
        m = re.match(r'(\w+)-(\d+f)', projPath.stem)
        assert m is not None
        projName = m[1]
        version = m[2]
        formalProjName = getProjFormalNameFromProjSimpleName(projName)
        mids = file2Lines(sampleTxt)
        for mid in mids:
            # check if it is already finished before
            patchesInfoFile = patchesDirPath / '{}_{}'.format(projName, mid) / 'patches-pool' / 'patches.info'
            if patchesInfoFile.exists():
                print('Patches for {}_{} already exist, skipping...'.format(projName, mid))
                continue
            print('=' * 10 + 'Start {}_{}'.format(projName, mid) + '=' * 10)
            # checkout the original fixed version
            targetProjPath = tbarD4jProjDirPath / '{}_{}'.format(projName, mid)
            try:
                sp.run('defects4j checkout -p {} -v {} -w {}'.format(formalProjName, version, str(targetProjPath)), shell=True, universal_newlines=True, check=True)
            except:
                print('Try removing {} and checkout again...'.format(str(targetProjPath)))
                shutil.rmtree(str(targetProjPath), ignore_errors=True)
                sp.run('defects4j checkout -p {} -v {} -w {}'.format(formalProjName, version, str(targetProjPath)), shell=True, universal_newlines=True, check=True)
            # apply the mutant file
            fileToBeReplacedPath, javaFileRelativePath = applyMutant(targetProjPath, projPath, mid, srcRelativePath=srcRelativePath)
            javacOutputDirPath = str((Path(targetProjPath) / buildRelativePath / javaFileRelativePath).parent)
            try:
                sp.run('defects4j compile', shell=True, universal_newlines=True, check=True, cwd=str(targetProjPath))
            except:
                try:
                    cmd = 'javac {} -cp {} -d {}'.format(fileToBeReplacedPath, buildRelativePath, javacOutputDirPath).split()
                    sp.run(cmd, shell=False, universal_newlines=True, check=True, cwd=str(targetProjPath))
                except:
                    print('[ERROR] The mutant {}-{} can not be compiled by defects4j.'.format(projName, mid))
                    continue
            # start the patch generation
            logPath = logDirPath / ('{}_{}.log'.format(projName, mid))
            tryRunCmdWithProcessPool('bash PerfectFLTBarRunner.sh {} {}_{} {} {}'.format(str(tbarD4jProjDirPath) + '/', projName, mid, d4jHome, str(bugPositionFile)).split(), logPath, insist=True)
        waitForProcessPoolFinish()
        print('=' * 10 + str(projPath) + ' Finished' + '=' * 10)
        for mid in mids:
            targetProjPath = tbarD4jProjDirPath / '{}_{}'.format(projName, mid)
            shutil.rmtree(str(targetProjPath), ignore_errors=True)

def runTbarOnSingleMutant(projName: str, mid: int):
    mid = str(mid)
    for projPath in getFinishedProjPath():
        if projPath.stem.startswith(projName + '-'):
            print('=' * 10 + str(projPath) + '=' * 10)
            srcRelativePath=getD4jProjSrcRelativePath(projPath)
            buildRelativePath=getD4jProperty(projPath, 'dir.bin.classes')
            sampleTxt = projPath / 'sampledMutIds.txt'
            assert sampleTxt.exists()
            m = re.match(r'(\w+)-(\d+f)', projPath.stem)
            assert m is not None
            projName = m[1]
            version = m[2]
            formalProjName = getProjFormalNameFromProjSimpleName(projName)
            
            # checkout the original fixed version
            targetProjPath = tbarD4jProjDirPath / '{}_{}'.format(projName, mid)
            sp.run('defects4j checkout -p {} -v {} -w {}'.format(formalProjName, version, str(targetProjPath)), shell=True, universal_newlines=True, check=True)
            # apply the mutant file
            fileToBeReplacedPath, javaFileRelativePath = applyMutant(targetProjPath, projPath, mid, srcRelativePath=srcRelativePath)
            javacOutputDirPath = str((Path(targetProjPath) / buildRelativePath / javaFileRelativePath).parent)
            try:
                sp.run('defects4j compile', shell=True, universal_newlines=True, check=True, cwd=str(targetProjPath))
            except:
                try:
                    cmd = 'javac {} -cp {} -d {}'.format(fileToBeReplacedPath, buildRelativePath, javacOutputDirPath).split()
                    sp.run(cmd, shell=False, universal_newlines=True, check=True, cwd=str(targetProjPath))
                except:
                    print('[ERROR] The mutant {}-{} can not be compiled by defects4j.'.format(projName, mid))
                    continue
            # start the patch generation
            cmd = 'bash PerfectFLTBarRunner.sh {} {}_{} {} {}'.format(str(tbarD4jProjDirPath) + '/', projName, mid, d4jHome, str(bugPositionFile)).split()
            # sp.run(cmd, shell=False, universal_newlines=True)
            logPath = logDirPath / ('{}_{}.log'.format(projName, mid))
            tryRunCmdWithProcessPool('bash PerfectFLTBarRunner.sh {} {}_{} {} {}'.format(str(tbarD4jProjDirPath) + '/', projName, mid, d4jHome, str(bugPositionFile)).split(), str(logPath), insist=True)
            waitForProcessPoolFinish()

if __name__ == '__main__':
    try:
        # genMutBenchBugPositions()
        main()
        # runTbarOnSingleMutant('time', 16447)
        # checkAllPatches()
        # getAllMutators()
    finally:
        for _, _, p, log in processPool:
            log.close()
            p.kill()