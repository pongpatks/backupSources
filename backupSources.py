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

import nuke
import pipeline

BACKUP_ROOT = "E:"

hierarchy = pipeline.ProjectHierarchy(None)
scriptPathList = hierarchy.listCompPaths("Gamonya_fw23695", "", "")

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

	return potentialHeroScripts

def backupScript(scriptPath):
	""""""
	copiesLog = []
	sourcesSet = set()

	entities = None
	try:
		entities = hierarchy.entitiesFromCompPath(scriptPath)
	except:
		logging.error("Unexpected error:", sys.exc_info()[0])
		raise


	# Backup script
	scriptBackupDir = "/".join([BACKUP_ROOT, entities[0], entities[1], entities[2], "Scripts"])

	if not os.path.exists(scriptBackupDir):
		os.makedirs(scriptBackupDir)
	else:
		logging.info("Script found. The shot have been copied. Skip current shot.")
		return copiesLog

	logging.info("Backup script..")

	shutil.copy(scriptPath, scriptBackupDir)


	# Open nukescript
	try:
		logging.info("Opening %s" %scriptPath)
		nuke.scriptOpen(scriptPath)
	except RuntimeError as e:
		print(e)
		logging.error(e)


	# Collect sources
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

	# Backup render
	outputPath = ""

	try:
		logging.info("Backup output..")
		print("Backup output..")
		
		outputPath = hierarchy.transcribeCompOutputPath(*entities)

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
	except:
		logging.error("Unexpected error:", sys.exc_info()[0])
		# raise

	logging.info("Backup %s sourcepaths.." %(len(sourcesSet)))


	# Backup sources
	for src in sourcesSet:
		starttime = time.time()
		logging.info("from :%s" %(src))

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
			srcType = re.search("FROM_[\w_/]+", os.path.dirname(unixPath)).group()
		elif "mattepaint" in unixPath.lower() or unixPath.endswith(".psd"):
			srcType = "MATTEPAINT"
		else:
			srcType = "Sources"


		backupPathSplit = [BACKUP_ROOT, entities[0], entities[1], entities[2], srcType]

		backupDir = "/".join(backupPathSplit)
		logging.info("to: %s" %(backupDir))

		# Copy file loop
		copyList = glob.glob(unixPath)

		try:
			if not os.path.exists(backupDir):
				os.makedirs(backupDir)		
			for eachFile in copyList:
				shutil.copy(eachFile, backupDir)

				# Which of these is faster?
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
			logging.error("Unexpected error:", sys.exc_info()[0])
			raise

		print("took %s seconds" %(time.time() - starttime))
	print("---")
	return copiesLog

def main():
	"""Main"""
	allMatList = set()

	for scriptPath in scriptPathList:
		potentialHeroScripts = getHeroScripts(scriptPath)
		
		for hero in potentialHeroScripts:
			# Open nuke, collect all read and write nodes, copy to back up server.
			refPaths = backupScript(hero)

	print("writing file..")

main()