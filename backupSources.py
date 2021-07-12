import fnmatch
import logging
import os
import sys
import glob
import re
import shutil
import subprocess
import errno
import time

sys.path.append("C:\\Users\\1000Volt\\Documents\\purgeMats")

import nuke

import copyLib
import traverse

SOURCESFILE = "C:\\Users\\1000Volt\\Documents\\purgeMats\\collect_strict.txt"

BACKUP_ROOT = "E:"

hierachy = traverse.ProjectHierachy(None)
scriptPathList = hierachy.listCompPaths("Gamonya_fw23695", "", "")

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='C:\\Users\\1000Volt\\Documents\\purgeMats\\error.log', format=FORMAT, encoding='utf-8', level=logging.ERROR)

def getHeroScripts(scriptPath):
	"""Determind which script is the main one. By version number or timestamp"""
	potentialHeroScripts = []

	rScriptPath = scriptPath.replace("\\", "/")
	shotName = rScriptPath.split("/")[-3]

	allScripts = os.listdir(rScriptPath)
	sortedVerValidScripts = sorted( fnmatch.filter(allScripts, "%s_v[0-9][0-9].nk" %(shotName) ) )
	
	invalidScripts = fnmatch.filter(allScripts, "%s_*.nk" %(shotName) )
	sortedLastModScriptPaths = sorted([os.path.join(rScriptPath, each) for each in invalidScripts], key=os.path.getmtime)
	
	latestVerScriptPath = ""
	if sortedVerValidScripts:
		latestVerScriptPath = rScriptPath + sortedVerValidScripts[-1]
		potentialHeroScripts.append(latestVerScriptPath)

	# if sortedLastModScriptPaths:
	# 	if latestVerScriptPath != sortedLastModScriptPaths[-1]:
	# 		potentialHeroScripts.append(sortedLastModScriptPaths[-1])

	return potentialHeroScripts

def backupSources(sourcesFile, backupPath):
	""""""
	logging.basicConfig(filename='C:\\Users\\1000Volt\\Documents\\purgeMats\\result.log', encoding='utf-8', level=logging.INFO)

	sourceList = []

	txt = open(sourcesFile, "r")
	for eachLine in txt:
		sourceList.append(eachLine)

	txt.close()

	info1 = "Copying %s paths to %s" %(len(sourceList), backupPath)
	print(info1)
	logging.info(info1)

	count = 0

	for source in sourceList:
		unixPath = source
		
		seqString = re.search("(?<=%)\d+(?=d)", os.path.basename(source))
		
		# Check if source is file sequence, then convert to unix style.
		if seqString:
			seqDigit = int(seqString.group())
			unixName = re.sub("%\d+d", "[0-9]"*seqDigit, os.path.basename(source))

			unixPath = os.path.join(os.path.dirname(source), unixName)

		info2 = "%s: %s" %(count, unixPath)
		print(info2)
		logging.info(info2)

		# Copy file loop
		copyList = glob.glob(unixPath)

		for eachFile in copyList:
			backupFilePath = os.path.join( backupPath, os.path.splitdrive(eachFile)[-1])

			if not os.path.exists(os.path.dirname(backupFilePath)):
				os.makedirs(os.path.dirname(backupFilePath))
			
			# try:
			subprocessCopy(eachFile, backupFilePath)
			# except IOError as io_err:
			# 	print(io_err)
			# 	logging.error(io_err)

		count+=1

	print("Backup finished")
	logging.info("Backup finished")

def gatherFileReferences(scriptName):
	""""""
	refPaths = []

	try:
		nuke.scriptOpen(scriptName)

		for eachNode in nuke.allNodes():
			if eachNode.Class() in ['Read', 'ReadGeo2']:
				print("---")

				readfile = eachNode['file'].value()

				print(readfile)
				refPaths.append(readfile)
		
		nuke.scriptClose()
		print("=========================")
	except:
		print("Unexpected error:", sys.exc_info()[0])
		logging.error("Unexpected error:", sys.exc_info()[0])

		nuke.scriptClose()
		raise

	return refPaths

class backupDataTree():
	def __init__(self):
		self.projs = {}

	def addShot(proj, seq, shot, sources):
		if not proj in self.projs:
			self.projs[proj] = {}

		if not seq in self.projs[proj]:
			self.projs[proj][seq] = {}

		# if not shot in self.projs[proj][seq]:
		self.projs[proj][seq][shot] = sources

def backupScript(scriptPath):
	""""""
	copiesLog = []
	sourcesSet = set()

	print(scriptPath)

	entities = None
	try:
		entities = hierachy.getEntityFromCompFile(scriptPath)
	except:
		print("Unexpected error:", sys.exc_info()[0])
		logging.error("Unexpected error:", sys.exc_info()[0])
		raise

	# Script
	scriptBackupDir = "/".join([BACKUP_ROOT, entities[0], entities[1], entities[2], "Scripts"])

	if not os.path.exists(scriptBackupDir):
		os.makedirs(scriptBackupDir)
	else:
		print("Script found. The shot have been copied. Skip current shot.")
		logging.info("Script found. The shot have been copied. Skip current shot.")
		return copiesLog
	print("Backup script..")
	logging.info("Backup script..")

	# allNukes = glob.glob(os.path.join(os.path.dirname(scriptPath), "*.nk"))

	# for each in allNukes:
	shutil.copy(scriptPath, scriptBackupDir)

	try:
		
		logging.info("Opening %s" %scriptPath)
		nuke.scriptOpen(scriptPath)
	except RuntimeError as e:
		print(e)
		logging.error(e)

	# Sources
	logging.info("Collecting file nodes..")
	for eachNode in nuke.allNodes():
		eachNodeKnobs = eachNode.knobs()

		if eachNodeKnobs.has_key("file"):
			if not eachNodeKnobs.has_key("Render") and not eachNodeKnobs.has_key("Execute"):
				if not eachNode.hasError():
					readfile = eachNodeKnobs['file'].value().strip()
					if readfile:
						# refPaths.append((eachNode.Class(), eachNodeKnobs['file'].value()))
						sourcesSet.add(readfile)

	nuke.scriptClose()

	# Output
	outputPath = ""

	try:
		logging.info("Backup output..")
		print("Backup output..")
		
		outputPath = hierachy.transcribeRenderPath(*entities)

		newOutputSplit = [BACKUP_ROOT, entities[0], entities[1], entities[2], "Output", os.path.basename(outputPath)]
		newOutputPath = "/".join(newOutputSplit)
		print(outputPath)

		# if os.path.exists(outputPath):
		if not os.path.exists(newOutputPath):
			copiesLog.append(outputPath)
			starttime = time.time()
			shutil.copytree(outputPath, newOutputPath)
			# subprocessCopy(each, newOutputPath)
			print("took %s seconds" %(time.time() - starttime))

		else:
			logging.error("Error: Backup path already exists: %s" %(newOutputPath))
			print("Error: Backup path already exists: %s" %(newOutputPath))
		# else:
		# 	logging.error("Error: Cannot find: %s" %(outputPath))
		# 	print("Error: Cannot find: %s" %(outputPath))
	except:
		print("Unexpected error:", sys.exc_info()[0])
		logging.error("Unexpected error:", sys.exc_info()[0])
		# raise

	logging.info("Backup %s sourcepaths.." %(len(sourcesSet)))
	print("Backup %s sourcepaths.." %(len(sourcesSet)))
	for src in sourcesSet:
		starttime = time.time()
		logging.info("from :%s" %(src))
		print("from :%s" %(src))
		copiesLog.append(src)
		unixPath = src

		seqString = re.search("(?<=%)\d+(?=d.\w{3,4}$)", os.path.basename(unixPath))
		
		# Check if source is file sequence, then convert to unix style.
		if seqString:
			seqDigit = int(seqString.group())
			unixName = re.sub("%\d+d", "[0-9]"*seqDigit, os.path.basename(unixPath))
			unixPath = os.path.join(os.path.dirname(unixPath), unixName)

		srcType = ""
		if unixPath.endswith(".obj" or unixPath.endswith(".abc")):
			srcType = "Geos"
		elif "MAYA" in unixPath:
			srcType = "3DPasses"
			if seqString:
				subFolder = re.search("(?<=RENDERS/)[\w_/]+", os.path.dirname(unixPath))
				if subFolder:
					srcType = srcType + "/" + subFolder.group()
		elif "material" in unixPath.lower():
			srcType = "Materials"
		elif "FROM_" in unixPath:
			#srcType = re.split(entities[1] + "/", os.path.dirname(unixPath), 1)[-1]
			srcType = re.search("FROM_[\w_/]+", os.path.dirname(unixPath)).group()
		elif "mattepaint" in unixPath.lower() or unixPath.endswith(".psd"):
			srcType = "MATTEPAINT"
		else:
			srcType = "Sources"


		backupPathSplit = [BACKUP_ROOT, entities[0], entities[1], entities[2], srcType]

		backupDir = "/".join(backupPathSplit)
		logging.info("to: %s" %(backupDir))
		print("to: %s" %(backupDir))

		# Copy file loop
		copyList = glob.glob(unixPath)

		try:
			if not os.path.exists(backupDir):
				os.makedirs(backupDir)		
			for eachFile in copyList:
				shutil.copy(eachFile, backupDir)
				# subprocessCopy(eachFile, backupDir)

				# shutil.copyfile(eachFile, backupFilePath)
			# osCopy(eachFile, backupFilePath)
		except OSError as e:
			if e.errno == errno.ENOSPC:
				print(e)
				logging.error(e)
				raise
			else:
				print(e)
				logging.error(e)
				raise
		except:
			print("Unexpected error:", sys.exc_info()[0])
			logging.error("Unexpected error:", sys.exc_info()[0])
			raise

		# count+=1		
		print("took %s seconds" %(time.time() - starttime))

	print("---")
	return copiesLog

def writeList(toWriteList, filename):
	""""""
	try:
		textfile = open(filename, "w")
		for each in toWriteList:
			textfile.write(each+"\n")

		textfile.close()
	except:
		print("Unexpected error:", sys.exc_info()[0])
		logging.error("Unexpected error:", sys.exc_info()[0])

def main():
	"""Main"""
	allMatList = set()
	whateverList = []

	for scriptPath in scriptPathList:
		potentialHeroScripts = getHeroScripts(scriptPath)
		
		for hero in potentialHeroScripts:
			whateverList.append(hero)
			# Open nuke and get all read and write nodes.
			# refPaths = gatherFileReferences(hero)
			refPaths = backupScript(hero)

			whateverList.extend(refPaths)


	print("writing file..")

	# whatever = "C:\\Users\\3D02\\Documents\\purgeMats\\nodeThatHasFile.txt"
	# writeList(whateverList, whatever)

	# backupSources(SOURCESFILE, "F:/")

main()