import argparse,os,datetime,time,shutil,random,sys
from Tshark import doPcaps
import tarfile,logging,os
import subprocess,glob
import logging.handlers
from termios import tcflush, TCIFLUSH
from multiprocessing import Process
import json,helper
from zipfile import ZipFile
import virualMachine as machine
from helper import *
DURATION =  90

def startCapture(args):
    src = args.src
    vm = args.vm
    nas = args.nas
    user = args.user
    snap = args.snap
    passwd = args.passwd
    interface = args.interface
    remoteLocation = args.remote
    with open(vm, "r") as myfile:
        lines = myfile.readlines()
        for line in lines:
            if not "ethernet0.vnet" in line:
                continue 
            if "ethernet0.vnet" in line:
                interfaceInFile = line.replace('ethernet0.vnet = "/dev/',"").replace('"',"").replace("\n","")
                break
        myfile.close()
    if interfaceInFile != interface:
        logging.warning("Please provide "+interfaceInFile+" as -i parameter to capture "+vm) #logging.warning = interface not equle error
        exit()
    for root, dirs, folder in os.walk(src):
        for files in folder:
            if files.endswith('.exe'):
                dest = "c:\\Malware\\"
                sha256 = os.path.basename(root)
                strain = os.path.basename(os.path.dirname(root))
                binaryInPath = os.path.join(root,files)
                baseFileName = files[:-4] + datetime.datetime.now().strftime('-%Y-%m-%d-%H-%M-%S')
                JsonPath = os.path.join(*[root,baseFileName+".json"])
                PcapPath = os.path.join(*[root,baseFileName+".pcapng"])
                evtxPath = os.path.join(*[root,baseFileName+".evtx"])
                LogPath = os.path.join(*[root,baseFileName+".log"])
                VmLogPath = os.path.join(*[root,baseFileName+"-vmware.log"])
                ZipPath = os.path.join(*[root,baseFileName+".tar"])

                loggingFunction(LogPath) #start with logging file and file diractory
                logging.info("strain: %s " % strain) #logging.info = strain 
                logging.info("sha256: %s " % sha256) #logging.info = sha256 
                machine.setupVM(vm,snap)
                dest = dest + files
                vmLoggingFunction(vm,VmLogPath) #geting a vmware log files 
                
                machine.copyFileToGuest(vm,binaryInPath,dest,user,passwd)
                initiateCaptureAndStartExe(interfaceInFile,PcapPath,root,vm,files,user,passwd)
                success = copyEventFile(vm,evtxPath,user,passwd,remoteLocation)
                if not success:
                    while(True):
                        confirmString = input("COPY FAILED:Do you want to copy and compress the security.evtx file?(yes or no)\n")
                        logging.error("COPY FAILED:Do you want to copy and compress the security.evtx file?(yes or no)\n") #error for evtx file not copy
                        if confirmString == "yes":
                            evtfileNameTemp = os.path.join(root,"Security.evtx")
                            if os.path.isfile(evtfileNameTemp):
                                os.rename(evtfileNameTemp,evtxPath)
                                break
                            else:
                                logging.warning("Place the Security.evtx at "+root+" before continuing") #warning logging 
                                continue
                        elif confirmString == "no":
                            machine.stopVM(vm)
                            logging.info("VMware stop") #logging.warning = for vmstop
                            exit()       
                        else:
                            continue
                machine.stopVM(vm)
                if os.path.isfile(PcapPath):
                    userComments = getComment()
                    evtxBz = evtxPath + ".bz"
                    logging.info("Copying file") #loggin.warning = evtx file copy and compares 
                    evtxBz = compressFile(evtxPath,evtxBz)
                    data = {}
                    data["comment"] = userComments
                    with open(JsonPath, 'w') as cf:
                        json.dump(data, cf)
                    pcapFilePath = fetchPcap(root)
                    logCompress(LogPath,VmLogPath,ZipPath)
                    for pcapFile in pcapFilePath:
                        validateStatus = validateCapture(pcapFile)
                        if not validateStatus:
                            logging.error("file missing") #pcap,evtx,json any one file missing
                            k = input("Press Enter key to delete and proceed with next sample....Press Y and Enter to Delete and Exit\n")
                            if(k.lower() == 'y'):
                                exit()
                            else:
                                
                                continue
                        else:
                            copyArtifaces(nas,sha256,evtxBz,PcapPath,JsonPath,LogPath,VmLogPath,ZipPath)
                    shutil.rmtree(root)
                    if os.path.dirname(root) != src:
                        if len(os.listdir(os.path.dirname(root))) <= 0:
                            shutil.rmtree(os.path.dirname(root))
                        k = input("Press Enter key to delete and proceed with next sample....Press Y and Enter to Delete and Exit\n")
                        if(k.lower() == 'y'):
                            exit()
                        else:
                            continue
                else:
                    logging.error("****PCAPNG FILE IS MISSING*****")
                    k = input("Press Enter key to delete and proceed with next sample....Press Y and Enter to Delete and Exit\n")
                    if(k.lower() == 'y'):
                        exit()
                    else:
                        continue
    
               
def initiateCaptureAndStartExe(ifName,filename,tempDir,vm,malware,user,psswd):
    thread_Capture = Process(target = capturePcap ,args=(ifName,filename,tempDir))
    thread_Start = Process(target = starMalware, args=(vm,malware,user,psswd))
    try:
        thread_Capture.start()
        thread_Start.start()
        thread_Capture.join()
        thread_Start.terminate()
    except KeyboardInterrupt:
        logging.error("Stopping Capture")
        thread_Capture.terminate()
        thread_Start.terminate()

def loggingFunction(LogPath):
    #print(root)
    LOG_FILENAME = LogPath
    logger = logging.getLogger()
    logger.setLevel(level=logging.INFO)
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME)
    logger.addHandler(handler)
    return LOG_FILENAME

def vmLoggingFunction(vm,VmLogPath):
    path = os.path.join(os.path.dirname(vm),"vmware.log")
    shutil.move(path,VmLogPath)
    
def logCompress(LogPath,VmLogPath,ZipPath):
    log = os.path.basename(LogPath)
    vm = os.path.basename(VmLogPath)
    os.popen("tar -zcvf "+ZipPath+".tar "+log+" "+vm)

def capturePcap(ifName,filename,tempDir):
    doPcaps(ifName,filename,int(DURATION),tempDir)

def starMalware(vm,malware,user,psswd):
    malware_path = "c:/Malware/" + malware
    toRun = "sudo vmrun  -T ws  -gu " + user +" -gp " + psswd + " runProgramInGuest \"" + vm +"\" -interactive -nowait \"" +  malware_path + "\""
    logging.info("Argument :" + toRun)
    os.system(toRun)

def main():

    parser = argparse.ArgumentParser(description="Capturing Windows Malware")
    parser.add_argument('action', action='store',help="")
    parser.add_argument('--src', '-s',
                        dest="src",
                        default="./",
                        help='Source Directory',required=True)
    parser.add_argument('--vm', '-vm',
                        dest="vm",
                        help='Path to VM file',required=True)
    parser.add_argument('--snapshot', '-ss',
                        dest="snap",
                        help='Snapshot to revert',required=True)
    parser.add_argument('--user','-u',
                        dest="user",
                        help='Guest OS User name',required=True)
    parser.add_argument('--password','-p',
                        dest="passwd",
                        help='to destination',required=True)
    parser.add_argument('--interface','-i',
                        dest="interface",
                        help='interface of the VM ',required=True)
    parser.add_argument('--output','-o',
                        dest="nas",
                        help='Destination to copy th target files',required=True)
    parser.add_argument('--remote','-rd',
                        dest="remote",
                        help='Remote Destination to copy th target files',required=True)
    args = parser.parse_args()
 
    logging.basicConfig(level=logging.DEBUG)

    if args.action == 'capture':
        startCapture(args)

if __name__ == "__main__":
    main()
