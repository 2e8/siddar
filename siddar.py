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


def calc_hash(path):  # IOError
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
    def __init__(self, is_dir):
        self.marked = False  # for 'include'
        self.isDir = is_dir


def hash_name(info):  # HashNameError
    if info.isDir or (info.hash == STR_EMPTY) or (info.size == -1):
        raise HashNameError()
    return info.hash + '.' + str(info.size)


class FileList():  # OSError, IOError, CatalogFormatError
    def __init__(self):
        self.dict = {}
    
    def getDirList(self, root_dir, rel_dir=STR_EMPTY):  # OSError
        # rootDir, relDir - unicode objects
        if rel_dir == STR_EMPTY:
            self.dict.clear()
        current_dir = root_dir + rel_dir
        current_dir_list = os.listdir(current_dir)  # OSError
        for f in current_dir_list:
            full_path = current_dir + STR_SLASH + f
            rel_path = rel_dir + STR_SLASH + f
            if os.path.isdir(full_path):  # OSError
                path_info = FileInfo(True)
                path_info.mtime = int(os.path.getmtime(full_path))  # OSError
                self.dict[rel_path] = path_info
                self.getDirList(root_dir, rel_path)
            elif os.path.isfile(full_path):  # OSError
                path_info = FileInfo(False)
                # read mtime, size and hash directly before file checking / archiving
                self.dict[rel_path] = path_info
    
    def __unmarkAll__(self):
        for key in self.dict:
            self.dict[key].marked = False
    
    # include only matched files/folders
    # use for "find"
    def include(self, pattern_list):
        if (pattern_list is not None) and (len(pattern_list) > 0):
            # unmark all records
            self.__unmarkAll__()
            # mark included
            for pattern in pattern_list:
                for key in self.dict:
                    if fnmatch.fnmatch(key, pattern):
                        self.dict[key].marked = True
            # remove not marked (not included)
            key_list = list(self.dict.keys())
            for key in key_list:
                if not self.dict[key].marked:
                    del self.dict[key]
    
    # include not only matched files/folders but also all parent folders for matched files/folders
    # use for "create" and "restore"
    def includeHierarchy(self, pattern_list):
        if (pattern_list is not None) and (len(pattern_list) > 0):
            # unmark all records
            self.__unmarkAll__()
            # mark included
            key_list = list(self.dict.keys())
            for pattern in pattern_list:
                for key in self.dict:
                    if fnmatch.fnmatch(key, pattern):
                        self.dict[key].marked = True
                        # mark folders with marked files/folders
                        d = os.path.dirname(key)
                        while d != STR_SLASH:
                            self.dict[d].marked = True
                            d = os.path.dirname(d)
            # remove not marked (not included)
            key_list = list(self.dict.keys())
            for key in key_list:
                if not self.dict[key].marked:
                    del self.dict[key]
    
    # check and if not exist all parent folders for files/folders in list
    def fixHierarchy(self):
        key_list = list(self.dict.keys())
        for key in key_list:
            d = os.path.dirname(key)
            while d != STR_SLASH:
                if d not in key_list:
                    path_info = FileInfo(False)
                    path_info.marked = False  # for 'include'
                    path_info.isDir = True
                    path_info.mtime = self.dict[key].mtime
                    self.dict[d] = path_info
                d = os.path.dirname(d)
    
    def exclude(self, pattern_list):
        if (pattern_list is not None) and (len(pattern_list) > 0):
            for pattern in pattern_list:
                key_list = list(self.dict.keys())
                for key in key_list:
                    if fnmatch.fnmatch(key, pattern):
                        del self.dict[key]
    
    def save(self, file_object):  # IOError
        # file_object = open('file.name', mode='w', encoding='utf-8')
        file_object.write(STR_DIR_LIST + STR_EOL)
        key_list = list(self.dict.keys())
        key_list.sort()
        for key in key_list:
            if self.dict[key].isDir:
                file_object.write(STR_DIR + STR_EOL)
                file_object.write(key + STR_EOL)
                file_object.write(str(self.dict[key].mtime) + STR_EOL)
                file_object.write(STR_DIR_END + STR_EOL)
            else:
                file_object.write(STR_FILE + STR_EOL)
                file_object.write(key + STR_EOL)
                file_object.write(str(self.dict[key].mtime) + STR_EOL)
                file_object.write(str(self.dict[key].size) + STR_EOL)
                file_object.write(self.dict[key].hash + STR_EOL)
                file_object.write(STR_FILE_END + STR_EOL)
        file_object.write(STR_DIR_LIST_END + STR_EOL)
    
    def load(self, file_object):  # IOError, CatalogFormatError
        # file_object = open('file.name', mode='r', encoding='utf-8')

        # consts for state machine
        wait_list = 0
        wait_dir_file = 1
        wait_path = 2
        wait_mtime = 3
        wait_size = 4
        wait_hash = 5
        wait_dir_end = 6
        wait_file_end = 7

        self.dict.clear()
        file_object.seek(0, os.SEEK_SET)

        state = wait_list
        info_is_dir = False
        info_path = STR_EMPTY
        info_mtime = -1
        info_size = -1
        info_hash = STR_EMPTY
        for s in file_object:
            line = s.strip()
            if (state == wait_list) and (line == STR_DIR_LIST):
                state = wait_dir_file
            
            elif ((state == wait_dir_file) and
                ((line == STR_DIR) or (line == STR_FILE) or (line == STR_DIR_LIST_END))):
                if line == STR_DIR:
                    info_is_dir = True
                    state = wait_path
                elif line == STR_FILE:
                    info_is_dir = False
                    state = wait_path
                elif line == STR_DIR_LIST_END:
                    return
            
            elif state == wait_path:
                info_path = line
                state = wait_mtime
            
            elif state == wait_mtime:
                info_mtime = int(line)
                if info_is_dir:
                    state = wait_dir_end
                else:
                    state = wait_size
            
            elif state == wait_size:
                info_size = int(line)
                state = wait_hash
            
            elif state == wait_hash:
                info_hash = line
                state = wait_file_end
            
            elif (state == wait_dir_end) and (line == STR_DIR_END):
                self.dict[info_path] = FileInfo(True)
                self.dict[info_path].mtime =info_mtime
                info_is_dir = False
                state = wait_dir_file
            
            elif (state == wait_file_end) and (line == STR_FILE_END):
                self.dict[info_path] = FileInfo(False)
                self.dict[info_path].mtime =info_mtime
                self.dict[info_path].size = info_size
                self.dict[info_path].hash = info_hash
                state = wait_dir_file
            
            else:
                raise CatalogFormatError()  # CatalogFormatError


# key = hash + u'.' + unicode(size)
# value = arch name
# FileList.dict[key].hashName
class HashList():  # IOError, CatalogFormatError
    def __init__(self):
        self.dict = {}
    
    def save(self, file_object):  # IOError
        # file_object = open('file.name', mode='w', encoding='utf-8')
        file_object.write(STR_HASH_LIST + STR_EOL)
        key_list = list(self.dict.keys())
        key_list.sort()
        for key in key_list:
            file_object.write(STR_HASH + STR_TAB + key + STR_TAB + self.dict[key] + STR_EOL)
        file_object.write(STR_HASH_LIST_END + STR_EOL)
    
    def load(self, file_object):  # IOError, CatalogFormatError
        # file_object = open('file.name', mode='r', encoding='utf-8')
        wait_list = 0
        wait_hash = 1
        self.dict.clear()
        file_object.seek(0, os.SEEK_SET)

        state = wait_list
        for s in file_object:
            line = s.strip()
            if (state == wait_list) and (line == STR_HASH_LIST):
                state = wait_hash
            elif state == wait_hash:
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
    def __init__(self, name, max_part_size, arch_type='tar'):
        self.TarName = name
        self.PartNumber = 0
        self.PartSize = 0
        self.PartFile = None
        self.Closed = True
        self.MaxPartSize = (max_part_size // tarfile.RECORDSIZE) * tarfile.RECORDSIZE
        self.Type = arch_type.lower()
        if arch_type == 'tar':
            self.Ext = STR_TAR_EXT
            self.Mode = 'w:'
        elif arch_type == 'gz':
            self.Ext = STR_GZ_EXT
            self.Mode = 'w:gz'
        elif arch_type == 'bz2':
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
        self.PartNumber += 1
        self.PartFile = tarfile.open(self.TarName + STR_POINT + str(self.PartNumber) + self.Ext, self.Mode)
        self.PartSize = 0
        self.Closed = False
    
    def add(self, file_path, tar_name):  # OSError, IOError, tarfile.TarError
        if self.Closed:
            self.__new_part()
        # prepare file object
        file_size = os.path.getsize(file_path)  # OSError
        file_tar_info = self.PartFile.gettarinfo(file_path)  # tarfile.TarError
        file_tar_info.name = tar_name
        
        with open(file_path, 'rb') as file_object:  # IOError
            # copy file to tar
            while (self.PartSize + file_size + 3*tarfile.BLOCKSIZE) > self.MaxPartSize:
                file_size_to_save = self.MaxPartSize - self.PartSize - 3*tarfile.BLOCKSIZE
                file_tar_info.size = file_size_to_save
                self.PartFile.addfile(file_tar_info, file_object)  # tarfile.TarError
                self.PartSize = self.PartSize + tarfile.BLOCKSIZE + file_size_to_save
                assert (self.PartSize + 2*tarfile.BLOCKSIZE) == self.MaxPartSize
                self.__new_part()
                file_size -= file_size_to_save
                
            file_tar_info.size = file_size
            self.PartFile.addfile(file_tar_info, file_object)  # tarfile.TarError
            # recalculate PartSize
            self.PartSize = self.PartSize + tarfile.BLOCKSIZE + \
                            (file_size // tarfile.BLOCKSIZE) * tarfile.BLOCKSIZE
            if (file_size % tarfile.BLOCKSIZE) > 0:
                self.PartSize += tarfile.BLOCKSIZE
        
        assert (self.PartSize + 2*tarfile.BLOCKSIZE) <= self.MaxPartSize
        
        if (self.PartSize + 3*tarfile.BLOCKSIZE) >= self.MaxPartSize:
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
        self.PartNumber += 1
        self.PartFile = tarfile.open(self.TarName + STR_POINT + str(self.PartNumber) + self.Ext)
    
    def extract(self, tar_name, file_path):  # KeyError, IOError, tarfile.TarError
        self.PartNumber = 0
        
        # ищем первый том в котором есть такой файл
        found = False
        no_file = False
        while not (found or no_file):
            try:
                self.__next_part()
                file_tar_info = self.PartFile.getmember(tar_name)
                found = True
            except IOError:
                no_file = True
            except KeyError:
                pass
        
        if found:
            with open(file_path, 'wb') as file_object:  # IOError
                while found:
                    # копируем в файл
                    tar_buffer = self.PartFile.extractfile(file_tar_info)  # tarfile.TarError
                    file_size = file_tar_info.size
                    while file_size > 0:
                        if file_size > tarfile.BLOCKSIZE:
                            file_size_to_save = tarfile.BLOCKSIZE
                        else:
                            file_size_to_save = file_size
                        file_object.write(tar_buffer.read(tarfile.BLOCKSIZE))  # IOError, tarfile.TarError
                        file_size = file_size - file_size_to_save
                    tar_buffer.close()  # tarfile.TarError
                    # проверяем в следующем томе
                    try:
                        self.__next_part()
                        file_tar_info = self.PartFile.getmember(tar_name)  # tarfile.TarError
                    except IOError:
                        found = False
                    except KeyError:
                        found = False
        else:
            raise KeyError()


def sh_create(sh_args):
    # check source
    if not os.path.isdir(sh_args.source):
        print('ERROR: Source not found!')
        return
    
    # check repository
    if not os.path.isdir(sh_args.repository):
        print('ERROR: Repository not found!')
        return
    
    # check if files with backup name exist
    if os.path.isfile(sh_args.repository + STR_SLASH + sh_args.name + STR_CAT_EXT):
        print('ERROR: Such archive already exists!')
        return
    
    # create sourceFileList
    source_list = FileList()
    try:
        source_list.getDirList(sh_args.source)
    except IOError as e:
        print('ERROR: Can not read: ' + e.filename)
        return
    
    # include / exclude files / dirs
    source_list.includeHierarchy(sh_args.include)
    source_list.exclude(sh_args.exclude)
            
    # create TmpHashList
    hash_list = HashList()
    
    if sh_args.reference is not None:
        # check if reference file exists
        ref_path = sh_args.repository + '/' + sh_args.reference + STR_CAT_EXT
        if not os.path.isfile(ref_path):
            print('ERROR: Reference not found!')
            return
        # load reference_list and hash_list
        reference_list = FileList()
        try:
            file_object = open(ref_path, mode='r', encoding='utf-8')
            reference_list.load(file_object)
            hash_list.load(file_object)
        except IOError:
            print('ERROR: Can not read reference catalogue file!')
            return
        except CatalogFormatError:
            print('ERROR: Reference catalogue is damaged!')
            return
        finally:
            file_object.close()
    
    # compression
    compr = 'tar'
    if sh_args.compression is not None:
        compr = sh_args.compression
    
    # create TarFileWriter
    writer = TarFileWriter(sh_args.repository + STR_SLASH + sh_args.name, sh_args.size, compr)
    # check files and if new/changed add to archive
    c_all = 0
    c_new = 0
    size_all = 0
    size_new = 0
    key_list = list(source_list.dict)
    key_list.sort()
    for file_name in key_list:
        file_path = sh_args.source + file_name
        if not source_list.dict[file_name].isDir:
            ok = False
            while not ok:
                try:
                    # get date and size
                    source_list.dict[file_name].mtime = int(os.path.getmtime(file_path))
                    source_list.dict[file_name].size = os.path.getsize(file_path)
                    # check if such file is in reference
                    if (not sh_args.recalculate) and (sh_args.reference != None) and \
                            (file_name in reference_list.dict) and \
                            (not reference_list.dict[file_name].isDir) and \
                            (source_list.dict[file_name].mtime == reference_list.dict[file_name].mtime) and \
                            (source_list.dict[file_name].size == reference_list.dict[file_name].size):
                        source_list.dict[file_name].hash = reference_list.dict[file_name].hash
                    else:
                        # calculate hash
                        source_list.dict[file_name].hash = calc_hash(file_path)
                        # add file to archive
                        tar_name = hash_name(source_list.dict[file_name])
                        if tar_name not in hash_list.dict:
                            hash_list.dict[tar_name] = sh_args.name
                            writer.add(sh_args.source + file_name, tar_name)
                            c_new += 1
                            size_new = size_new + source_list.dict[file_name].size
                    size_all = size_all + source_list.dict[file_name].size
                    ok = True
                except (OSError, IOError) as e:
                    print('ERROR: Can not read: ' + e.filename)
                    if sh_args.ignore:
                        answer = 'i'
                    else:
                        answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                    if answer == 'c':
                        writer.close()
                        return
                    elif answer == 'i':
                        del source_list.dict[file_name]
                        ok = True
                except tarfile.TarError:
                    print('ERROR: Can not write files to archive!')
                    answer = input('Cancel (c) / Retry (other): ')
                    if answer == 'c':
                        writer.close()
                        return
            c_all += 1
        if not sh_args.quiet:
            sys.stdout.write("\rFiles (New/All): %s / %s, Size (New/All): %.02f Mb / %.02f Mb" % (
                            c_new, c_all, size_new/1024.0/1024.0, size_all/1024.0/1024.0))
            sys.stdout.flush()
    
    # close TarFileWriter
    writer.close()
    
    if not sh_args.quiet:
        sys.stdout.write(STR_EOL)
        sys.stdout.flush()
    
    # save catalogue
    try:                  
        file_object = open(sh_args.repository + STR_SLASH + sh_args.name + STR_CAT_EXT,
                            mode='w', encoding='utf-8')
        source_list.save(file_object)
        hash_list.save(file_object)
    except IOError:
        print('ERROR: Can not create catalogue file!')
        return
    finally:
        file_object.close()


def sh_find(sh_args):
    # check repository
    if not os.path.isdir(sh_args.repository):
        print('ERROR: Repository not found!\n')
        return
    
    # get file list
    cat_list = os.listdir(sh_args.repository)
    cat_list.sort()
    key_list = list(cat_list)
    for key in key_list:
        if not fnmatch.fnmatch(key, sh_args.name + STR_CAT_EXT):
            del cat_list[cat_list.index(key)]
    
    # check if something found
    if len(cat_list) == 0:
        print('ERROR: No catalogue found!\n')
        return
    
    # looking for patterns in all catalogues
    for cat in cat_list:
        # loading catalogue
        file_list = FileList()
        try:
            file_object = open(sh_args.repository + STR_SLASH + cat, mode='r', encoding='utf-8')
            file_list.load(file_object)
        except IOError:
            print('ERROR: Can not read  catalogue file: ' + cat)
            return
        except CatalogFormatError:
            print('ERROR: Catalogue is damaged: ' + cat)
            return
        finally:
            file_object.close()
        
        # include / exclude files / dirs
        file_list.include(sh_args.include)
        file_list.exclude(sh_args.exclude)
        
        # looking for matching files and dirs
        key_list = list(file_list.dict.keys())
        key_list.sort()
        for key in key_list:
            print(cat + ': ' + key)


def sh_restore(sh_args):
    # check repository
    if not os.path.isdir(sh_args.repository):
        print('ERROR: Repository not found!\n')
        return
    
    # check existence of catalogue file
    if not os.path.isfile(sh_args.repository + STR_SLASH + sh_args.name + STR_CAT_EXT):
        print('ERROR: Catalogue not found!\n')
        return
    
    # check destination existence
    if not os.path.isdir(sh_args.destination):
        print('ERROR: Destination not found!\n')
        return
    
    # read FileList and HashList from catalogue
    source_list = FileList()
    hash_list = HashList()
    try:
        file_object = open(sh_args.repository + STR_SLASH + sh_args.name + STR_CAT_EXT,
                            mode='r', encoding='utf-8')
        source_list.load(file_object)
        hash_list.load(file_object)
    except IOError:
        print('ERROR: Can not read catalogue file!')
        return
    except CatalogFormatError:
        print('ERROR: Catalogue is damaged!')
        return
    finally:
        file_object.close()
    
    # include / exclude files / dirs
    source_list.fixHierarchy()
    source_list.includeHierarchy(sh_args.include)
    source_list.exclude(sh_args.exclude)
    
    # create not existing dirs and extract new or changed files
    c_all = 0
    c_new = 0
    size_all = 0
    size_new = 0
    key_list = list(source_list.dict)
    key_list.sort()
    for file_name in key_list:
        file_path = sh_args.destination + file_name
        # make directory
        if source_list.dict[file_name].isDir:
            file_dir = file_path
        else:
            (file_dir, stub) = os.path.split(file_path)
        ok = False
        while not ok:
            try:
                if os.path.isfile(file_dir):
                    os.remove(file_dir)
                if not os.path.isdir(file_dir):
                    os.makedirs(file_dir)
                ok = True
            except OSError as e:
                print('ERROR: Can not create directory: ' + e.filename)
                if sh_args.ignore:
                    answer = 'i'
                else:
                    answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                if answer == 'c':
                    return
                elif answer == 'i':
                    ok = True
        # restore file
        if not source_list.dict[file_name].isDir:
            hash_key = hash_name(source_list.dict[file_name])
            backup_file = hash_list.dict[hash_key]
            ok = False
            while not ok:
                try:
                    # check if such file exists
                    reader = TarFileReader(sh_args.repository + STR_SLASH + backup_file)
                    if os.path.isfile(file_path) and \
                            (source_list.dict[file_name].mtime == int(os.path.getmtime(file_path))) and \
                            (source_list.dict[file_name].size == os.path.getsize(file_path)) and \
                            (source_list.dict[file_name].hash == calc_hash(file_path)):
                        pass
                    else:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        reader.extract(hash_key, file_path)
                        c_new += 1
                        size_new = size_new + source_list.dict[file_name].size
                    ok = True
                except (OSError, IOError) as e:
                    print('ERROR: Can not restore file: ' + e.filename)
                    if sh_args.ignore:
                        answer = 'i'
                    else:
                        answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                    if answer == 'c':
                        return
                    elif answer == 'i':
                        ok = True
                finally:
                    reader.close()
            c_all += 1
            size_all = size_all + source_list.dict[file_name].size
        # set time
        ok = False
        while not ok:
            try:
                os.utime(file_path, (source_list.dict[file_name].mtime,
                        source_list.dict[file_name].mtime))
                ok = True
            except OSError as e:
                print('ERROR: Can not update time for: ' + e.filename)
                if sh_args.ignore:
                    answer = 'i'
                else:
                    answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                if answer == 'c':
                    return
                elif answer == 'i':
                    ok = True
        sys.stdout.write("\rFiles (New/All): %s / %s, Size (New/All): %.02f Mb / %.02f Mb" % (
                        c_new, c_all, size_new/1024.0/1024.0, size_all/1024.0/1024.0))
        sys.stdout.flush()
    
    sys.stdout.write(STR_EOL)
    sys.stdout.flush()
    
    # get FileList for destination
    if sh_args.delete:
        destination_list = FileList()
        destination_list.getDirList(sh_args.destination)
        # remove old files
        key_list = list(destination_list.dict.keys())
        key_list.sort()
        for file_name in key_list:
            file_path = sh_args.destination + file_name
            if (not destination_list.dict[file_name].isDir) and \
                    (file_name not in source_list.dict):
                ok = False
                while not ok:
                    try:
                        os.remove(file_path)
                        ok = True
                    except OSError as e:
                        print('ERROR: Can not delete file: ' + e.filename)
                        if sh_args.ignore:
                            answer = 'i'
                        else:
                            answer = input('Cancel (c) / Ignore (i) / Retry (other): ')
                        if answer == 'c':
                            return
                        elif answer == 'i':
                            ok = True
        # remove old dirs
        key_list = list(destination_list.dict.keys())
        key_list.sort()
        for file_name in key_list:
            file_path = sh_args.destination + file_name
            if destination_list.dict[file_name].isDir and \
                    (file_name not in source_list.dict):
                ok = False
                while not ok:
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        ok = True
                    except OSError as e:
                        print('ERROR: Can not delete directory: ' + e.filename)
                        if sh_args.ignore:
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

parser_create = subparsers.add_parser('create')  #
parser_create.add_argument('source', help='Directory tree that will be backed up.')  # dir
parser_create.add_argument('repository', help='Directory in which backup will be stored.')  # dir
parser_create.add_argument('name', help='Basename for backup.')  # name
parser_create.add_argument('-r', '--reference',
                           help='Reference basename for differential backup. '
                                'Reference catalog should be stored in the same repository.')  # path
parser_create.add_argument('-s', '--size', type=int, default=1024*1024*1020, help='Size of one slice.')
parser_create.add_argument('-i', '--include', nargs='*',
                           help='Mask list. Files/Dirs matching at least one mask will be included in backup. '
                                'If no mask specified all Files/Dirs will be included.')
parser_create.add_argument('-e', '--exclude', nargs='*',
                           help='Mask list. Files/Dirs matching at least one mask will be excluded from backup.')
parser_create.add_argument('-q', '--quiet', action='store_true',
                           help='Nothing is displayed if operation succeeds.')  # !!!
parser_create.add_argument('-g', '--ignore', action='store_true', help='Ignore all errors.')
parser_create.add_argument('-c', '--compression', help="'tar'-default, 'gz' or 'bz2'")
parser_create.add_argument('-a', '--recalculate', action='store_true',
                           help="Recalculate all hashes again. Don't use hashes from reference.")
parser_create.set_defaults(func=sh_create)

parser_find = subparsers.add_parser('find')  # simple regular expressions
parser_find.add_argument('repository', help='Directory in which backup is stored.')  # dir
parser_find.add_argument('name', help='Mask for backup basename. '
                                      'Several backups can be looked thorough.')  # name pattern (without ext)
parser_find.add_argument('-i', '--include', nargs='*',
                         help='Mask list. Files/Dirs matching at least one mask will be shown. '
                              'If no mask specified all Files/Dirs will be shown.')
parser_find.add_argument('-e', '--exclude', nargs='*',
                         help='Mask list. Files/Dirs matching at least one mask will not be shown.')
parser_find.set_defaults(func=sh_find)

parser_restore = subparsers.add_parser('restore')  # restore backup
parser_restore.add_argument('repository', help='Directory in which backup is stored.')  # dir
parser_restore.add_argument('name', help='Basename for backup to be restored.')  # name
parser_restore.add_argument('destination', help='Directory which will be restored.')  # dir
parser_restore.add_argument('-i', '--include', nargs='*',
                            help='Mask list. Files/Dirs matching at least one mask will be restored. '
                                 'If no mask specified all Files/Dirs will be restored.')
parser_restore.add_argument('-e', '--exclude', nargs='*',
                            help='Mask list. Files/Dirs matching at least one mask will not be restored.')
parser_restore.add_argument('-d', '--delete', action='store_true',
                            help='Delete Files/Dirs not existing in backup.')
parser_restore.add_argument('-g', '--ignore', action='store_true', help='Ignore all errors.')
parser_restore.set_defaults(func=sh_restore)

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
