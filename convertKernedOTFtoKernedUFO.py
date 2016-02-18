#!/usr/bin/python
import os
import sys
import string
import subprocess
from defcon import Font
from fontTools import ttLib

import getKerningPairsFromOTF
# reload(getKerningPairsFromOTF)

__doc__ ='''\

    This script extracts kerning and groups from a compiled OTF and injects
    them into a new UFO file (which is created via tx).
    It requires the script 'getKerningPairsFromOTF.py'; which is distributed
    in the same folder.

    usage:
    python dumpKernObjectFromOTF.py font.otf

    '''


kKernFeatureTag = 'kern'
compressSinglePairs = True
# Switch to control if single pairs shall be written plainly, or in a more space-saving notation (using enum).


def sortGlyphs(glyphlist):
    # Sort glyphs in a way that glyphs from the exceptionList, or glyphs starting with 'uni' names do not get to be key (first) glyphs.
    # An infinite loop is avoided, in case there are only glyphs matching above mentioned properties.
    exceptionList = 'dotlessi dotlessj kgreenlandic ae oe AE OE uhorn'.split()

    glyphs = sorted(glyphlist)
    for i in range(len(glyphs)):
        if glyphs[0] in exceptionList or glyphs[0].startswith('uni'):
            glyphs.insert(len(glyphs), glyphs.pop(0))
        else:
            continue

    return glyphs


def nameClass(glyphlist, flag):
    glyphs = sortGlyphs(glyphlist)
    if len(glyphs) == 0:
        name = 'error!!!'
        print 'Found empty class.'
    else:
        name = glyphs[0]

    if name in string.ascii_lowercase:
        case = '_LC'
    elif name in string.ascii_uppercase:
        case = '_UC'
    else:
        case = ''

    return '@MMK%s%s%s' % (flag, name, case)



def makeKernObjects(fontPath):
    f = getKerningPairsFromOTF.ReadKerning(fontPath)

    groups = {}
    kerning = {}

    for kerningClass in f.allLeftClasses:
        glyphs = sortGlyphs(f.allLeftClasses[kerningClass])
        className = nameClass(glyphs, '_L_')
        groups.setdefault(className, glyphs)

    for kerningClass in f.allRightClasses:
        glyphs = sortGlyphs(f.allRightClasses[kerningClass])
        className = nameClass(glyphs, '_R_')
        groups.setdefault(className, glyphs)


    for (leftClass, rightClass), value in sorted(f.classPairs.items()):
        leftGlyphs = sortGlyphs(f.allLeftClasses[leftClass])
        leftClassName = nameClass(leftGlyphs, '_L_')

        rightGlyphs = sortGlyphs(f.allRightClasses[rightClass])
        rightClassName = nameClass(rightGlyphs, '_R_')

        kerning[(leftClassName, rightClassName)] = value


    kerning.update(f.singlePairs)
    return groups, kerning


def injectKerningToUFO(ufoPath, groups, kerning):
    ufo = Font(ufoPath)
    ufo.kerning.clear()
    ufo.groups.clear()

    print 'Injecting OTF groups and kerning into %s ...' % ufoPath
    ufo.groups.update(groups)
    ufo.kerning.update(kerning)
    ufo.save()


def injectOS2TableToUFO(otfPath, ufoPath):
    otfFont = ttLib.TTFont(otfPath)
    os2Table = otfFont['OS/2']
    ufo = Font(ufoPath)

    print 'Injecting OS/2 table into %s ...' % ufoPath

    ufo.info.ascender = os2Table.sTypoAscender
    ufo.info.capHeight = os2Table.sCapHeight
    ufo.info.descender = os2Table.sTypoDescender
    ufo.info.xHeight = os2Table.sxHeight

    ufo.info.openTypeOS2VendorID = os2Table.achVendID
    ufo.info.openTypeOS2TypoAscender = os2Table.sTypoAscender
    ufo.info.openTypeOS2TypoDescender = os2Table.sTypoDescender
    ufo.info.openTypeOS2TypoLineGap = os2Table.sTypoLineGap
    ufo.info.openTypeOS2StrikeoutPosition = os2Table.yStrikeoutPosition
    ufo.info.openTypeOS2StrikeoutSize = os2Table.yStrikeoutSize
    ufo.info.openTypeOS2SubscriptXOffset = os2Table.ySubscriptXOffset
    ufo.info.openTypeOS2SubscriptXSize = os2Table.ySubscriptXSize
    ufo.info.openTypeOS2SubscriptYOffset = os2Table.ySubscriptYOffset
    ufo.info.openTypeOS2SubscriptYSize = os2Table.ySubscriptYSize
    ufo.info.openTypeOS2SuperscriptXOffset = os2Table.ySuperscriptXOffset
    ufo.info.openTypeOS2SuperscriptXSize = os2Table.ySuperscriptXSize
    ufo.info.openTypeOS2SuperscriptYOffset = os2Table.ySuperscriptYOffset
    ufo.info.openTypeOS2SuperscriptYSize = os2Table.ySuperscriptYSize
    ufo.save()


def convertOTFtoUFO(otfPath):
    ufoPath = '%s.ufo' % os.path.splitext(otfPath)[0]
    print 'Creating %s from %s ...' % (ufoPath, otfPath)
    txCommand = 'tx -ufo %s %s' % (otfPath, otfPath.replace('otf', 'ufo'))
    txProcess = subprocess.Popen(txCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output,errors = txProcess.communicate()

    if errors:
        print errors
        sys.exit()

    return ufoPath



errorMessage = '''\

ERROR:
No valid font and/or UFO provided.
The script is used like this:

python %s font.otf
''' % os.path.basename(__file__)



if __name__ == "__main__":

    if len(sys.argv) == 2:
        assumedFontPath = sys.argv[1]

        if  os.path.exists(assumedFontPath) and os.path.splitext(assumedFontPath)[1].lower() in ['.otf', '.ttf']:

            fontPath = assumedFontPath
            groups, kerning = makeKernObjects(fontPath)

            ufoPath = convertOTFtoUFO(fontPath)
            injectKerningToUFO(ufoPath, groups, kerning)
            injectOS2TableToUFO(fontPath, ufoPath)

            print 'done'

        else:
            print errorMessage

    else:
        print errorMessage