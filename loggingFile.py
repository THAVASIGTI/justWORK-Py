import os,shutil,tarfile
import zipfile

def main():
	path = os.getcwd()
	#dest = os.path.join(path,"comp")
	#try:
	#	os.mkdir(dest)
	#except OSError:
	#	print("aldery use")

	log = os.path.join(path,"l.log")
	#print(log)
	l = os.path.basename(log)
	print(l)
	vm = os.path.join(path,"vm.log")
#	#print(vm)
	v = os.path.basename(vm)
	print(v)
#	shutil.copy(log,dest)
#	shutil.copy(vm,dest)
#	d = os.path.basename(dest)
	comp = "/home/thavasigti/snap/compress"

	os.popen("tar -zcvf "+comp+".tar "+l+" "+v)
#	os.popen("tar -zcvf "+comp+".tar "+v) 
#	with ZipFile.ZipFile(comp,"w")
#    	j.write(log)
#    	j.write(vm)

if __name__=="__main__":
    main()
