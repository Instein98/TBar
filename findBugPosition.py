import re

proj=""
buggyFile=""
# nextLineNumLine=False
# orgLineNum=-1
buggyLineNum=""
# isOneLineChange=False

print() # start a new line in BugPositions.txt
with open("findOneLinePatch.log") as file:
    for line in file:
        if line.startswith("checking"):
            proj=line.split(" ")[1].replace("/", "_").strip()
            buggyLineNum=""
            buggyFile=""
            # print(proj)
        elif line.startswith("diff "):
            buggyFile=line.split(" ")[2].strip()
            # print(buggyFile)
            # nextLineNumLine=True
        elif re.match(r"[0-9]+(,[0-9]+)*(c|a|d)[0-9]+(,[0-9]+)*", line.strip()):
            # print("matched: " + line.strip())
            # if "c" in line:
            #     isOneLineChange=True
            # else:
            #     isOneLineChange=False
            buggyLineNum = buggyLineNum + re.split("c|a|d", line)[1].strip() + ","
            # print(orgLineNum)
            # nextLineNumLine = False
        elif line.startswith(proj.replace("_","-")):
            if "is one-line patch!" in line:
                if buggyLineNum.endswith(","):
                    buggyLineNum = buggyLineNum[:-1]
                print(proj+"@"+buggyFile+"@"+str(buggyLineNum))
                # isOneLineChange=False