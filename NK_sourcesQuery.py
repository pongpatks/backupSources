import nuke

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


# Sources

for eachNode in nuke.allNodes():
	eachNodeKnobs = eachNode.knobs()

	if eachNodeKnobs.has_key("file"):
		if not eachNodeKnobs.has_key("Render") and not eachNodeKnobs.has_key("Execute"):
			if not eachNode.hasError():
				readfile = eachNodeKnobs['file'].value().strip()
				if readfile:
					print(readfile)