# -*- coding: utf-8 -*-
"""
Created on Wed Aug 31 13:46:29 2011

@author: simon
"""

VOL_EXTENSIONS = ['nii','img','mgz','mgh']

import os, tempfile, json, shutil, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))
from commandGroup import CommandGroup

# Read config file
configDir = os.path.join(os.path.dirname(__file__), 'config')
config = json.load(open(os.path.join(configDir, 'config.json'), 'r'))

# Use NIFTI files
os.environ['FSLOUTPUTTYPE'] = 'NIFTI'

anatomicalDir = os.path.join(config['General']['DataDir'], 'mri', 'raw')

# Get registration template
regTemplate = None
if config['Anatomical']['RegistrationTemplate']:
    # Check that directory exists
    run = str(config['Anatomical']['RegistrationTemplate']).zfill(3)
    templateDir = os.path.join(anatomicalDir, run)
    if os.path.exists(templateDir) and os.path.isdir(templateDir):
        # Find registration template in directory
        for file in os.listdir(templateDir):
            if os.path.splitext(file)[1][1:] in VOL_EXTENSIONS:
                regTemplate = os.path.join(templateDir, file)
                break
    
    if not regTemplate:
        raise Exception('Specified registration template '+run+' does not exist')

volsToAverage = []
tmpdir = tempfile.mkdtemp(prefix='mriaverageanatomical-')
try:
    # Perform registration of anatomicals
    cmdGroup = CommandGroup()
    for dirpath, dirnames, filenames in os.walk(anatomicalDir):
        for file in filenames:
            if os.path.splitext(file)[1][1:] in VOL_EXTENSIONS:
                volume = os.path.join(dirpath, file)
                
                if not regTemplate:
                # If no template specified, this is our template
                    regTemplate = volume
                    continue
                elif volume == regTemplate:
                    # Don't average the template
                    break
                
                regVolume = os.path.join(tmpdir, os.path.basename(dirpath)) \
                            +'.nii'
                volsToAverage.append(regVolume)
                cmd = ['fsl_rigid_register',
                       '-r', regTemplate,
                       '-i', volume,
                       '-o', regVolume]
                cmdGroup.run(cmd)
                break
    
    cmdGroup.wait()
    
    # Average anatomicals
    outVolume = os.path.join(config['General']['DataDir'], 'mri',
                             'avg.'+config['Anatomical']['Format'])
    
    fslmathsCmd = [os.path.join(os.environ['FSL_BIN'], 'fslmaths'), regTemplate]
    for volume in volsToAverage:
        fslmathsCmd.extend(['-add', volume])
    fslmathsCmd.extend(['-div', str(len(volsToAverage)), outVolume])
    CommandGroup(fslmathsCmd)
finally:
    if not config['General']['Debug']:
        shutil.rmtree(tmpdir)