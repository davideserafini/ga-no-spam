import os
import os.path
import re
import shutil
import urllib

# Clean each line removing additional characters present in the file on github
def cleanLine(line):
    return line.replace("- ", "").replace("<i></i>", "");

# Prepare the line for regex, cleaning it and then escaping for the regex
def prepareLine(line):
    line = cleanLine(line)
    return re.escape(line)

# Save the list to an output file
def saveToFile(outputPath, newContent):
    newFile = open(outputPath, "w")
    newFile.write("\n\n".join(newContent))
    newFile.close()

# Check if the script is launched from within a repository structure or not
def checkRepositoryMode():
    thisFilePath = os.path.realpath(__file__)
    thisDirectoryName = os.path.basename(os.path.dirname(thisFilePath))
    return thisDirectoryName == "tools" and os.path.exists(os.path.join(os.path.dirname(thisFilePath), os.pardir, URL_LOCAL_SOURCE))

# Get correct path for the tmp directory
def getTmpDirectory():
    thisFilePath = os.path.realpath(__file__)
    return os.path.abspath(os.path.join(thisFilePath, os.pardir, TMP_DIR))

# Get correct path for the output directory
def getOutputDirectory():
    thisFilePath = os.path.realpath(__file__)
    return os.path.abspath(os.path.join(thisFilePath, os.pardir, OUTPUT_DIR))

# Get correct path for output file
def getOutputFile(outputFile):
    return os.path.join(getOutputDirectory(), outputFile)

# Constants
# Remote url of the file
URL_REMOTE_SOURCE = "https://raw.githubusercontent.com/davideserafini/ga-no-spam/master/README.md"
# Local name of downlaoded file
URL_DESTINATION = "source.txt"
# Local name of local repository file
URL_LOCAL_SOURCE = "README.md"
# Temp directory
TMP_DIR = "tmp"
# Output directory
OUTPUT_DIR = "output"
# Regex output file
OUTPUT_REGEX_HOSTNAMES = "hostnames_regex.txt"
# Hostname output files
OUTPUT_HOSTNAMES = "hostnames.txt"
# URLS output files
OUTPUT_URLS = "urls.txt"
# Max Length for regex
FILTER_MAX_LENGTH = 255

outputDir = getOutputDirectory()
sourceFilePath = "";

repositoryMode = checkRepositoryMode();

if repositoryMode:
    # Use local file when running this script from the repository structure     
    thisFilePath = os.path.realpath(__file__)
    sourceFilePath = os.path.join(os.path.dirname(thisFilePath), os.pardir, URL_LOCAL_SOURCE)
else:
    # Create temp directory
    tmpDir = getTmpDirectory()
    if not os.path.exists(tmpDir):
        os.mkdir(tmpDir)

    sourceFilePath = os.path.join(tmpDir, URL_DESTINATION)

    # Download file with URLs list and save it locally
    sourceFile = urllib.URLopener()
    sourceFile.retrieve(URL_REMOTE_SOURCE, sourceFilePath);

# Read downloaded file in list
lines = [line.rstrip('\n') for line in open(sourceFilePath)]

# Flags to check if we are looping on referral spam or spam URLs
inReferralSpamList = False
inUrlSpamList = False

# List of domains found in the referral list. These domains are ascii encoded and will be converted to regex
referralSpam = []
# List of domains found in the referral list. These domains are NOT ascii encoded and won't be converted to regex
hostnameSpam = []
# List of URLs found in the spam list. These URLs won't be converted to regex
urlSpam = []
# List of ascii domains converted into regex. Each entry fits in length the FILTER_MAX_LENGTH value
regexFilters = []

# Loop on the file
for line in lines:
    # Skip empty lines
    if line != "":
        # Check only lines starting with a -
        if (line[0] == "-"):
            if inReferralSpamList:
                try:
                    line = line.decode("ascii")
                except UnicodeDecodeError:
                    hostnameSpam.append(cleanLine(line))
                else:
                    referralSpam.append(prepareLine(line))

            if inUrlSpamList:
                urlSpam.append(cleanLine(line))

        # Use titles as markers of the lists
        if line == "## Referral spam":
            inReferralSpamList = True
        if line == "## Common URLs":
            inReferralSpamList = False
            inUrlSpamList = True

# Create the regex from the ascii domains. Keep the length below FILTER_MAX_LENGTH
for domain in referralSpam:
    lineLength = len(domain)
    alreadyBuiltLineLength = 0 if len(regexFilters) == 0 else len(regexFilters[len(regexFilters) - 1])

    if (alreadyBuiltLineLength > 0 and alreadyBuiltLineLength + lineLength <= FILTER_MAX_LENGTH):
        regexFilters[len(regexFilters) - 1] += "|" + domain
    else:
        regexFilters.append(domain)

# Create output directory
if not os.path.exists(outputDir):
    os.mkdir(outputDir)

# Create output files
# Save regex
saveToFile(getOutputFile(OUTPUT_REGEX_HOSTNAMES), regexFilters)

# Save hostnames
saveToFile(getOutputFile(OUTPUT_HOSTNAMES), hostnameSpam)

# Save spam URLs
saveToFile(getOutputFile(OUTPUT_URLS), urlSpam)

# Cleanup of temp directory
if not repositoryMode:
    shutil.rmtree(getTmpDirectory())

