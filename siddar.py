#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================================
#
# MIT License
# http://opensource.org/licenses/MIT
# Copyright (c) 2013 Denys Orlenko
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright holders
# shall not be used in advertising or otherwise to promote the sale, use or
# other dealings in this Software without prior written authorization.
#
# ==============================================================================

import os
import os.path
import shutil
import tarfile
import hashlib
import argparse
import fnmatch
import sys

STR_EMPTY = ''
STR_SLASH = '/'
STR_POINT = '.'
STR_TAB = '\t'
STR_EOL = '\n'
STR_CAT_EXT = '.cat'
STR_TAR_EXT = '.tar'
STR_GZ_EXT = '.tar.gz'
STR_BZ2_EXT = '.tar.bz2'

STR_DIR_LIST = 'DIR_LIST'
STR_DIR = 'DIR'
STR_DIR_END = 'DIR_END'
STR_FILE = 'FILE'
STR_FILE_END = 'FILE_END'
STR_DIR_LIST_END = 'DIR_LIST_END'

STR_HASH_LIST = 'HASH_LIST'
STR_HASH = 'HASH'
STR_HASH_LIST_END = 'HASH_LIST_END'


def calcHash(path):  # IOError
    h = hashlib.sha256()
    
    with open(path, 'rb') as f:  # IOError
        block = f.read(h.block_size)
        while block:
            h.update(block)
            block = f.read(h.block_size)
    
    return h.hexdigest()


class CatalogFormatError(Exception):
    pass


class HashNameError(Exception):
    pass


class FileInfo():
    def __init__(self, isDir):
        self.marked = False  # for 'include'
        self.isDir = isDir


def hashName(info):  # HashNameError
    if info.isDir or (info.hash == STR_EMPTY) or (info.size == -1):
        raise HashNameError()
    return info.hash + '.' + str(info.size)


class FileList():  # OSError, IOError, CatalogFormatError
    def __init__(self):
        self.dict = {}
    
    def getDirList(self, rootDir, relDir=STR_EMPTY):  # OSError
        # rootDir, relDir - unicode objects
        if relDir == STR_EMPTY:
            self.dict.clear()
        currentDir = rootDir + relDir
        currentDirList = os.listdir(currentDir)  # OSError
        for f in currentDirList:
            fullPath = currentDir + STR_SLASH + f
            relPath = relDir + STR_SLASH + f
            if os.path.isdir(fullPath):  # OSError
                pathInfo = FileInfo(True)
                pathInfo.mtime = int(os.path.getmtime(fullPath))  # OSError
                self.dict[relPath] = pathInfo
                self.getDirList(rootDir, relPath)
            elif os.path.isfile(fullPath):  # OSError
                pathInfo = FileInfo(False)
                # read mtime, size and hash directly before file checking / archiving
                self.dict[relPath] = pathInfo
    
    def __unmarkAll__(self):
        for key in self.dict:
            self.dict[key].marked = False
    
    # include only matched files/folders
    # use for "find"
    def include(self, patternList):
        if (patternList != None) and (len(patternList) > 0):
            # unmark all records
            self.__unmarkAll__()
            # mark included
            for pattern in patternList:
                for key in self.dict:
                    if fnmatch.fnmatch(key, pattern):
                        self.dict[key].marked = True
            # remove not marked (not included)
            keyList = list(self.dict.keys())
            for key in keyList:
                if not self.dict[key].marked:
                    del self.dict[key]
    
    # include not only matched files/folders but also all parent folders for matched files/folders
    # use for "create" and "restore"
    def includeHierarchy(self, patternList):
        if (patternList != None) and (len(patternList) > 0):
            # unmark all records
            self.__unmarkAll__()
            # mark included
            keyList = list(self.dict.keys())
            for pattern in patternList:
                for key in self.dict:
                    if fnmatch.fnmatch(key, pattern):
                        self.dict[key].marked = True
                        # mark folders with marked files/folders
                        d = os.path.dirname(key)
                        while d != STR_SLASH:
                            self.dict[d].marked = True
                            d = os.path.dirname(d)
            # remove not marked (not included)
            keyList = list(self.dict.keys())
            for key in keyList:
                if not self.dict[key].marked:
                    del self.dict[key]
    
    # check and if not exist all parent folders for files/folders in list
    def fixHierarchy(self):
        keyList = list(self.dict.keys())
        for key in keyList:
            d = os.path.dirname(key)
            while d != STR_SLASH:
                if d not in keyList:
                    pathInfo = FileInfo(False)
                    pathInfo.marked = False  # for 'include'
                    pathInfo.isDir = True
                    pathInfo.mtime = self.dict[key].mtime
                    self.dict[d] = pathInfo
                d = os.path.dirname(d)
    
    def exclude(self, patternList):
        if (patternList != None) and (len(patternList) > 0):
            for pattern in patternList:
                keyList = list(self.dict.keys())
                for key in keyList:
                    if fnmatch.fnmatch(key, pattern):
                        del self.dict[key]
    
    # def calcHashes(self, rootDir, verbose=False):  # IOError
    #    if verbose:
    #        s1 = 0
    #        for key in self.dict:
    #            if (not self.dict[key].isDir) and (self.dict[key].hash == STR_EMPTY):
    #                s1 = s1 + self.dict[key].size
    #    # rootDir - unicode object
    #    s2 = 0
    #    for key in self.dict:
    #        if (not self.dict[key].isDir) and (self.dict[key].hash == STR_EMPTY):
    #            self.dict[key].hash = calcHash(rootDir + STR_SLASH + key) # IOError
    #            if verbose:
    #                s2 = s2 + self.dict[key].size
    #                print('Calculated hash: ' + str(100*s2/s1) + '% - ' + str(s2) + '/' + str(s1))
    
    def save(self, fObject):  # IOError
        # fObject = open('file.name', mode='w', encoding='utf-8')
        fObject.write(STR_DIR_LIST + STR_EOL)
        key_list = list(self.dict.keys())
        key_list.sort()
        for key in key_list:
            if self.dict[key].isDir:
                fObject.write(STR_DIR + STR_EOL)
                fObject.write(key + STR_EOL)
                fObject.write(str(self.dict[key].mtime) + STR_EOL)
                fObject.write(STR_DIR_END + STR_EOL)
            else:
                fObject.write(STR_FILE + STR_EOL)
                fObject.write(key + STR_EOL)
                fObject.write(str(self.dict[key].mtime) + STR_EOL)
                fObject.write(str(self.dict[key].size) + STR_EOL)
                fObject.write(self.dict[key].hash + STR_EOL)
                fObject.write(STR_FILE_END + STR_EOL)
        fObject.write(STR_DIR_LIST_END + STR_EOL)
    
    def load(self, fObject):  # IOError, CatalogFormatError
        # fObject = open('file.name', mode='r', encoding='utf-8')
        self.dict.clear()
        fObject.seek(0, os.SEEK_SET)
        
        # consts for state machine
        WAIT_LIST = 0
        WAIT_DIR_FILE = 1
        WAIT_PATH = 2
        WAIT_MTIME = 3
        WAIT_SIZE = 4
        WAIT_HASH = 5
        WAIT_DIR_END = 6
        WAIT_FILE_END = 7
        
        state = WAIT_LIST
        infoIsDir = False
        infoPath = STR_EMPTY
        infoMtime = -1
        infoSize = -1
        infoHash = STR_EMPTY
        for s in fObject:
            line = s.strip()
            if (state == WAIT_LIST) and (line == STR_DIR_LIST):
                state = WAIT_DIR_FILE
            
            elif ((state == WAIT_DIR_FILE) and
                ((line == STR_DIR) or (line == STR_FILE) or (line == STR_DIR_LIST_END))):
                if line == STR_DIR:
                    infoIsDir = True
                    state = WAIT_PATH
                elif line == STR_FILE:
                    infoIsDir = False
                    state = WAIT_PATH
                elif line == STR_DIR_LIST_END:
                    return
            
            elif state == WAIT_PATH:
                infoPath = line
                state = WAIT_MTIME
            
            elif state == WAIT_MTIME:
                infoMtime = int(line)
                if infoIsDir:
                    state = WAIT_DIR_END
                else:
                    state = WAIT_SIZE
            
            elif state == WAIT_SIZE:
                infoSize = int(line)
                state = WAIT_HASH
            
            elif state == WAIT_HASH:
                infoHash = line
                state = WAIT_FILE_END
            
            elif (state == WAIT_DIR_END) and (line == STR_DIR_END):
                self.dict[infoPath] = FileInfo(True)
                self.dict[infoPath].mtime =infoMtime
                isDir = False
                state = WAIT_DIR_FILE
            
            elif (state == WAIT_FILE_END) and (line == STR_FILE_END):
                self.dict[infoPath] = FileInfo(False)
                self.dict[infoPath].mtime =infoMtime
                self.dict[infoPath].size = infoSize
                self.dict[infoPath].hash = infoHash
                state = WAIT_DIR_FILE
            
            else:
                raise CatalogFormatError()  # CatalogFormatError


# key = hash + u'.' + unicode(size)
# value = arch name
# FileList.dict[key].hashName
class HashList():  # IOError, CatalogFormatError
    def __init__(self):
        self.dict = {}
    
    def save(self, fObject):  # IOError
        # fObject = open('file.name', mode='w', encoding='utf-8')
        fObject.write(STR_HASH_LIST + STR_EOL)
        key_list = list(self.dict.keys())
        key_list.sort()
        for key in key_list:
            fObject.write(STR_HASH + STR_TAB + key + STR_TAB + self.dict[key] + STR_EOL)
        fObject.write(STR_HASH_LIST_END + STR_EOL)
    
    def load(self, fObject):  # IOError, CatalogFormatError
        # fObject = open(u'file.name', mode='r', encoding='utf-8')
        self.dict.clear()
        fObject.seek(0, os.SEEK_SET)
        
        WAIT_LIST = 0
        WAIT_HASH = 1
        state = WAIT_LIST
        for s in fObject:
            line = s.strip()
            if (state == WAIT_LIST) and (line == STR_HASH_LIST):
                state = WAIT_HASH
            elif state == WAIT_HASH:
                if line == STR_HASH_LIST_END:
                    return
                else:
                    lst = line.split(STR_TAB)
                    if (len(lst) == 3) and (lst[0] == STR_HASH):
                        self.dict[lst[1]] = lst[2]
                    else:
                        raise CatalogFormatError()


# not correct for unicode file names
class TarFileWriter:  # OSError, IOError, tarfile.TarError
    def __init__(self, name, maxPartSize, type='tar'):
        self.TarName = name
        self.PartNumber = 0
        self.PartSize = 0
        self.PartFile = None
        self.Closed = True
        self.MaxPartSize = (maxPartSize // tarfile.RECORDSIZE) * tarfile.RECORDSIZE
        self.Type = type.lower()
        if type == 'tar':
            self.Ext = STR_TAR_EXT
            self.Mode = 'w:'
        elif type == 'gz':
            self.Ext = STR_GZ_EXT
            self.Mode = 'w:gz'
        elif type == 'bz2':
            self.Ext = STR_BZ2_EXT
            self.Mode = 'w:bz2'
        else:
            raise IOError()
    
    def close(self):  # IOError
        if not self.Closed:
            self.PartFile.close()
            self.PartFile = None
            self.Closed = True
    
    def __new_part(self):  # IOError
        self.close()
        self.PartNumber = self.PartNumber + 1
        self.PartFile = tarfile.open(self.TarName + STR_POINT + str(self.PartNumber) + self.Ext, self.Mode)
        self.PartSize = 0
        self.Closed = False
    
    def add(self, fPath, tarName):  # OSError, IOError, tarfile.TarError
        if self.Closed:
            self.__new_part()
        # prepare file object
        fSize = os.path.getsize(fPath)  # OSError
        fTarInfo = self.PartFile.gettarinfo(fPath)  # tarfile.TarError
        fTarInfo.name = tarName
        
        with open(fPath, 'rb') as fObject:  # IOError
            # copy file to tar
            while ((self.PartSize + fSize + 3*tarfile.BLOCKSIZE) > self.MaxPartSize): 
                fSizeToSave = self.MaxPartSize - self.PartSize - 3*tarfile.BLOCKSIZE
                fTarInfo.size = fSizeToSave
                self.PartFile.addfile(fTarInfo, fObject)  # tarfile.TarError
                self.PartSize = self.PartSize + tarfile.BLOCKSIZE + fSizeToSave
                assert (self.PartSize + 2*tarfile.BLOCKSIZE) == self.MaxPartSize
                self.__new_part()
                fSize = fSize - fSizeToSave
                
            fTarInfo.size = fSize
            self.PartFile.addfile(fTarInfo, fObject)  # tarfile.TarError
            # recalc PartSize
            self.PartSize = self.PartSize + tarfile.BLOCKSIZE + \
                            (fSize // tarfile.BLOCKSIZE) * tarfile.BLOCKSIZE
            if ((fSize % tarfile.BLOCKSIZE) > 0):
                self.PartSize = self.PartSize + tarfile.BLOCKSIZE
        
        assert (self.PartSize + 2*tarfile.BLOCKSIZE) <= self.MaxPartSize
        
        if ((self.PartSize + 3*tarfile.BLOCKSIZE) >= self.MaxPartSize):
            self.close()


# not correct for unicode file names
class TarFileReader:  # KeyError, IOError, tarfile.TarError
    def __init__(self, name):
        self.TarName = name
        self.PartNumber = 0
        self.PartFile = None
        self.Closed = True
        if os.path.isfile(name + '.1' + STR_TAR_EXT):
            self.Ext = STR_TAR_EXT
        elif os.path.isfile(name + '.1' + STR_GZ_EXT):
            self.Ext = STR_GZ_EXT
        elif os.path.isfile(name + '.1' + STR_BZ2_EXT):
            self.Ext = STR_BZ2_EXT
        else:
            raise IOError()
    
    def close(self):  # IOError
        if not self.Closed:
            self.PartFile.close()
            self.PartFile = None
            self.Closed = True
    
    def __next_part(self):  # IOError
        self.close()
        self.PartNumber = self.PartNumber + 1
        self.PartFile = tarfile.open(self.TarName + STR_POINT + str(self.PartNumber) + self.Ext)
    
    # def list(self):
    #    self.PartNumber = 0
    #    noFile = False
    #    lst = []
    #    while not noFile:
    #        try:
    #            self.__next_part()
    #        except IOError:
    #            noFile = True
    #        if not noFile:
    #            fTarInfo = self.PartFile.next()
    #            while fTarInfo <> None:
    #                if fTarInfo.name not in lst:
    #                    lst.append(fTarInfo.name)
    #                fTarInfo = self.PartFile.next()
    #    return lst
    
    def extract(self, tarName, fPath):  # KeyError, IOError, tarfile.TarError
        self.PartNumber = 0
        
        # ищем первый том в котором есть такой файл
        found = False
        noFile = False
        while not (found or noFile):
            try:
                self.__next_part()
                fTarInfo = self.PartFile.getmember(tarName)
                found = True
            except IOError:
                noFile = True
            except KeyError:
                pass
        
        if found:
            with open(fPath, 'wb') as fObject:  # IOError
                while found:
                    # копируем в файл
                    tarBuffer = self.PartFile.extractfile(fTarInfo)  # tarfile.TarError
                    fSize = fTarInfo.size
                    while (fSize > 0):
                        if (fSize > tarfile.BLOCKSIZE):
                            fSizeToSave = tarfile.BLOCKSIZE
                        else:
                            fSizeToSave = fSize
                        fObject.write(tarBuffer.read(tarfile.BLOCKSIZE))  # IOError, tarfile.TarError
                        fSize = fSize - fSizeToSave
                    tarBuffer.close()  # tarfile.TarError
                    # проверяем в следующем томе
                    try:
                        self.__next_part()
                        fTarInfo = self.PartFile.getmember(tarName)  # tarfile.TarError
                    except IOError:
                        found = False
                    except KeyError:
                        found = False
        else:
            raise KeyError()


def fCreate(args):
    # check source
    if not os.path.isdir(args.source):
        print('ERROR: Source not found!')
        return
    
    # check repository
    if not os.path.isdir(args.repository):
        print('ERROR: Repository not found!')
        return
    
    # check if files with backup name exist
    if os.path.isfile(args.repository + STR_SLASH + args.name + STR_CAT_EXT):
        print('ERROR: Such archive already exists!')
        return
    
    # create sourceFileList
    sourceList = FileList()
    try:
        sourceList.getDirList(args.source)
    except IOError as e:
        print('ERROR: Can not read: ' + e.filename)
        return
    
    # include / exclude files / dirs
    sourceList.includeHierarchy(args.include)
    sourceList.exclude(args.exclude)
            
    # create TmpHashList
    hashList = HashList()
    
    if args.reference != None:
        # check if reference file exists
        refPath = args.repository + '/' + args.reference + STR_CAT_EXT
        if not os.path.isfile(refPath):
            print('ERROR: Reference not found!')
            return
        # load referenceList and hashList
        referenceList = FileList()
        try:
            fObject = open(refPath, mode='r', encoding='utf-8')
            referenceList.load(fObject)
            hashList.load(fObject)
        except IOError:
            print('ERROR: Can not read reference catalogue file!')
            return
        except CatalogFormatError:
            print('ERROR: Reference catalogue is damaged!')
            return
        finally:
            fObject.close()
    
    # compression
    compr = 'tar'
    if args.compression != None:
        compr = args.compression
    
    # create TarFileWriter
    writer = TarFileWriter(args.repository + STR_SLASH + args.name, args.size, compr)
    # check files and if new/changed add to archive
    cAll = 0
    cNew = 0
    sizeAll = 0
    sizeNew = 0
    keyList = list(sourceList.dict)
    keyList.sort()
    for fileName in keyList:
        filePath = args.source + fileName
        if not sourceList.dict[fileName].isDir:
            ok = False
            while not ok:
                try:
                    # get date and size
                    sourceList.dict[fileName].mtime = int(os.path.getmtime(filePath))
                    sourceList.dict[fileName].size = os.path.getsize(filePath)
                    # check if such file is in reference
                    if (not args.recalculate) and (args.reference != None) and \
                            (fileName in referenceList.dict) and \
                            (not referenceList.dict[fileName].isDir) and \
                            (sourceList.dict[fileName].mtime == referenceList.dict[fileName].mtime) and \
                            (sourceList.dict[fileName].size == referenceList.dict[fileName].size):
                        sourceList.dict[fileName].hash = referenceList.dict[fileName].hash
                    else:
                        # calculate hash
                        sourceList.dict[fileName].hash = calcHash(filePath)
                        # add file to archive
                        tarName = hashName(sourceList.dict[fileName])
                        if tarName not in hashList.dict:
                            hashList.dict[tarName] = args.name
                            writer.add(args.source + fileName, tarName)
                            cNew = cNew + 1
                            sizeNew = sizeNew + sourceList.dict[fileName].size
                    sizeAll = sizeAll + sourceList.dict[fileName].size
                    ok = True
                except (OSError, IOError) as e:
                    print('ERROR: Can not read: ' + e.filename)
                    if args.ignore:
                        answer = 'i'
                    else:
                        answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                    if answer == 'c':
                        writer.close()
                        return
                    elif answer == 'i':
                        del sourceList.dict[fileName]
                        ok = True
                except tarfile.TarError:
                    print('ERROR: Can not write files to archive!')
                    answer = input('Cancel (c) / Retry (other): ')
                    if answer == 'c':
                        writer.close()
                        return
            cAll = cAll + 1
        if not args.quiet:
            sys.stdout.write("\rFiles (New/All): %s / %s, Size (New/All): %.02f Mb / %.02f Mb" % (
                            cNew, cAll, sizeNew/1024.0/1024.0, sizeAll/1024.0/1024.0))
            sys.stdout.flush()
    
    # close TarFileWriter
    writer.close()
    
    if not args.quiet:
        sys.stdout.write(STR_EOL)
        sys.stdout.flush()
    
    # save catalogue
    try:                  
        fObject = open(args.repository + STR_SLASH + args.name + STR_CAT_EXT,
                            mode='w', encoding='utf-8')
        sourceList.save(fObject)
        hashList.save(fObject)
    except IOError:
        print('ERROR: Can not create catalogue file!')
        return
    finally:
        fObject.close()


def fFind(args):
    # check repository
    if not os.path.isdir(args.repository):
        print('ERROR: Repository not found!\n')
        return
    
    # get file list
    catList = os.listdir(args.repository)
    catList.sort()
    keyList = list(catList)
    for key in keyList:
        if not fnmatch.fnmatch(key, args.name + STR_CAT_EXT):
            del catList[catList.index(key)]
    
    # check if something found
    if len(catList) == 0:
        print('ERROR: No catalogue found!\n')
        return
    
    # looking for patterns in all catalogues
    for cat in catList:
        # loading catalogue
        fileList = FileList()
        try:
            fObject = open(args.repository + STR_SLASH + cat, mode='r', encoding='utf-8')
            fileList.load(fObject)
        except IOError:
            print('ERROR: Can not read  catalogue file: ' + cat)
            return
        except CatalogFormatError:
            print('ERROR: Catalogue is damaged: ' + cat)
            return
        finally:
            fObject.close()
        
        # include / exclude files / dirs
        fileList.include(args.include)
        fileList.exclude(args.exclude)
        
        # looking for matching files and dirs
        keyList = list(fileList.dict.keys())
        keyList.sort()
        for key in keyList:
            print(cat + ': ' + key)


def fRestore(args):
    # check repository
    if not os.path.isdir(args.repository):
        print('ERROR: Repository not found!\n')
        return
    
    # check existence of catalogue file
    if not os.path.isfile(args.repository + STR_SLASH + args.name + STR_CAT_EXT):
        print('ERROR: Catalogue not found!\n')
        return
    
    # check destination existence
    if not os.path.isdir(args.destination):
        print('ERROR: Destination not found!\n')
        return
    
    # read FileList and HashList from catalogue
    sourceList = FileList()
    hashList = HashList()
    try:
        fObject = open(args.repository + STR_SLASH + args.name + STR_CAT_EXT,
                            mode='r', encoding='utf-8')
        sourceList.load(fObject)
        hashList.load(fObject)
    except IOError:
        print('ERROR: Can not read catalogue file!')
        return
    except CatalogFormatError:
        print('ERROR: Catalogue is damaged!')
        return
    finally:
        fObject.close()
    
    # include / exclude files / dirs
    sourceList.fixHierarchy()
    sourceList.includeHierarchy(args.include)
    sourceList.exclude(args.exclude)
    
    # create not existing dirs and extract new or changed files
    cAll = 0
    cNew = 0
    sizeAll = 0
    sizeNew = 0
    keyList = list(sourceList.dict)
    keyList.sort()
    for fileName in keyList:
        filePath = args.destination + fileName
        # make directory
        if sourceList.dict[fileName].isDir:
            fileDir = filePath
        else:
            (fileDir, stub) = os.path.split(filePath)
        ok = False
        while not ok:
            try:
                if os.path.isfile(fileDir):
                    os.remove(fileDir)
                if not os.path.isdir(fileDir):
                    os.makedirs(fileDir)
                ok = True
            except OSError as e:
                print('ERROR: Can not create directory: ' + e.filename)
                if args.ignore:
                    answer = 'i'
                else:
                    answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                if answer == 'c':
                    return
                elif answer == 'i':
                    ok = True
        # restore file
        if not sourceList.dict[fileName].isDir:
            hashKey = hashName(sourceList.dict[fileName])
            backupFile = hashList.dict[hashKey]
            ok = False
            while not ok:
                try:
                    # check if such file exists
                    reader = TarFileReader(args.repository + STR_SLASH + backupFile)
                    if os.path.isfile(filePath) and \
                            (sourceList.dict[fileName].mtime == int(os.path.getmtime(filePath))) and \
                            (sourceList.dict[fileName].size == os.path.getsize(filePath)) and \
                            (sourceList.dict[fileName].hash == calcHash(filePath)):
                        pass
                    else:
                        if os.path.isdir(filePath):
                            shutil.rmtree(filePath)
                        reader.extract(hashKey, filePath)
                        cNew = cNew + 1
                        sizeNew = sizeNew + sourceList.dict[fileName].size
                    ok = True
                except (OSError, IOError) as e:
                    print('ERROR: Can not restore file: ' + e.filename)
                    if args.ignore:
                        answer = 'i'
                    else:
                        answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                    if answer == 'c':
                        return
                    elif answer == 'i':
                        ok = True
                finally:
                    reader.close()
            cAll = cAll + 1
            sizeAll = sizeAll + sourceList.dict[fileName].size
        # set time
        ok = False
        while not ok:
            try:
                os.utime(filePath,
                        (sourceList.dict[fileName].mtime,
                        sourceList.dict[fileName].mtime))
                ok = True
            except OSError as e:
                print('ERROR: Can not update time for: ' + e.filename)
                if args.ignore:
                    answer = 'i'
                else:
                    answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                if answer == 'c':
                    return
                elif answer == 'i':
                    ok = True
        sys.stdout.write("\rFiles (New/All): %s / %s, Size (New/All): %.02f Mb / %.02f Mb" % (
                        cNew, cAll, sizeNew/1024.0/1024.0, sizeAll/1024.0/1024.0))
        sys.stdout.flush()
    
    sys.stdout.write(STR_EOL)
    sys.stdout.flush()
    
    # get FileList for destination
    if args.delete:
        destinationList = FileList()
        destinationList.getDirList(args.destination)
        # remove old files
        keyList = list(destinationList.dict.keys())
        keyList.sort()
        for fileName in keyList:
            filePath = args.destination + fileName
            if (not destinationList.dict[fileName].isDir) and \
                    (fileName not in sourceList.dict):
                ok = False
                while not ok:
                    try:
                        os.remove(filePath)
                        ok = True
                    except OSError as e:
                        print('ERROR: Can not delete file: ' + e.filename)
                        if args.ignore:
                            answer = 'i'
                        else:
                            answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                        if answer == 'c':
                            return
                        elif answer == 'i':
                            ok = True
        # remove old dirs
        keyList = list(destinationList.dict.keys())
        keyList.sort()
        for fileName in keyList:
            filePath = args.destination + fileName
            if destinationList.dict[fileName].isDir and \
                    (fileName not in sourceList.dict):
                ok = False
                while not ok:
                    try:
                        if os.path.isdir(filePath):
                            shutil.rmtree(filePath)
                        ok = True
                    except OSError as e:
                        print('ERROR: Can not delete directory: ' + e.filename)
                        if args.ignore:
                            answer = 'i'
                        else:
                            answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                        if answer == 'c':
                            return
                        elif answer == 'i':
                            ok = True

# source - папка, которая архивируется
# destination - папка, в которую извлекается
# repository - папка в которой хранится архив
# name - имя архива (без расширения и без пути, архив должен быть в [repository])
# reference - путь/имя каталога эталона с расширением
# slice - том архива, перед расширением номер [backup].3.tar
# catalogue - каталог архива - [backup].cat
parser = argparse.ArgumentParser(description='version 0.6')
subparsers = parser.add_subparsers()

parser_create = subparsers.add_parser('create') #
parser_create.add_argument('source', help='Directory tree that will be backed up.') # dir
parser_create.add_argument('repository', help='Directory in which backup will be stored.') # dir
parser_create.add_argument('name', help='Basename for backup.') # name
parser_create.add_argument('-r', '--reference', help='Reference basename for differential backup. Reference catalog should be stored in the same repository.') # path
parser_create.add_argument('-s', '--size', type=int, default=1024*1024*1020, help='Size of one slice.')
parser_create.add_argument('-i', '--include', nargs='*', help='Mask list. Files/Dirs matching at least one mask will be included in backup. If no mask specified all Files/Dirs will be included.')
parser_create.add_argument('-e', '--exclude', nargs='*', help='Mask list. Files/Dirs matching at least one mask will be excluded from backup.')
parser_create.add_argument('-q', '--quiet', action='store_true', help='Nothing is displayed if operation succeeds.') # !!!
parser_create.add_argument('-g', '--ignore', action='store_true', help='Ignore all errors.')
parser_create.add_argument('-c', '--compression', help="'tar'-default, 'gz' or 'bz2'")
parser_create.add_argument('-a', '--recalculate', action='store_true', help="Recalculate all hashes again. Don't use hashes from reference.")
parser_create.set_defaults(func=fCreate)

parser_find = subparsers.add_parser('find') # simple regular expressions
parser_find.add_argument('repository', help='Directory in which backup is stored.') # dir
parser_find.add_argument('name', help='Mask for backup basename. Several backups can be looked thorough.') # name pattern (without ext)
parser_find.add_argument('-i', '--include', nargs='*', help='Mask list. Files/Dirs matching at least one mask will be shown. If no mask specified all Files/Dirs will be shown.')
parser_find.add_argument('-e', '--exclude', nargs='*', help='Mask list. Files/Dirs matching at least one mask will not be shown.')
parser_find.set_defaults(func=fFind)

parser_restore = subparsers.add_parser('restore') # restore backup
parser_restore.add_argument('repository', help='Directory in which backup is stored.') # dir
parser_restore.add_argument('name', help='Basename for backup to be restored.') # name
parser_restore.add_argument('destination', help='Directory which will be restored.') # dir
parser_restore.add_argument('-i', '--include', nargs='*', help='Mask list. Files/Dirs matching at least one mask will be restored. If no mask specified all Files/Dirs will be restored.')
parser_restore.add_argument('-e', '--exclude', nargs='*', help='Mask list. Files/Dirs matching at least one mask will not be restored.')
parser_restore.add_argument('-d', '--delete', action='store_true', help='Delete Files/Dirs not existing in backup.')
parser_restore.add_argument('-g', '--ignore', action='store_true', help='Ignore all errors.')
parser_restore.set_defaults(func=fRestore)

args = parser.parse_args()
args.func(args)

# // целочисленное деление, результат – целое число (дробная часть отбрасывается)
# % деление по модулю

# tar file format
# 1 file info - BLOCKSIZE (512)
# 1 file data - filled by zeros to BLOCKSIZE (512)
# 2 file info - BLOCKSIZE (512)
# 2 file data - filled by zeros to BLOCKSIZE (512)
# N file info - BLOCKSIZE (512)
# N file data - filled by zeros to BLOCKSIZE (512)
# two finishing zero blocks - BLOCKSIZE * 2 (512 * 2)
# filled by zeros to RECORDSIZE (BLOCKSIZE * 20) (512 * 20)
# tarfile.BLOCKSIZE = 512
# tarfile.RECORDSIZE = BLOCKSIZE * 20
