import fnmatch
import glob
import os
import re
import sys

import yaml

MAINPATH = "D:/FakePipeline"

def convertTemplate2REX(pipeline):
	""""""

	filePath = "<root>/<proj>/NUKE/_timeline/<ep>/<shot>/scripts/<shot>_v<version>.nk"

	i = 0

	def replMet(matchobj):
		nonlocal i
		if i==0:
			i+=1
			#print(matchobj.groups())
			return matchobj.expand(r'(?P<\1>\\w+)')
		else:
			i+=1
			#print(matchobj.groups())
			return matchobj.expand(r'(?P=\1)')

	for each in ["proj", "ep", "shot"]:
		i = 0

		print(re.sub("<(%s)>" %each, replMet, "<root>/<proj>/NUKE/<ep>/<shot>/<shot>_v001"))

class ProjectHierachy():
	def __init__(self, projectName, root=MAINPATH):
		self.root = MAINPATH
		self.descriptor = {}

		self.loadProjectDescriptor(projectName, root)

	def loadProjectDescriptor(self, projectName, root=MAINPATH):
		"""In future, should we read this from xml input?"""

		self.root = root

		descriptorPath = "/".join([self.root, projectName, "desc.yaml"])

		with open(descriptorPath, "r") as stream:
			self.descriptor = yaml.load(stream, Loader=yaml.FullLoader)

		self.hierarchyOrder = [ list( each.keys() )[0] for each in self.descriptor["pipeline"]["hierarchy"] ]

		# self.epiPath = "<root>/<proj>/EPISODES/"
		# self.compPath = "<root>/<proj>/NUKE/_timeline/<ep>/<shot>/scripts/<shot>_v<version>.nk" #E:\146_BACKUP_LTO\aykut_eniste_2_fw25096\nuke\Reel_1\AE2_R01_S001_P0010\scripts
		# self.renderPath = "<root>/<proj>/NUKE/_timeline/<ep>/<shot>/renders/<shot>_v<version>/"
		# self.draftPath = "<root>/<proj>/EPISODES/<ep>/FROM_ONLINE/PREVIEW/"

	def getEntityFromCompFile(self, compFile):
		""""""
		self.compREGEX = r"[a-zA-Z0-9_/:]+/(?P<proj>[a-zA-Z0-9_ ]+)/NUKE/_timeline/(?P<ep>\w+)/(?P<shot>\w+)/scripts/(?P=shot)_v(?P<version>\d{2}).nk"
		#self.compREGEX = r"[a-zA-Z0-9_/:]+/(?P<proj>\w+)/NUKE/(?P<ep>\w+)/_timeline/(?P<shot>\w+)/scripts/(?P=shot)_v(?P<version>\d{2}).nk"

		matchObj = re.match(self.compREGEX, compFile)

		try:
			if len(matchObj.groups()) != 4:
				print("This comp file does not that the pipeline!")
				raise
		except AttributeError as e:
			print("This comp file does not that the pipeline!")
			raise

		return matchObj.groups()

	def convertTemplate2REX(self, pipeline):
		""""""

		filePath = self.descriptor["pipeline"][pipeline]

		for i in range(len(self.hierarchyOrder)):
			count = 0
			
			print(list(self.descriptor["pipeline"]["hierarchy"][i].items())[0][1])
			
			def replMet(matchobj):
				nonlocal count
				if count==0:
					count+=1
					return matchobj.expand(r'(?P<\1>\\w+)')
				else:
					count+=1
					return matchobj.expand(r'(?P=\1)')

			filePath = re.sub("<(%s)>" %self.hierarchyOrder[i], replMet, filePath)

		return filePath

	def listCompPath(self, *inputs):
		""""""
		return self._listPaths("compPath", *inputs)

	def listCompOutputPath(self, *inputs):
		""""""
		return self._listPaths("compOutputPath", *inputs)

	def _listPaths(self, pipeline, *inputs):
		"""Query and list comp work files based on criteria inputs"""

		filePath = self.descriptor["pipeline"][pipeline]

		if len(inputs) > len(self.hierarchyOrder):
			raise

		filePath = re.sub("<root>", self.root, filePath)

		# Replace template path with inputs
		for i in range(len(inputs)):
			# If not specify, make it unix wildcard for glob
			repl = inputs[i] if inputs[i] else "*"

			subREX = re.compile(self.hierarchyOrder[i])
			filePath = subREX.sub(repl, filePath)

		allFilePaths = glob.glob(filePath)

		return allFilePaths

	def transcribeCompPath(self, *inputs):
		""""""
		return self.transcribeFilePath(self, "compPath", *inputs)

	def transcribeCompOutputPath(self, *inputs):
		""""""
		return self.transcribeFilePath(self, "compOutputPath", *inputs)

	def _transcribeFilePath(self, pipeline, *inputs):
		"""inputs are project, ep, seq, shot, so on.. Get filepath concatted at last input"""

		filePath = self.descriptor["pipeline"][pipeline]
		
		if len(inputs) > len(self.hierarchyOrder):
			raise

		concatPathSplit = []

		# Concat RenderPath at the last input. Ex: if shot is provided, find first mention of shot and concat the path at that point.
		filePath = re.sub("<root>", self.root, filePath)

		for each in re.split("/", filePath):
			concatREX = re.compile(self.hierarchyOrder[len(inputs)-1])
			matchObj = concatREX.search(each)

			concatPathSplit.append(each)
			
			if matchObj:
				break
			
		concatePath = "/".join(concatPathSplit)

		# Replace template path with inputs
		for i in range(len(inputs)):
			subREX = re.compile(self.hierarchyOrder[i])
			concatePath = subREX.sub(inputs[i], concatePath)

		return concatePath

	def transcribeTempBackupPath(self, *inputs):
		""""""
		pathSplit = [self.root]
		pathSplit.extend(inputs)

		return "/".join(pathSplit)

if __name__ == "__main__":
	xx = ProjectHierachy("50M2")
	# compPath = "X:/PROJECTS/_BACKUP/Gamonya_fw23695/NUKE/_timeline/Reel_1/GMY_S001_P001/scripts/GMY_S001_P001_v04.nk"
	# aa = xx.getEntityFromCompFile(compPath)
	# print(aa)
	# bb = xx.transcribeRenderPath(*aa)
	# print(bb)
	# cc = xx.listCompPaths(*aa)
	# print(cc)
	cc = xx.convertTemplate2REX("compPath")

	print(cc)