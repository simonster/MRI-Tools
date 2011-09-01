# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:32:47 2011

@author: simon
"""

VOL_EXTENSIONS = ['nii','img','mgz','mgh']

import os, json, subprocess, re, sys, shutil, tempfile

# Read config file
configDir = os.path.join(os.path.dirname(__file__), 'config')
config = json.load(open(os.path.join(configDir, 'config.json'), 'r'))

# Determine whether there are child directories in DICOM dir
originalDicomDir = config['Unpack']['DICOMDir']
dicomDirNotFlat = False
for file in os.listdir(originalDicomDir):
    if os.path.isdir(os.path.join(originalDicomDir, file)):
        dicomDirNotFlat = True
        break

# If there are child directories, create a new, flat directory struction
if dicomDirNotFlat:
    print('DICOM directory not flat; flattening')
    flatDicomDir = tempfile.mkdtemp(prefix='mriunpack-')
    for root, dirs, files in os.walk(originalDicomDir):
        for file in files:
            shutil.copyfile(os.path.join(root, file),
                            os.path.join(flatDicomDir, file))
else:
    print('DICOM directory is flat')
    flatDicomDir = originalDicomDir

# Scan directory (first pass)
print('Scanning '+config['Unpack']['DICOMDir']+' for DICOM files...')
out = subprocess.check_output(['dcmunpack',
                                '-src', flatDicomDir])

# Get sequence names and numbers
unpackCmd = ['dcmunpack', '-src', flatDicomDir,
             '-targ', config['General']['DataDir']]

# Figure out where to put sequences
seqConfig = config['Unpack']['Sequences']
lastSequence = None
lastSequenceNum = 0
for run, sequence in re.findall('\n([0-9]+) ([^ ]+)(?: [0-9.]+){4}', out):
    if sequence in seqConfig:
        seqInfo = seqConfig[sequence]
        
        # Handle sequences that save multiple runs
        if isinstance(seqInfo, list):
            if lastSequence == sequence and lastSequenceNum+1 < len(seqInfo):
                seqInfo = seqInfo[lastSequenceNum+1]
                lastSequenceNum += 1
            else:
                seqInfo = seqInfo[0]
                lastSequence = sequence
                lastSequenceNum = 0
        else:
            lastSequence = sequence
            lastSequenceNum = 0
        
        # Construct command
        unpackCmd.extend(['-run', run, seqInfo['subdir'], seqInfo['format'],
                          seqInfo['stemname']])
    else:
        print >> sys.stderr, 'Run '+run+': No match for '+sequence
        unpackCmd.extend(['-run', run, 'other', 'nii', 'vol'])

if not os.path.exists(config['General']['DataDir']):
    os.mkdir(config['General']['DataDir'])
subprocess.call(unpackCmd)

# Correct for Sphinx position
if 'CorrectForSphinxPosition' in config['Unpack'] \
and config['Unpack']['CorrectForSphinxPosition']:
    for dirpath, dirnames, filenames in os.walk(config['General']['DataDir']):
        for f in filenames:
            if os.path.splitext(f)[1][1:] in VOL_EXTENSIONS:
                fPath = os.path.join(dirpath, f)
                shutil.move(fPath, fPath+'.bak')
                subprocess.call(['mri_convert', '-i', fPath+'.bak', '-o', fPath,
                                 '--sphinx'])
                if not config['General']['Debug']:
                    os.unlink(fPath+'.bak')
        