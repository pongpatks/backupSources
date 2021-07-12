import glob
import os
import shutil
import subprocess

import time

def subprocessCopy(source, dest):
	"""Subprocess, using windows command to copy files, dest is destination directory."""

	# Sanity check on inputs. Be mindful as dest is directory, it need extra slash.
	rSource = "\"" + source.replace("/", "\\") + "\""
	rDest = "\"" + dest.replace("/", "\\") + "\\\""

	commandArgs = " ".join(['xcopy', rSource, rDest, '/K/Y/i/q'])

	proc = subprocess.Popen(commandArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)#, shell=True)

	proc.wait()
	# outtxt = proc.stdout.readline()
	# print(outtxt)
	err = proc.stderr.readline()
	return err

def subprocessCopy2(source, dest):
	"""Use os module to call windows command, I suspect it is the same as above anyway. dest is destination directory."""
	
	# Sanity check on inputs. Be mindful as dest is directory, it need extra slash.
	rSource = "\"" + source.replace("/", "\\") + "\""
	rDest = "\"" + dest.replace("/", "\\") + "\\\""

	commandArgs = " ".join(['xcopy', rSource, rDest, '/K/Y/i/q'])

	os.system(commandArgs)

def copyByIO(src, dst):
	"""Copy by read and write file to new place. I heard this have the benefit of adjustable buffer.
		but speed test is so slow.. something wrong?"""
	destFullPath = os.path.join(dst, os.path.basename(src))
	with open(src, 'rb') as fsrc:
		with open(destFullPath, 'wb') as fdst:
			for x in iter(lambda: fsrc.read(16384),""):
				fdst.write(x)


if __name__ == "__main__":
	sourcePath = "N:\\NETFLIX\\THE_PROTECTOR\\EPISODES\\402\\FROM_ONLINE\\MASTER\\TP_402_S001_P0010\\TP_402_S001_P0010_v02"
	destpath = "D:\\SpeedTest"

	sourceList = glob.glob(os.path.join(sourcePath, "*.dpx"))

	startTime = time.time()
	print("Test speed")
	for each in sourceList:
		#subprocessCopy(each, destpath)
		#shutil.copy(each, destpath)
		copy3(each, destpath)

	print(time.time() - startTime)