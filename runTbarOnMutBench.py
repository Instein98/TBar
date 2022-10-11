import os, re
import shutil
import subprocess as sp
from pathlib import Path

processPool = []  # storing (cmd, cwd, process)
maxMultiProcess = 1  # Todo: multiple tbar patch generation processes will all stuck

def runCmdAndWaitForFinish(cmd: list, cwd=None):
    process = sp.Popen(cmd, shell=False, stdout=sp.PIPE, stderr=sp.PIPE, cwd=cwd, universal_newlines=True)
    stdout, stderr = process.communicate()
    retCode = process.poll()
    return stdout, stderr, retCode

def tryRunCmdWithProcessPool(cmd: list, cwd=None, insist=True):
    if len(processPool) >= maxMultiProcess:
        if insist:
            waitForProcessPoolSlotAvailable()
        else:
            return False
    process = sp.Popen(cmd, shell=False, stdout=sp.PIPE, stderr=sp.PIPE, cwd=cwd, universal_newlines=True)  # shell=False by default
    cwd = '.' if cwd is None else cwd
    processPool.append((cmd, cwd, process))
    print("Process \"{}\"@\"{}\" has started and been added to the pool.".format(cmd, cwd))
    return True

def waitUntilMultiProcessLessThan(t):
    if len(processPool) >= t:
        print("[INFO] Waiting the number of parallel processes become less than " + str(t))
    while len(processPool) >= t:
        for cmd, cwd, process in processPool:
            retCode = process.poll()
            # haven't finished yet
            if retCode is None:
                continue
            else:
                print('=' * 10 + ' `{}` in "{}" Finished '.format(cmd, cwd) + '=' * 10)
                print('*' * 10 + ' RetCode: ' + str(retCode) + ' ' + ('*' * 10))
                stdout, stderr = process.communicate()
                print('*' * 10 + ' STDOUT ' + ('*' * 10))
                if stdout is not None and len(stdout) > 0:
                    print(stdout)
                print('*' * 10 + ' STDERR ' + ('*' * 10))
                if stderr is not None and len(stderr) > 0:
                    print(stderr)
                print('=' * (20 + len(' `{}` in "{}" Finished '.format(cmd, cwd))))
                processPool.remove((cmd, cwd, process))
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


def main():
    for projPath in getFinishedProjPath():
        print('=' * 10 + str(projPath) + '=' * 10)
        srcRelativePath=getD4jProjSrcRelativePath(projPath)
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
            sp.run('defects4j checkout -p {} -v {} -w {}'.format(formalProjName, version, str(targetProjPath)), shell=True, universal_newlines=True, check=True)
            # apply the mutant file
            applyMutant(targetProjPath, projPath, mid, srcRelativePath=srcRelativePath)
            try:
                sp.run('defects4j compile', shell=True, universal_newlines=True, check=True, cwd=str(targetProjPath))
            except:
                print('[ERROR] The mutant {}-{} can not be compiled by defects4j.'.format(projName, mid))
                continue
            # start the patch generation
            tryRunCmdWithProcessPool('bash PerfectFLTBarRunner.sh {} {}_{} {} {}'.format(str(tbarD4jProjDirPath) + '/', projName, mid, d4jHome, str(bugPositionFile)).split(), insist=True)
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
            applyMutant(targetProjPath, projPath, mid, srcRelativePath=srcRelativePath)
            try:
                sp.run('defects4j compile', shell=True, universal_newlines=True, check=True, cwd=str(targetProjPath))
            except:
                print('[ERROR] The mutant {}-{} can not be compiled by defects4j.'.format(projName, mid))
                continue
            # start the patch generation
            cmd = 'bash PerfectFLTBarRunner.sh {} {}_{} {} {}'.format(str(tbarD4jProjDirPath) + '/', projName, mid, d4jHome, str(bugPositionFile)).split()
            # sp.run(cmd, shell=False, universal_newlines=True)
            tryRunCmdWithProcessPool('bash PerfectFLTBarRunner.sh {} {}_{} {} {}'.format(str(tbarD4jProjDirPath) + '/', projName, mid, d4jHome, str(bugPositionFile)).split(), insist=True)
            waitForProcessPoolFinish()

if __name__ == '__main__':
    try:
        # genMutBenchBugPositions()
        # main()
        runTbarOnSingleMutant('csv', 526)
    finally:
        for _, _, p in processPool:
            p.kill()