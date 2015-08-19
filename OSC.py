'''

Adapted from pyOSC: https://trac.v2.nl/wiki/pyOSC
Bypasses all unneeded functionality (client, bundling, etc.)

'''

import math, re, socket, select, string, struct, sys, threading, time, types
from SocketServer import UDPServer, DatagramRequestHandler, ForkingMixIn, ThreadingMixIn

global version
version = ("0.3","5b", "$Rev: 5294 $"[6:-2])

global FloatTypes
FloatTypes = [types.FloatType]

global IntTypes
IntTypes = [types.IntType]

##
# numpy/scipy support:
##

try:
	from numpy import typeDict

	for ftype in ['float32', 'float64', 'float128']:
		try:
			FloatTypes.append(typeDict[ftype])
		except KeyError:
			pass
		
	for itype in ['int8', 'int16', 'int32', 'int64']:
		try:
			IntTypes.append(typeDict[itype])
			IntTypes.append(typeDict['u' + itype])
		except KeyError:
			pass
		
	# thanks for those...
	del typeDict, ftype, itype
	
except ImportError:
	pass

######
#
# OSCMessage classes
#
######

class OSCMessage(object):
	
	def __init__(self, address=""):
		"""Instantiate a new OSCMessage.
		The OSC-address can be specified with the 'address' argument
		"""
		self.clear(address)

	def setAddress(self, address):
		"""Set or change the OSC-address
		"""
		self.address = address

	def clear(self, address=""):
		"""Clear (or set a new) OSC-address and clear any arguments appended so far
		"""
		self.address  = address
		self.clearData()

	def clearData(self):
		"""Clear any arguments appended so far
		"""
		self.typetags = ","
		self.message  = ""

	def append(self, argument, typehint=None):
		"""Appends data to the message, updating the typetags based on
		the argument's type. If the argument is a blob (counted
		string) pass in 'b' as typehint.
		'argument' may also be a list or tuple, in which case its elements
		will get appended one-by-one, all using the provided typehint
		"""
		if type(argument) == types.DictType:
			argument = argument.items()
		elif isinstance(argument, OSCMessage):
			raise TypeError("Can only append 'OSCMessage' to 'OSCBundle'")
		
		if hasattr(argument, '__iter__'):
			for arg in argument:
				self.append(arg, typehint)
			
			return
		
		if typehint == 'b':
			binary = OSCBlob(argument)
			tag = 'b'
		elif typehint == 't':
			binary = OSCTimeTag(argument)
			tag = 't'
		else:
			tag, binary = OSCArgument(argument, typehint)

		self.typetags += tag
		self.message += binary
		
	def getBinary(self):
		"""Returns the binary representation of the message
		"""
		binary = OSCString(self.address)
		binary += OSCString(self.typetags)
		binary += self.message
		
		return binary

	def __repr__(self):
		"""Returns a string containing the decode Message
		"""
		return str(decodeOSC(self.getBinary()))

	def __str__(self):
		"""Returns the Message's address and contents as a string.
		"""
		return "%s %s" % (self.address, str(self.values()))
	
	def __len__(self):
		"""Returns the number of arguments appended so far
		"""
		return (len(self.typetags) - 1)
	
	def __eq__(self, other):
		"""Return True if two OSCMessages have the same address & content
		"""
		if not isinstance(other, self.__class__):
			return False
		
		return (self.address == other.address) and (self.typetags == other.typetags) and (self.message == other.message)
	
	def __ne__(self, other):
		"""Return (not self.__eq__(other))
		"""
		return not self.__eq__(other)
	
	def __add__(self, values):
		"""Returns a copy of self, with the contents of 'values' appended
		(see the 'extend()' method, below)
		"""
		msg = self.copy()
		msg.extend(values)
		return msg
	
	def __iadd__(self, values):
		"""Appends the contents of 'values'
		(equivalent to 'extend()', below)
		Returns self
		"""
		self.extend(values)
		return self
	
	def __radd__(self, values):
		"""Appends the contents of this OSCMessage to 'values'
		Returns the extended 'values' (list or tuple)
		"""
		out = list(values)
		out.extend(self.values())
		
		if type(values) == types.TupleType:
			return tuple(out)
		
		return out
	
	def _reencode(self, items):
		"""Erase & rebuild the OSCMessage contents from the given
		list of (typehint, value) tuples"""
		self.clearData()
		for item in items:
			self.append(item[1], item[0])
		
	def values(self):
		"""Returns a list of the arguments appended so far
		"""
		return decodeOSC(self.getBinary())[2:]
	
	def tags(self):
		"""Returns a list of typetags of the appended arguments
		"""
		return list(self.typetags.lstrip(','))
	
	def items(self):
		"""Returns a list of (typetag, value) tuples for 
		the arguments appended so far
		"""
		out = []
		values = self.values()
		typetags = self.tags()
		for i in range(len(values)):
			out.append((typetags[i], values[i]))
			
		return out

	def __contains__(self, val):
		"""Test if the given value appears in the OSCMessage's arguments
		"""
		return (val in self.values())

	def __getitem__(self, i):
		"""Returns the indicated argument (or slice)
		"""
		return self.values()[i]

	def __delitem__(self, i):
		"""Removes the indicated argument (or slice)
		"""
		items = self.items()
		del items[i]
			
		self._reencode(items)
	
	def _buildItemList(self, values, typehint=None):
		if isinstance(values, OSCMessage):
			items = values.items()
		elif type(values) == types.ListType:
			items = []
			for val in values:
				if type(val) == types.TupleType:
					items.append(val[:2])
				else:
					items.append((typehint, val))
		elif type(values) == types.TupleType:
			items = [values[:2]]
		else:		
			items = [(typehint, values)]
			
		return items
	
	def __setitem__(self, i, val):
		"""Set indicatated argument (or slice) to a new value.
		'val' can be a single int/float/string, or a (typehint, value) tuple.
		Or, if 'i' is a slice, a list of these or another OSCMessage.
		"""
		items = self.items()
		
		new_items = self._buildItemList(val)
		
		if type(i) != types.SliceType:
			if len(new_items) != 1:
				raise TypeError("single-item assignment expects a single value or a (typetag, value) tuple")
			
			new_items = new_items[0]
			
		# finally...
		items[i] = new_items
		
		self._reencode(items)
	
	def setItem(self, i, val, typehint=None):
		"""Set indicated argument to a new value (with typehint)
		"""
		items = self.items()
		
		items[i] = (typehint, val)
			
		self._reencode(items)
		
	def copy(self):
		"""Returns a deep copy of this OSCMessage
		"""
		msg = self.__class__(self.address)
		msg.typetags = self.typetags
		msg.message = self.message
		return msg
	
	def count(self, val):
		"""Returns the number of times the given value occurs in the OSCMessage's arguments
		"""
		return self.values().count(val)
	
	def index(self, val):
		"""Returns the index of the first occurence of the given value in the OSCMessage's arguments.
		Raises ValueError if val isn't found
		"""
		return self.values().index(val)
	
	def extend(self, values):
		"""Append the contents of 'values' to this OSCMessage.
		'values' can be another OSCMessage, or a list/tuple of ints/floats/strings
		"""
		items = self.items() + self._buildItemList(values)
		
		self._reencode(items)
		
	def insert(self, i, val, typehint = None):
		"""Insert given value (with optional typehint) into the OSCMessage
		at the given index.
		"""
		items = self.items()
		
		for item in reversed(self._buildItemList(val)):
			items.insert(i, item)
			
		self._reencode(items)
		
	def popitem(self, i):
		"""Delete the indicated argument from the OSCMessage, and return it
		as a (typetag, value) tuple.
		"""
		items = self.items()
		
		item = items.pop(i)
		
		self._reencode(items)
		
		return item
	
	def pop(self, i):
		"""Delete the indicated argument from the OSCMessage, and return it.
		"""
		return self.popitem(i)[1]
		
	def reverse(self):
		"""Reverses the arguments of the OSCMessage (in place)
		"""
		items = self.items()
		
		items.reverse()
		
		self._reencode(items)
		
	def remove(self, val):
		"""Removes the first argument with the given value from the OSCMessage.
		Raises ValueError if val isn't found.
		"""
		items = self.items()
		
		# this is not very efficient...
		i = 0
		for (t, v) in items:
			if (v == val):
				break
			i += 1
		else:
			raise ValueError("'%s' not in OSCMessage" % str(m))
		# but more efficient than first calling self.values().index(val),
		# then calling self.items(), which would in turn call self.values() again...
		
		del items[i]
		
		self._reencode(items)
		
	def __iter__(self):
		"""Returns an iterator of the OSCMessage's arguments
		"""
		return iter(self.values())

	def __reversed__(self):
		"""Returns a reverse iterator of the OSCMessage's arguments
		"""
		return reversed(self.values())

	def itervalues(self):
		"""Returns an iterator of the OSCMessage's arguments
		"""
		return iter(self.values())

	def iteritems(self):
		"""Returns an iterator of the OSCMessage's arguments as
		(typetag, value) tuples
		"""
		return iter(self.items())

	def itertags(self):
		"""Returns an iterator of the OSCMessage's arguments' typetags
		"""
		return iter(self.tags())

######
#
# OSCMessage encoding functions
#
######

def OSCString(next):
	"""Convert a string into a zero-padded OSC String.
	The length of the resulting string is always a multiple of 4 bytes.
	The string ends with 1 to 4 zero-bytes ('\x00') 
	"""
	
	OSCstringLength = math.ceil((len(next)+1) / 4.0) * 4
	return struct.pack(">%ds" % (OSCstringLength), str(next))

def OSCBlob(next):
	"""Convert a string into an OSC Blob.
	An OSC-Blob is a binary encoded block of data, prepended by a 'size' (int32).
	The size is always a mutiple of 4 bytes. 
	The blob ends with 0 to 3 zero-bytes ('\x00') 
	"""

	if type(next) in types.StringTypes:
		OSCblobLength = math.ceil((len(next)) / 4.0) * 4
		binary = struct.pack(">i%ds" % (OSCblobLength), OSCblobLength, next)
	else:
		binary = ""

	return binary

def OSCArgument(next, typehint=None):
	""" Convert some Python types to their
	OSC binary representations, returning a
	(typetag, data) tuple.
	"""
	if not typehint:
		if type(next) in FloatTypes:
			binary  = struct.pack(">f", float(next))
			tag = 'f'
		elif type(next) in IntTypes:
			binary  = struct.pack(">i", int(next))
			tag = 'i'
		else:
			binary  = OSCString(next)
			tag = 's'

	elif typehint == 'f':
		try:
			binary  = struct.pack(">f", float(next))
			tag = 'f'
		except ValueError:
			binary  = OSCString(next)
			tag = 's'
	elif typehint == 'i':
		try:
			binary  = struct.pack(">i", int(next))
			tag = 'i'
		except ValueError:
			binary  = OSCString(next)
			tag = 's'
	else:
		binary  = OSCString(next)
		tag = 's'

	return (tag, binary)

def OSCTimeTag(time):
	"""Convert a time in floating seconds to its
	OSC binary representation
	"""
	if time > 0:
		fract, secs = math.modf(time)
		binary = struct.pack('>ll', long(secs), long(fract * 1e9))
	else:
		binary = struct.pack('>ll', 0L, 1L)

	return binary

######
#
# OSCMessage decoding functions
#
######

def _readString(data):
	"""Reads the next (null-terminated) block of data
	"""
	length   = string.find(data,"\0")
	nextData = int(math.ceil((length+1) / 4.0) * 4)
	return (data[0:length], data[nextData:])

def _readBlob(data):
	"""Reads the next (numbered) block of data
	"""
	
	length   = struct.unpack(">i", data[0:4])[0]
	nextData = int(math.ceil((length) / 4.0) * 4) + 4
	return (data[4:length+4], data[nextData:])

def _readInt(data):
	"""Tries to interpret the next 4 bytes of the data
	as a 32-bit integer. """
	
	if(len(data)<4):
		print "Error: too few bytes for int", data, len(data)
		rest = data
		integer = 0
	else:
		integer = struct.unpack(">i", data[0:4])[0]
		rest	= data[4:]

	return (integer, rest)

def _readLong(data):
	"""Tries to interpret the next 8 bytes of the data
	as a 64-bit signed integer.
	 """

	high, low = struct.unpack(">ll", data[0:8])
	big = (long(high) << 32) + low
	rest = data[8:]
	return (big, rest)

def _readTimeTag(data):
	"""Tries to interpret the next 8 bytes of the data
	as a TimeTag.
	 """
	high, low = struct.unpack(">ll", data[0:8])
	if (high == 0) and (low <= 1):
		time = 0.0
	else:
		time = int(high) + float(low / 1e9)
	rest = data[8:]
	return (time, rest)

def _readFloat(data):
	"""Tries to interpret the next 4 bytes of the data
	as a 32-bit float. 
	"""
	
	if(len(data)<4):
		print "Error: too few bytes for float", data, len(data)
		rest = data
		float = 0
	else:
		float = struct.unpack(">f", data[0:4])[0]
		rest  = data[4:]

	return (float, rest)

def decodeOSC(data):
	"""Converts a binary OSC message to a Python list. 
	"""
	table = {"i":_readInt, "f":_readFloat, "s":_readString, "b":_readBlob}
	decoded = []
	address,  rest = _readString(data)
	if address.startswith(","):
		typetags = address
		address = ""
	else:
		typetags = ""

	if address == "#bundle":
		time, rest = _readTimeTag(rest)
		decoded.append(address)
		decoded.append(time)
		while len(rest)>0:
			length, rest = _readInt(rest)
			decoded.append(decodeOSC(rest[:length]))
			rest = rest[length:]

	elif len(rest)>0:
		if not len(typetags):
			typetags, rest = _readString(rest)
		decoded.append(address)
		decoded.append(typetags)
		if typetags.startswith(","):
			for tag in typetags[1:]:
				value, rest = table[tag](rest)
				decoded.append(value)
		else:
			raise OSCError("OSCMessage's typetag-string lacks the magic ','")

	return decoded

######
#
# Utility functions
#
######

def hexDump(bytes):
	""" Useful utility; prints the string in hexadecimal.
	"""
	print "byte   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F"

	num = len(bytes)
	for i in range(num):
		if (i) % 16 == 0:
			 line = "%02X0 : " % (i/16)
		line += "%02X " % ord(bytes[i])
		if (i+1) % 16 == 0:
			print "%s: %s" % (line, repr(bytes[i-15:i+1]))
			line = ""

	bytes_left = num % 16
	if bytes_left:
		print "%s: %s" % (line.ljust(54), repr(bytes[-bytes_left:]))

def getUrlStr(*args):
	"""Convert provided arguments to a string in 'host:port/prefix' format
	Args can be:
	  - (host, port)
	  - (host, port), prefix
	  - host, port
	  - host, port, prefix
	"""
	if not len(args):
		return ""
		
	if type(args[0]) == types.TupleType:
		host = args[0][0]
		port = args[0][1]
		args = args[1:]
	else:
		host = args[0]
		port = args[1]
		args = args[2:]
		
	if len(args):
		prefix = args[0]
	else:
		prefix = ""
	
	if len(host) and (host != '0.0.0.0'):
		try:
			(host, _, _) = socket.gethostbyaddr(host)
		except socket.error:
			pass
	else:
		host = 'localhost'
	
	if type(port) == types.IntType:
		return "%s:%d%s" % (host, port, prefix)
	else:
		return host + prefix
		
def parseUrlStr(url):
	"""Convert provided string in 'host:port/prefix' format to it's components
	Returns ((host, port), prefix)
	"""
	if not (type(url) in types.StringTypes and len(url)):
		return (None, '')

	i = url.find("://")
	if i > -1:
		url = url[i+3:]
		
	i = url.find(':')
	if i > -1:
		host = url[:i].strip()
		tail = url[i+1:].strip()
	else:
		host = ''
		tail = url
	
	for i in range(len(tail)):
		if not tail[i].isdigit():
			break
	else:
		i += 1
	
	portstr = tail[:i].strip()
	tail = tail[i:].strip()
	
	found = len(tail)
	for c in ('/', '+', '-', '*'):
		i = tail.find(c)
		if (i > -1) and (i < found):
			found = i
	
	head = tail[:found].strip()
	prefix = tail[found:].strip()
	
	prefix = prefix.strip('/')
	if len(prefix) and prefix[0] not in ('+', '-', '*'):
		prefix = '/' + prefix
	
	if len(head) and not len(host):
		host = head

	if len(host):
		try:
			host = socket.gethostbyname(host)
		except socket.error:
			pass

	try:
		port = int(portstr)
	except ValueError:
		port = None
	
	return ((host, port), prefix)

######
#
# FilterString Utility functions
#
######

def parseFilterStr(args):
	"""Convert Message-Filter settings in '+<addr> -<addr> ...' format to a dict of the form
	{ '<addr>':True, '<addr>':False, ... } 
	Returns a list: ['<prefix>', filters]
	"""
	out = {}
	
	if type(args) in types.StringTypes:
		args = [args]
		
	prefix = None
	for arg in args:
		head = None
		for plus in arg.split('+'):
			minus = plus.split('-')
			plusfs = minus.pop(0).strip()
			if len(plusfs):
				plusfs = '/' + plusfs.strip('/')
			
			if (head == None) and (plusfs != "/*"):
				head = plusfs
			elif len(plusfs):
				if plusfs == '/*':
					out = { '/*':True }	# reset all previous filters
				else:
					out[plusfs] = True
				
			for minusfs in minus:
				minusfs = minusfs.strip()
				if len(minusfs):
					minusfs = '/' + minusfs.strip('/')
					if minusfs == '/*':
						out = { '/*':False }	# reset all previous filters
					else:
						out[minusfs] = False
				
		if prefix == None:
			prefix = head

	return [prefix, out]

def getFilterStr(filters):
	"""Return the given 'filters' dict as a list of
	'+<addr>' | '-<addr>' filter-strings
	"""
	if not len(filters):
		return []
	
	if '/*' in filters.keys():
		if filters['/*']:
			out = ["+/*"]
		else:
			out = ["-/*"]
	else:
		if False in filters.values():
			out = ["+/*"]
		else:
			out = ["-/*"]
	
	for (addr, bool) in filters.items():
		if addr == '/*':
			continue
		
		if bool:
			out.append("+%s" % addr)
		else:
			out.append("-%s" % addr)

	return out

# A translation-table for mapping OSC-address expressions to Python 're' expressions
OSCtrans = string.maketrans("{,}?","(|).")

def getRegEx(pattern):
	"""Compiles and returns a 'regular expression' object for the given address-pattern.
	"""
	# Translate OSC-address syntax to python 're' syntax
	pattern = pattern.replace(".", r"\.")		# first, escape all '.'s in the pattern.
	pattern = pattern.replace("(", r"\(")		# escape all '('s.
	pattern = pattern.replace(")", r"\)")		# escape all ')'s.
	pattern = pattern.replace("*", r".*")		# replace a '*' by '.*' (match 0 or more characters)
	pattern = pattern.translate(OSCtrans)		# change '?' to '.' and '{,}' to '(|)'
	
	return re.compile(pattern)


######
#
# OSCRequestHandler classes
#
######

class OSCRequestHandler(DatagramRequestHandler):
	"""RequestHandler class for the OSCServer
	"""
	def dispatchMessage(self, pattern, tags, data):
		"""Attmept to match the given OSC-address pattern, which may contain '*',
		against all callbacks registered with the OSCServer.
		Calls the matching callback and returns whatever it returns.
		If no match is found, and a 'default' callback is registered, it calls that one,
		or raises NoCallbackError if a 'default' callback is not registered.
		
		  - pattern (string):  The OSC-address of the receied message
		  - tags (string):  The OSC-typetags of the receied message's arguments, without ','
		  - data (list):  The message arguments
		"""
		self.server.callback(pattern, tags, data, self.client_address)
		
	def setup(self):
		"""Prepare RequestHandler.
		Unpacks request as (packet, source socket address)
		Creates an empty list for replies.
		"""
		(self.packet, self.socket) = self.request

	def _unbundle(self, decoded):
		"""Recursive bundle-unpacking function"""
		if decoded[0] != "#bundle":
			self.dispatchMessage(decoded[0], decoded[1][1:], decoded[2:])
		
	def handle(self):
		"""Handle incoming OSCMessage
		"""
		decoded = decodeOSC(self.packet)
		if not len(decoded):
			return
		
		self._unbundle(decoded)
		
	def finish(self):
		"""Finish handling OSCMessage.
		Send any reply returned by the callback(s) back to the originating client
		as an OSCMessage or OSCBundle
		"""
		pass

class ThreadingOSCRequestHandler(OSCRequestHandler):
	"""Multi-threaded OSCRequestHandler;
	Starts a new RequestHandler thread for each unbundled OSCMessage
	"""
	def _unbundle(self, decoded):
		"""Recursive bundle-unpacking function
		This version starts a new thread for each sub-Bundle found in the Bundle,
		then waits for all its children to finish.
		"""
		
		if decoded[0] != "#bundle":
			self.dispatchMessage(decoded[0], decoded[1][1:], decoded[2:])
			return
		
######
#
# OSCServer classes
#
######

class OSCServer(UDPServer):
	"""A Synchronous OSCServer
	Serves one request at-a-time, until the OSCServer is closed.
	The OSC address-pattern is matched against a set of OSC-adresses
	that have been registered to the server with a callback-function.
	If the adress-pattern of the message machtes the registered address of a callback,
	that function is called. 
	"""
	
	# set the RequestHandlerClass, will be overridden by ForkingOSCServer & ThreadingOSCServer
	RequestHandlerClass = OSCRequestHandler
	
	# define a socket timeout, so the serve_forever loop can actually exit.
	socket_timeout = 0.
	
	# DEBUG: print error-tracebacks (to stderr)?
	print_tracebacks = False
	
	def __init__(self, server_address, client=None, return_port=0):
		"""Instantiate an OSCServer.
		  - server_address ((host, port) tuple): the local host & UDP-port
		  the server listens on
		  - client (OSCClient instance): The OSCClient used to send replies from this server.
		  If none is supplied (default) an OSCClient will be created.
		  - return_port (int): if supplied, sets the default UDP destination-port
		  for replies coming from this server.
		"""
		UDPServer.__init__(self, server_address, self.RequestHandlerClass)
		
		self.callback = None
		self.socket.settimeout(self.socket_timeout)
		self.running = False

	def serve_forever(self):
		"""Handle one request at a time until server is closed."""
		self.running = True
		while self.running:
			self.handle_request()	# this times-out when no data arrives.

	def close(self):
		"""Stops serving requests, closes server (socket), closes used client
		"""
		self.running = False
		self.client.close()
		self.server_close()
	
	def __str__(self):
		"""Returns a string containing this Server's Class-name, software-version and local bound address (if any)
		"""
		out = self.__class__.__name__
		out += " v%s.%s-%s" % version
		addr = self.address()
		if addr:
			out += " listening on osc://%s" % getUrlStr(addr)
		else:
			out += " (unbound)"
			
		return out
	
	def __eq__(self, other):
		"""Compare function.
		"""
		if not isinstance(other, self.__class__):
			return False
			
		return cmp(self.socket._sock, other.socket._sock)

	def __ne__(self, other):
		"""Compare function.
		"""
		return not self.__eq__(other)

	def address(self):
		"""Returns a (host,port) tuple of the local address this server is bound to,
		or None if not bound to any address.
		"""
		try:
			return self.socket.getsockname()
		except socket.error:
			return None
	
	def reportErr(self, txt, client_address):
		"""Writes 'OSCServer: txt' to sys.stderr
		If self.error_prefix is defined, sends 'txt' as an OSC error-message to the client(s)
		(see printErr() and sendOSCerror())
		"""
		self.printErr(txt)
		
		if len(self.error_prefix):
			self.sendOSCerror(txt, client_address)
	
class ForkingOSCServer(ForkingMixIn, OSCServer):
	"""An Asynchronous OSCServer.
	This server forks a new process to handle each incoming request.
	""" 
	# set the RequestHandlerClass, will be overridden by ForkingOSCServer & ThreadingOSCServer
	RequestHandlerClass = ThreadingOSCRequestHandler

class ThreadingOSCServer(ThreadingMixIn, OSCServer):
	"""An Asynchronous OSCServer.
	This server starts a new thread to handle each incoming request.
	""" 
	# set the RequestHandlerClass, will be overridden by ForkingOSCServer & ThreadingOSCServer
	RequestHandlerClass = ThreadingOSCRequestHandler

######
#
# OSCError classes
#
######

class OSCError(Exception):
	"""Base Class for all OSC-related errors
	"""
	def __init__(self, message):
		self.message = message

	def __str__(self):
		return self.message

class OSCClientError(OSCError):
	"""Class for all OSCClient errors
	"""
	pass

class OSCServerError(OSCError):
	"""Class for all OSCServer errors
	"""
	pass

class NoCallbackError(OSCServerError):
	"""This error is raised (by an OSCServer) when an OSCMessage with an 'unmatched' address-pattern
	is received, and no 'default' handler is registered.
	"""
	def __init__(self, pattern):
		"""The specified 'pattern' should be the OSC-address of the 'unmatched' message causing the error to be raised.
		"""
		self.message = "No callback registered to handle OSC-address '%s'" % pattern

class NotSubscribedError(OSCClientError):
	"""This error is raised (by an OSCMultiClient) when an attempt is made to unsubscribe a host
	that isn't subscribed.
	"""
	def __init__(self, addr, prefix=None):
		if prefix:
			url = getUrlStr(addr, prefix)
		else:
			url = getUrlStr(addr, '')

		self.message = "Target osc://%s is not subscribed" % url
