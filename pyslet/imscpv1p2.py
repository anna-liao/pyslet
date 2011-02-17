#! /usr/bin/env python
"""This module implements the IMS CP 1.2 specification defined by IMS GLC
"""

import pyslet.xmlnames20091208 as xmlns

from types import StringTypes
from tempfile import mkdtemp
import os, os.path, urlparse, urllib, shutil
import zipfile
import re, random

IMSCP_NAMESPACE="http://www.imsglobal.org/xsd/imscp_v1p1"
IMSCPX_NAMESPACE="http://www.imsglobal.org/xsd/imscp_extensionv1p2"

cp_dependency=(IMSCP_NAMESPACE,'dependency')
cp_file=(IMSCP_NAMESPACE,'file')
cp_manifest=(IMSCP_NAMESPACE,'manifest')
cp_metadata=(IMSCP_NAMESPACE,'metadata')
cp_organization=(IMSCP_NAMESPACE,'organization')
cp_organizations=(IMSCP_NAMESPACE,'organizations')
cp_resource=(IMSCP_NAMESPACE,'resource')
cp_resources=(IMSCP_NAMESPACE,'resources')

cp_identifier="identifier"
cp_identifierref="identifierref"
cp_href="href"
cp_type="type"

IGNOREFILES_RE="\\..*"

class CPException(Exception): pass
class CPFilePathError(Exception): pass
class CPFileTypeError(Exception): pass
class CPManifestError(CPException): pass
class CPProtocolError(CPException): pass
class CPValidationError(CPException): pass
class CPZIPBeenThereError(Exception): pass
class CPZIPDirectorySizeError(CPException): pass
class CPZIPDuplicateFileError(CPException): pass
class CPZIPFilenameError(CPException): pass

class CPElement(xmlns.XMLNSElement):
	"""Basic element to represent all CP elements"""
	pass


def PathInPath(childPath, parentPath):
	"""Returns childPath expressed relative to parentPath
	
	Both paths are normalized to remove any navigational segments, the resulting
	path will not contain these either.

	If childPath is not contained in parentPath then None is returned.

	If childPath and parentPath are equal an empty string is returned."""
	relPath=[]
	childPath=os.path.normpath(childPath)
	parentPath=os.path.normpath(parentPath)
	while os.path.normcase(childPath)!=os.path.normcase(parentPath):
		childPath,tail=os.path.split(childPath)
		if not childPath or not tail:
			# We've gone as far as we can, fail!
			return None
		relPath[0:0]=[tail]
	if relPath:
		return os.path.join(*relPath)
	else:
		return ''
	
class CPManifest(CPElement):
	ID=cp_identifier
	XMLNAME=cp_manifest
	
	def __init__(self,parent):
		CPElement.__init__(self,parent)
		self.metadata=None
		self.organizations=CPOrganizations(self)
		self.resources=CPResources(self)
		self.childManifests=[]
		self.extensions=[]
		
	def GetIdentifier(self):
		return self.attrs.get(cp_identifier,None)
		
	def SetIdentifier(self,identifier):
		CPElement.SetAttribute(self,cp_identifier,identifier)
		
	def GetMetadata(self):
		return None
		
	def AddChild(self,child):
		if isinstance(child,CPMetadata):
			self.metadata=child
		elif isinstance(child,CPOrganizations):
			self.organizations=child
		elif isinstance(child,CPResources):
			self.resources=child
		elif isinstance(child,CPManifest):
			self.childManifests,append(child)
		elif self.CheckOther(child,IMSCP_NAMESPACE):
			self.extensions.append(child)
		else:
			self.ValidationError(self,child)

	def GetChildren(self):
		children=[]
		if self.metadata:
			children.append(self.metadata)
		children.append(self.organizations)
		children.append(self.resources)
		return tuple(children+self.childManifests+self.extensions)
		

class CPMetadata(CPElement):
	XMLNAME=cp_metadata
	

class CPOrganizations(CPElement):
	XMLNAME=cp_organizations
	
	def __init__(self,parent):
		CPElement.__init__(self,parent)
		self.list=[]
		
	def AddChild(self,child):
		if isinstance(child,CPOrganization):
			self.list.append(child)
		CPElement.AddChild(self,child)


class CPOrganization(CPElement):
	XMLNAME=cp_organization
			

class CPResources(CPElement):
	XMLNAME=cp_resources

	def __init__(self,parent):
		CPElement.__init__(self,parent)
		self.list=[]
		self.extensions=[]
		
	def AddChild(self,child):
		if isinstance(child,CPResource):
			self.list.append(child)
		elif self.CheckOther(child,IMSCP_NAMESPACE):
			self.extensions.append(child)
		else:
			self.ValidationError(self,child)

	def GetChildren(self):
		return tuple(self.list+self.extensions)
		
	def CPResource(self,identifier,type):
		r=CPResource(self)
		r.SetIdentifier(identifier)
		r.SetType(type)
		self.AddChild(r)
		return r


class CPResource(CPElement):
	XMLNAME=cp_resource
	ID=cp_identifier

	def __init__(self,parent):
		CPElement.__init__(self,parent)
		self.metadata=None
		self.fileList=[]
		self.dependencies=[]
		self.extensions=[]
		
	def GetIdentifier(self):
		return self.attrs.get(cp_identifier,None)
		
	def SetIdentifier(self,identifier):
		CPElement.SetAttribute(self,cp_identifier,identifier)
		
	def GetType(self):
		return self.attrs.get(cp_type,None)
		
	def SetType(self,type):
		CPElement.SetAttribute(self,cp_type,type)
		
	def GetHREF(self):
		return self.attrs.get(cp_href,None)
		
	def SetHREF(self,href):
		CPElement.SetAttribute(self,cp_href,href)
	
	def GetEntryPoint(self):
		"""Returns the CPFile object that is identified as the entry point.
		
		If there is no entry point, or no CPFile object with a matching
		href, then None is returned."""
		href=self.GetHREF()
		if href:
			href=self.ResolveURI(href)
			for f in self.fileList:
				fHREF=f.GetHREF()
				if fHREF:
					fHREF=f.ResolveURI(fHREF)
					if href==fHREF:
						return f
		return None

	def SetEntryPoint(self,f):
		"""Set's the CPFile object that is identified as the entry point.
		
		The CPFile must already exist and be associated with the resource."""
		# We resolve and recalculate just in case xml:base lurks on this file
		href=self.RelativeURI(f.ResolveURI(f.GetHREF()))
		self.SetHREF(href)
		
	def CPFile(self,href):
		child=CPFile(self)
		child.SetHREF(href)
		self.fileList.append(child)
		CPElement.AddChild(self,child)
		return child
	
	def DeleteFile(self,f):
		index=self.fileList.index(f)
		del self.fileList[index]
		
	def CPDependency(self,identifierref):
		child=CPDependency(self)
		child.SetIdentifierRef(identifierref)
		self.dependencies.append(child)
		CPElement.AddChild(self,child)
		
	def DeleteDependency(self,d):
		index=self.dependencies.index(d)
		del self.dependencies[index]
		
	def AddChild(self,child):
		if isinstance(child,CPMetadata):
			self.metadata=child
		elif isinstance(child,CPFile):
			self.fileList.append(child)
		elif isinstance(child,CPDependency):
			self.dependencies.append(child)
		elif self.CheckOther(child,IMSCP_NAMESPACE):
			self.extensions.append(child)
		else:
			self.ValidationError(self,child)

	def GetChildren(self):
		children=[]
		if self.metadata:
			children.append(self.metadata)
		return tuple(children+self.fileList+self.dependencies+self.extensions)
		

class CPDependency(CPElement):
	XMLNAME=cp_dependency

	def GetIdentifierRef(self):
		return self.attrs.get(cp_identifierref,None)
		
	def SetIdentifierRef(self,identifierref):
		CPElement.SetAttribute(self,cp_identifierref,identifierref)

			
class CPFile(CPElement):
	XMLNAME=cp_file
	
	def GetHREF(self):
		return self.attrs.get(cp_href,None)
		
	def SetHREF(self,href):
		CPElement.SetAttribute(self,cp_href,href)
				
	def PackagePath(self,cp):
		"""Returns the normalized file path relative to the root of the content
		package.

		If the HREF does not point to a local file then None is returned. 
		Otherwise, this function calculates an absolute path to the file and
		then calls the content package's PackagePath method."""
		url=urlparse.urlsplit(self.ResolveURI(self.GetHREF()))
		if not(url.scheme=='file' and url.netloc==''):
			return None
		return cp.PackagePath(urllib.url2pathname(url.path))

	
class CPDocument(xmlns.XMLNSDocument):
	def __init__(self,**args):
		""""""
		xmlns.XMLNSDocument.__init__(self,**args)
		self.defaultNS=IMSCP_NAMESPACE

	def GetElementClass(self,name):
		return CPDocument.classMap.get(name,CPDocument.classMap.get((name[0],None),xmlns.XMLNSElement))

	classMap={
		cp_dependency:CPDependency,
		cp_file:CPFile,
		cp_manifest:CPManifest,
		cp_organizations:CPOrganizations,
		cp_organization:CPOrganization,
		cp_resources:CPResources,
		cp_resource:CPResource
		}


class ContentPackage:
	def __init__(self,dPath=None):
		self.tempDir=False
		errorFlag=True
		try:
			if dPath is None:
				self.dPath=mkdtemp('.d','imscpv1p2-')
				self.tempDir=True
				self.packageName='imscp'
			else:
				self.dPath=os.path.abspath(dPath)
				head,tail=os.path.split(self.dPath)
				self.packageName=tail
				if os.path.isdir(self.dPath):
					# existing directory
					pass
				elif os.path.exists(self.dPath):
					# is this a zip archive?
					if zipfile.is_zipfile(self.dPath):					
						name,ext=os.path.splitext(tail)
						if ext.lower()==".zip":
							self.packageName=name
						self.ExpandZip(self.dPath)
					else:
						# anything else must be a manifest file
						self.dPath=head;mPath=tail
						head,tail=os.path.split(self.dPath)
						if os.path.normcase(mPath)!='imsmanifest.xml':
							raise CPManifestError("%s must be named imsmanifest.xml"%mPath)
						self.packageName=tail
				else:
					os.mkdir(self.dPath)
			mPath=os.path.join(self.dPath,'imsmanifest.xml')
			if os.path.exists(mPath):
				self.manifest=CPDocument(baseURI=urllib.pathname2url(mPath))
				self.manifest.Read()
				if not isinstance(self.manifest.rootElement,CPManifest):
					raise CPManifestError("%s not a manifest file, found %s::%s "%
						(mPath,self.manifest.rootElement.ns,self.manifest.rootElement.xmlname))
			else:
				self.manifest=CPDocument(root=CPManifest, baseURI=urllib.pathname2url(mPath))
				self.manifest.rootElement.SetIdentifier(self.manifest.GetUniqueID('manifest'))
				self.manifest.Create()
			self.SetIgnoreFiles(IGNOREFILES_RE)
			self.RebuildFileTable()
			errorFlag=False
		finally:
			if errorFlag:
				self.Close()
	
	def SetIgnoreFiles(self,ignoreFiles):
		self.ignoreFiles=re.compile(ignoreFiles)
	
	def IgnoreFile(self,f):
		match=self.ignoreFiles.match(f)
		if match:
			return len(f)==match.end()
		else:
			return False
		
	def RebuildFileTable(self):
		self.fileTable={}
		beenThere={}
		for f in os.listdir(self.dPath):
			if self.IgnoreFile(f):
				continue
			if os.path.normcase(f)=='imsmanifest.xml':
				continue
			self.FileScanner(f,beenThere)
		# Now scan the manifest and identify which file objects refer to which files
		for r in self.manifest.rootElement.resources.list:
			for f in r.fileList:
				fPath=f.PackagePath(self)
				if fPath is None:
					continue
				if self.fileTable.has_key(fPath):
					self.fileTable[fPath].append(f)
				else:
					self.fileTable[fPath]=[f]
					
	def FileScanner(self,fPath,beenThere):
		fullPath=os.path.join(self.dPath,fPath)
		rFullPath=os.path.realpath(fullPath)
		if beenThere.has_key(rFullPath):
			raise CPPackageBeenThereError(rFullPath)
		beenThere[rFullPath]=True
		if os.path.isdir(fullPath):
			for f in os.listdir(fullPath):
				if self.IgnoreFile(f):
					continue
				self.FileScanner(os.path.join(fPath,f),beenThere)
		elif os.path.isfile(fullPath):
			self.fileTable[os.path.normcase(fPath)]=[]
		else: # skip non-regular files.
			pass
	
	def PackagePath(self,fPath):
		"""Converts an absolute file path into a canonical package-relative path
		
		Returns None if fPath is not inside the package."""
		relPath=[]
		while fPath!=self.dPath:
			fPath,tail=os.path.split(fPath)
			if not fPath or not tail:
				# We've gone as far as we can, fail!
				return None
			relPath[0:0]=[tail]
		return os.path.normcase(os.path.join(*relPath))
		
	def ExpandZip(self,zPath):
		self.dPath=mkdtemp('.d','imscpv1p2-')
		self.tempDir=True
		zf=zipfile.ZipFile(zPath)
		try:
			for zfi in zf.infolist():
				path=self.dPath
				for pathSeg in zfi.filename.split('/'):
					# The current path will need to be a directory
					if not os.path.isdir(path):
						os.mkdir(path)
					path=os.path.normpath(os.path.join(path,pathSeg))
					if self.PackagePath(path) is None:
						raise CPZIPFilenameError(zfi.filename)
				if os.path.isdir(path):
					if zfi.file_size>0:
						raise CPZIPDirectorySizeError("%s has size %i"%(zfi.filename,zfi.file_size))
				elif os.path.exists(path):
					# Duplicate entries in the zip file
					raise CPZIPDuplicateFileError(zfi.filename)
				else:
					f=open(path,'wb')
					f.write(zf.read(zfi.filename))
					f.close()
		finally:
			zf.close()
	
	def ExportToPIF(self,zPath):
		zf=zipfile.ZipFile(zPath,'w')
		base=''
		beenThere={}
		try:
			for f in os.listdir(self.dPath):
				if self.IgnoreFile(f):
					continue
				self.AddToZip(os.path.join(self.dPath,f),zf,base,beenThere)
		finally:
			zf.close()
		
	def AddToZip(self,fPath,zf,zbase,beenThere):
		rfName=os.path.realpath(fPath)
		if beenThere.has_key(rfName):
			raise CPZIPBeenThereError(fPath)
		beenThere[rfName]=True
		fName=os.path.split(fPath)[1]
		zpath=zbase+fName.replace('/',':')
		if os.path.isdir(fPath):
			zpath+='/'
			zf.writestr(zpath,'')
			for f in os.listdir(fPath):
				if self.IgnoreFile(f):
					continue
				self.AddToZip(os.path.join(fPath,f),zf,zpath,beenThere)
		elif os.path.isfile(fPath):
			zf.write(fPath,zpath)
		else: # skip non-regular files.
			pass
	
	def GetUniqueFile(self,suggestedPath):
		"""Returns a unique file path suitable for creating a new file in the package.
		
		suggestedPath is used to provide a suggested path for the file.  This
		may be relative (to the root and manifest) or absolute but it must
		resolve to an file (potentially) in the package.

		The return result is always normalized and returned relative to the
		package root.
		"""
		fPath=os.path.join(self.dPath,suggestedPath)
		fPath=PathInPath(fPath,self.dPath)
		if fPath is None:
			raise CPFilePathError(suggestedPath)
		fPath=os.path.normcase(fPath)
		# Now we can try and make it unique
		pathStr=fPath
		pathExtra=0
		while self.fileTable.has_key(pathStr):
			if not pathExtra:
				pathExtra=random.randint(0,0xFFFF)
			fName,fExt=os.path.splitext(fPath)
			pathStr='%s_%X%s'%(fName,pathExtra,fExt)
			pathExtra=pathExtra+1
		# we have the path string
		return pathStr
	
	def CPFile(self,resource,href):
		"""Creates a new CPFile attached to a resource, pointing to href

		href is expressed relative to resource, e.g., using
		resource.RelativeURI"""
		fURL=resource.ResolveURI(href)
		url=urlparse.urlsplit(fURL)
		if not(url.scheme=='file' and url.netloc==''):
			# Not a local file
			return resource.CPFile(href)
		fullPath=urllib.url2pathname(url.path)
		head,tail=os.path.split(fullPath)
		if self.IgnoreFile(tail):
			raise CPFilePathError(url.path)
		relPath=PathInPath(fullPath,self.dPath)
		if relPath is None or relPath.lower=='imsmanifest.xml':
			raise CPFilePathError(url.path)
		# normalise the case ready to put in the file table
		relPath=os.path.normcase(relPath)
		f=resource.CPFile(href)
		if not self.fileTable.has_key(relPath):
			self.fileTable[relPath]=[f]
		else:
			self.fileTable[relPath].append(f)
		return f
		
	def DeleteFile(self,href):
		"""Removes the file at href from the file system
		
		This method also removes any file references to it from resources in the
		manifest. href is given relative to the package root (i.e., ignoring any
		xml:base overrides in the manifest element).  File references are only
		removed if they point to the same file after any xml:base references
		have been taken into account of course.
		
		CPFileTypeError is raised if the file is not a regular file

		CPFilePathError is raised if the file is an IgnoreFile, the manifest
		itself or outside of the content package.

		CPProtocolError is raised if the content package is not in the local
		file system."""
		baser=self
		baseURI=self.manifest.GetBase()
		fURL=urlparse.urljoin(baseURI,str(href))
		url=urlparse.urlsplit(fURL)
		if not(url.scheme=='file' and url.netloc==''):
			# We cannot delete objects that are not local (though in future
			# we should support HTTP DELETE)
			return CPProtocolError(fURL)
		fullPath=urllib.url2pathname(url.path)
		if not os.path.isfile(fullPath):
			raise CPFileTypeError(url.path)
		head,tail=os.path.split(fullPath)
		if self.IgnoreFile(tail):
			raise CPFilePathError(url.path)
		relPath=PathInPath(fullPath,self.dPath)
		if relPath is None or relPath.lower=='imsmanifest.xml':
			raise CPFilePathError(url.path)
		# normalise the case ready for comparisons
		relPath=os.path.normcase(relPath)
		for r in self.manifest.rootElement.resources.list:
			delList=[]
			for f in r.fileList:
				# Does f point to the same file?
				if f.PackagePath(self)==relPath:
					delList.append(f)
			for f in delList:
				r.DeleteFile(f)
		# Now there are no more references, safe to remove the file itself
		os.remove(fullPath)
		if self.fileTable.has_key(relPath):
			del self.fileTable[relPath]
		
	def GetPackageName(self):
		"""Returns a name for the package

		The name is determined by the method used to create the CPPackage object.
		The purpose is to return a name that would be intuitive to the user if it
		were to be used as the name of the package directory or the stem of a file
		name when exporting to a PIF file.
		
		Note that the name is returned as a unicode string suitable for showing to
		the user and may need to be encoded before being used in file path operations."""
		return unicode(self.packageName,'utf-8')
		
	def Close(self):
		self.manifest=None
		self.fileTable={}
		if self.tempDir:
			shutil.rmtree(self.dPath,True)
			self.dPath=None
