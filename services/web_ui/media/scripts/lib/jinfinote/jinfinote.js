/*
Copyright (c) 2009-2011 Simon Veith <simon@jinfinote.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

/** @namespace
 */
Operations = {};

/** Instantiates a new NoOp operation object.
 *  @class An operation that does nothing.
 */
Operations.NoOp = function() {};

Operations.NoOp.prototype.requiresCID = false;

Operations.NoOp.prototype.toString = function() { return "NoOp()"; };

Operations.NoOp.prototype.toHTML = Operations.NoOp.prototype.toString;

/** Applies this NoOp operation to a buffer. This does nothing, per
 *  definition. */
Operations.NoOp.prototype.apply = function(buffer) {};

/** Transforms this NoOp operation against another operation. This returns a
 *  new NoOp operation.
 *  @type Operations.NoOp
 */
Operations.NoOp.prototype.transform = function(other) { 
	return new Operations.NoOp();
};

/** Mirrors this NoOp operation. This returns a new NoOp operation.
 *  @type Operations.NoOp
 */
Operations.NoOp.prototype.mirror = function() {
	return new Operations.NoOp();
};

/** Instantiates a new Insert operation object.
 *  @class An operation that inserts a Buffer at a certain offset.
 *  @param {Number} position The offset at which the text is to be inserted.
 *  @param {Buffer} text The Buffer to insert.
 */
Operations.Insert = function(position, text) {
	this.position = position;
	this.text = text.copy();
};

Operations.Insert.prototype.requiresCID = true;

Operations.Insert.prototype.toString = function() {
	return "Insert(" + this.position + ", " + this.text + ")";
};

Operations.Insert.prototype.toHTML = function() {
	return "Insert(" + this.position + ", " + this.text.toHTML() + ")";
};

/** Applies the insert operation to the given Buffer.
 *  @param {Buffer} buffer The buffer in which the insert operation is to be
 *  performed.
 */
Operations.Insert.prototype.apply = function(buffer) {
	buffer.splice(this.position, 0, this.text);
};

/** Computes the concurrency ID against another Insert operation.
 *  @param {Operations.Insert} other
 *  @returns The operation that is to be transformed.
 *  @type Operations.Insert
 */
Operations.Insert.prototype.cid = function(other) {
	if(this.position < other.position)
		return other;
	if(this.position > other.position)
		return this;
};

/** Returns the total length of data to be inserted by this insert operation,
 *  in characters.
 *  @type Number
 */
Operations.Insert.prototype.getLength = function() {
	return this.text.getLength();
};

/** Transforms this Insert operation against another operation, returning the
 *  resulting operation as a new object.
 *  @param {Operation} other The operation to transform against.
 *  @param {Operation} [cid] The cid to take into account in the case of
 *  conflicts.
 *  @type Operation
 */
Operations.Insert.prototype.transform = function(other, cid) {
	if(other instanceof Operations.NoOp)
		return new Operations.Insert(this.position, this.text);
	
	if(other instanceof Operations.Split) {
		// We transform against the first component of the split operation
		// first.
		var transformFirst = this.transform(other.first,
			(cid == this ? this : other.first));
		
		// The second part of the split operation is transformed against its
		// first part.
		var newSecond = other.second.transform(other.first);
		
		var transformSecond = transformFirst.transform(newSecond,
			(cid == this ? transformFirst : newSecond));
		
		return transformSecond;
	}
	
	var pos1 = this.position;
	var str1 = this.text;
	var pos2 = other.position;
	
	if(other instanceof Operations.Insert) {
		var str2 = other.text;
		
		if(pos1 < pos2 || (pos1 == pos2 && cid == other))
			return new Operations.Insert(pos1, str1);
		if(pos1 > pos2 || (pos1 == pos2 && cid == this))
			return new Operations.Insert(pos1 + str2.getLength(), str1);
	} else if(other instanceof Operations.Delete) {
		var len2 = other.getLength();
		
		if(pos1 >= pos2 + len2)
			return new Operations.Insert(pos1 - len2, str1);
		if(pos1 < pos2)
			return new Operations.Insert(pos1, str1);
		if(pos1 >= pos2 && pos1 < pos2 + len2)
			return new Operations.Insert(pos2, str1);
	}
};

/** Returns the inversion of this Insert operation.
 *  @type Operations.Delete
 */
Operations.Insert.prototype.mirror = function() {
	return new Operations.Delete(this.position, this.text.copy());
};

/** Instantiates a new Delete operation object.
 *  Delete operations can be reversible or not, depending on how they are
 *  constructed. Delete operations constructed with a Buffer object know which
 *  text they are removing from the buffer and can therefore be mirrored,
 *  whereas Delete operations knowing only the amount of characters to be
 *  removed are non-reversible.
 *  @class An operation that removes a range of characters in the target
 *  buffer.
 *  @param {Number} position The offset of the first character to remove.
 *  @param what The data to be removed. This can be either a numeric value
 *  or a Buffer object.
 */
Operations.Delete = function(position, what, recon) {
	this.position = position;
	
	if(what instanceof Buffer)
		this.what = what.copy();
	else
		this.what = what;
	
	if(recon)
		this.recon = recon;
	else
		this.recon = new Recon();
};

Operations.Delete.prototype.requiresCID = false;

Operations.Delete.prototype.toString = function() {
	return "Delete(" + this.position + ", " + this.what + ")";
};

Operations.Delete.prototype.toHTML = function() {
	return "Delete(" + this.position + ", " + 
		(this.what instanceof Buffer ? this.what.toHTML() : this.what) + ")";
};

/** Determines whether this Delete operation is reversible.
 *  @type Boolean
 */
Operations.Delete.prototype.isReversible = function() {
	return (this.what instanceof Buffer);
};

/** Applies this Delete operation to a buffer.
 *  @param {Buffer} buffer The buffer to which the operation is to be applied.
 */
Operations.Delete.prototype.apply = function(buffer) {
	buffer.splice(this.position, this.getLength());
};

Operations.Delete.prototype.cid = function(other) {};

/** Returns the number of characters that this Delete operation removes.
 *  @type Number
 */
Operations.Delete.prototype.getLength = function() {
	if(this.isReversible())
		return this.what.getLength();
	else
		return this.what;
};

/** Splits this Delete operation into two Delete operations at the given
 *  offset. The resulting Split operation will consist of two Delete
 *  operations which, when combined, affect the same range of text as the
 *  original Delete operation.
 *  @param {Number} at Offset at which to split the Delete operation.
 *  @type Operations.Split
 */
Operations.Delete.prototype.split = function(at) {
	if(this.isReversible())
	{
		// This is a reversible Delete operation. No need to to any
		// processing for recon data.
		console.log(at);
		return new Operations.Split(            
			new Operations.Delete(this.position, this.what.slice(0, at)),
			new Operations.Delete(this.position + at, this.what.slice(at))
		);
	} else {
		// This is a non-reversible Delete operation that might carry recon
		// data. We need to split that data accordingly between the two new
		// components.
		var recon1 = new Recon();
		var recon2 = new Recon();
		
		for(index in this.recon.segments)
		{
			if(this.recon.segments[index].offset < at)
				recon1.segments.push(this.recon.segments[index]);
			else
				recon2.segments.push(
					new ReconSegment(this.recon.segments[index].offset - at,
						this.recon.segments[index].buffer)
				);
		}
		
		return new Operations.Split(
			new Operations.Delete(this.position, at, recon1),
			new Operations.Delete(this.position + at, this.what - at, recon2)
		);
	}
};

/** Returns the range of text in a buffer that this Delete or Split-Delete
 *  operation removes.
 *  @param operation A Split-Delete or Delete operation
 *  @param {Buffer} buffer
 *  @type Buffer
 */
Operations.Delete.getAffectedString = function(operation, buffer) {
	if(operation instanceof Operations.Split)
	{
		// The other operation is a Split operation. We call this function
		// again recursively for each component.
		var part1 = Operations.Delete.getAffectedString(operation.first,
			buffer);
		var part2 = Operations.Delete.getAffectedString(operation.second,
			buffer);
		
		part2.splice(0, 0, part1);
		return part2;
	} else if (operation instanceof Operations.Delete) {
		// In the process of determining the affected string, we also
		// have to take into account the data that has been "transformed away"
		// from the Delete operation and which is stored in the Recon object.
		
		var reconBuffer = buffer.slice(operation.position, operation.position
			+ operation.getLength());
		
		operation.recon.restore(reconBuffer);

		return reconBuffer;
	}
};

/** Makes this Delete operation reversible, given a transformed version of 
 *  this operation in a buffer matching its state. If this Delete operation is
 *  already reversible, this function simply returns a copy of it.
 *  @param {Operations.Delete} transformed A transformed version of this
 *  operation.
 *  @param {State} state The state in which the transformed operation could be
 *  applied.
 */
Operations.Delete.prototype.makeReversible = function(transformed, state) {
	if(this.what instanceof Buffer)
		return new Operations.Delete(this.position, this.what);
	else {
		return new Operations.Delete(this.position, 
			Operations.Delete.getAffectedString(transformed, state.buffer)
		);
	}
};

/** Merges a Delete operation with another one. The resulting Delete operation
 *  removes the same range of text as the two separate Delete operations would
 *  when executed sequentially.
 *  @param {Operations.Delete} other
 *  @type Operations.Delete
 */
Operations.Delete.prototype.merge = function(other) {
	if(this.isReversible()) {
		if(!other.isReversible())
			throw "Cannot merge reversible operations with non-reversible ones";
		
		var newBuffer = this.what.copy();
		newBuffer.splice(newBuffer.getLength(), 0, other.what);
		return new Operations.Delete(this.position, newBuffer);
	} else {
		var newLength = this.getLength() + other.getLength();
		return new Operations.Delete(this.position, newLength);
	}
};

/** Transforms this Delete operation against another operation.
 *  @param {Operation} other
 *  @param {Operation} [cid]
 */
Operations.Delete.prototype.transform = function(other, cid) {
	if(other instanceof Operations.NoOp)
		return new Operations.Delete(this.position, this.what, this.recon);
	
	if(other instanceof Operations.Split) {
		// We transform against the first component of the split operation
		// first.
		var transformFirst = this.transform(other.first,
			(cid == this ? this : other.first));
		
		// The second part of the split operation is transformed against its
		// first part.
		var newSecond = other.second.transform(other.first);
		
		var transformSecond = transformFirst.transform(newSecond,
			(cid == this ? transformFirst : newSecond));
		
		return transformSecond;
	}
	
	var pos1 = this.position;
	var len1 = this.getLength();
	
	var pos2 = other.position;
	var len2 = other.getLength();
	
	if(other instanceof Operations.Insert)
	{
		if(pos2 >= pos1 + len1)
			return new Operations.Delete(pos1, this.what, this.recon);
		if(pos2 <= pos1)
			return new Operations.Delete(pos1 + len2, this.what, this.recon);
		if(pos2 > pos1 && pos2 < pos1 + len1)
		{
			var result = this.split(pos2 - pos1);
			result.second.position += len2;
			return result;
		}
	} else if(other instanceof Operations.Delete) {
		if(pos1 + len1 <= pos2)
			return new Operations.Delete(pos1, this.what, this.recon);
		if(pos1 >= pos2 + len2)
			return new Operations.Delete(pos1 - len2, this.what, this.recon);
		if(pos2 <= pos1 && pos2 + len2 >= pos1 + len1) {
			/*     1XXXXX|
			 * 2-------------|
			 *
			 * This operation falls completely within the range of another,
			 * i.e. all data has already been removed. The resulting
			 * operation removes nothing.
			 */
			var newData = (this.isReversible() ? new Buffer() : 0);
			var newRecon = this.recon.update(0,
				other.what.slice(pos1 - pos2, pos1 - pos2 + len1) );
			return new Operations.Delete(pos2, newData, newRecon);
		}
		if(pos2 <= pos1 && pos2 + len2 < pos1 + len1)
		{
			/*     1XXXX----|
			 * 2--------|
			 * 
			 * The first part of this operation falls within the range of
			 * another.
			 */
			var result = this.split(pos2 + len2 - pos1);
			result.second.position = pos2;
			result.second.recon = this.recon.update(0,
				other.what.slice(pos1 - pos2) );
			return result.second;
		}
		if(pos2 > pos1 && pos2 + len2 >= pos1 + len1)
		{
			/* 1----XXXXX|
			 *     2--------|
			 *
			 * The second part of this operation falls within the range of
			 * another.
			 */
			var result = this.split(pos2 - pos1);
			result.first.recon = this.recon.update(result.first.getLength(), other.what.slice(0, pos1 + len1 - pos2) );
			return result.first;
		}
		if(pos2 > pos1 && pos2 + len2 < pos1 + len1)
		{
			/* 1-----XXXXXX---|
			 *      2------|
			 *
			 * Another operation falls completely within the range of this
			 * operation. We remove that part.
			 */
			
			// We split this operation two times: first at the beginning of
			// the second operation, then at the end of the second operation.
			var r1 = this.split(pos2 - pos1);
			var r2 = r1.second.split(len2);
			
			// The resulting Delete operation consists of the first and the
			// last part, which are merged back into a single operation.
			var result = r1.first.merge(r2.second);
			result.recon = this.recon.update(pos2 - pos1, other.what);
			return result;
		}
	}
};

/** Mirrors this Delete operation. Returns an operation which inserts the text
 *  that this Delete operation would remove. If this Delete operation is not
 *  reversible, the return value is undefined.
 *  @type Operations.Insert
 */
Operations.Delete.prototype.mirror = function() {
	if(this.isReversible())
		return new Operations.Insert(this.position, this.what.copy());
};

/** Instantiates a new Split operation object.
 *  @class An operation which wraps two different operations into a single
 *  object. This is necessary for example in order to transform a Delete
 *  operation against an Insert operation which falls into the range that is
 *  to be deleted.
 *  @param {Operation} first
 *  @param {Operation} second
 */
Operations.Split = function(first, second) {
    console.log('split');
	this.first = first;
	this.second = second;
};

Operations.Split.prototype.requiresCID = true;

Operations.Split.prototype.toString = function() {
	return "Split(" + this.first + ", " + this.second + ")";
};

Operations.Split.prototype.toHTML = function() {
	return "Split(" + this.first.toHTML() + ", " + this.second.toHTML() + ")";
};

/** Applies the two components of this split operation to the given buffer
 *  sequentially. The second component is implicitly transformed against the 
 *  first one in order to do so.
 *  @param {Buffer} buffer The buffer to which this operation is to be applied.
 */
Operations.Split.prototype.apply = function(buffer) {
	this.first.apply(buffer);
	var transformedSecond = this.second.transform(this.first);
	transformedSecond.apply(buffer);
};

Operations.Split.prototype.cid = function() {};

/** Transforms this Split operation against another operation. This is done
 *  by transforming both components individually.
 *  @param {Operation} other
 *  @param {Operation} [cid]
 */
Operations.Split.prototype.transform = function(other, cid) {
	if(cid == this || cid == other)
		return new Operations.Split(
			this.first.transform(other, (cid == this ? this.first : other)),
			this.second.transform(other, (cid == this ? this.second : other))
		);
	else
		return new Operations.Split(
			this.first.transform(other),
			this.second.transform(other)
		);
};

/** Mirrors this Split operation. This is done by transforming the second
 *  component against the first one, then mirroring both components
 *  individually.
 *  @type Operations.Split
 */
Operations.Split.prototype.mirror = function() {
	var newSecond = this.second.transform(this.first);
	return new Operations.Split(this.first.mirror(), newSecond.mirror());
};

/** Creates a new Recon object.
 *  @class The Recon class is a helper class which collects the parts of a
 *  Delete operation that are lost during transformation. This is used to
 *  reconstruct the text of a remote Delete operation that was issued in a
 *  previous state, and thus to make such a Delete operation reversible.
 *  @param {Recon} [recon] Pre-initialize the Recon object with data from
 *  another object.
 */
function Recon(recon) {
	if(recon)
		this.segments = recon.segments.slice(0);
	else
		this.segments = new Array();
}

Recon.prototype.toString = function() {
	return "Recon(" + this.segments + ")";
};

/** Creates a new Recon object with an additional piece of text to be restored
 *  later.
 *  @param {Number} offset
 *  @param {Buffer} buffer
 *  @type {Recon}
 */
Recon.prototype.update = function(offset, buffer) {
	var newRecon = new Recon(this);
	if(buffer instanceof Buffer)
		newRecon.segments.push(new ReconSegment(offset, buffer));
	return newRecon;
};

/** Restores the recon data in the given buffer.
 *  @param {Buffer} buffer
 */
Recon.prototype.restore = function(buffer) {
	for(var index in this.segments)
	{
		var segment = this.segments[index];
		buffer.splice(segment.offset, 0, segment.buffer);
	}
};

/** Instantiates a new ReconSegment object.
 *  @class ReconSegments store a range of text combined with the offset at
 *  which they are to be inserted upon restoration.
 *  @param {Number} offset
 *  @param {Buffer} buffer
 */
function ReconSegment(offset, buffer) {
	this.offset = offset;
	this.buffer = buffer.copy();
}

ReconSegment.prototype.toString = function() {
	return "(" + this.offset + ", " + this.buffer + ")";
};
/*
Copyright (c) 2009-2011 Simon Veith <simon@jinfinote.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

/** Initializes a new DoRequest object.
 *  @class Represents a request made by an user at a certain time.
 *  @param {Number} user The user that issued the request
 *  @param {Vector} vector The time at which the request was issued
 *  @param {Operation} operation
 */
function DoRequest(user, vector, operation) {
	this.user = user;
	this.vector = vector;
	this.operation = operation;
}

DoRequest.prototype.toString = function() {
	return "DoRequest(" + 
		[this.user, this.vector, this.operation].join(", ") + ")";
};

DoRequest.prototype.toHTML = function() {
	return "DoRequest(" + 
		[this.user, this.vector.toHTML(), this.operation.toHTML()].join(", ")
		+ ")";
};

DoRequest.prototype.copy = function() {
	return new DoRequest(this.user, this.vector, this.operation);
};

/** Applies the request to a State.
 *  @param {State} state The state to which the request should be applied.
 */
DoRequest.prototype.execute = function(state) {
	this.operation.apply(state.buffer);
	
	state.vector = state.vector.incr(this.user, 1);
	
	return this;
};

/** Transforms this request against another request.
 *  @param {DoRequest} other
 *  @param {DoRequest} [cid] The concurrency ID of the two requests. This is
 *  the request that is to be transformed in case of conflicting operations.
 *  @type DoRequest
 */
DoRequest.prototype.transform = function(other, cid) {
	if(this.operation instanceof Operations.NoOp)
		var newOperation = new Operations.NoOp();
	else {
		var op_cid;
		if(cid == this)
			op_cid = this.operation;
		if(cid == other)
			op_cid = other.operation;
		
		var newOperation = this.operation.transform(other.operation, op_cid);
	}
	
	return new DoRequest(this.user, this.vector.incr(other.user),
		newOperation);
};

/** Mirrors the request. This inverts the operation and increases the issuer's
 *  component of the request time by the given amount.
 *  @param {Number} [amount] The amount by which the request time is
 *  increased. Defaults to 1.
 *  @type DoRequest
 */
DoRequest.prototype.mirror = function(amount) {
	if(typeof(amount) != "number")
		amount = 1;
	return new DoRequest(this.user, this.vector.incr(this.user, amount),
		this.operation.mirror());
};

/** Folds the request along another user's axis. This increases that user's
 *  component by the given amount, which must be a multiple of 2.
 *  @type DoRequest
 */
DoRequest.prototype.fold = function(user, amount) {
	if(amount % 2 == 1)
		throw "Fold amounts must be multiples of 2.";
	return new DoRequest(this.user, this.vector.incr(user, amount),
		this.operation);
};

/** Makes a request reversible, given a translated version of this request
 *  and a State object. This only applies to requests carrying a Delete
 *  operation; for all others, this does nothing.
 *  @param {DoRequest} translated This request translated to the given state
 *  @param {State} state The state which is used to make the request
 *  reversible.
 *  @type DoRequest
 */
DoRequest.prototype.makeReversible = function(translated, state) {
	var result = this.copy();
	
	if(this.operation instanceof Operations.Delete) {
		result.operation = this.operation.makeReversible(translated.operation,
			state);
	}
	
	return result;
};

/** Instantiates a new undo request.
 *  @class Represents an undo request made by an user at a certain time.
 *  @param {Number} user
 *  @param {Vector} vector The time at which the request was issued.
 */
function UndoRequest(user, vector) {
	this.user = user;
	this.vector = vector;
}

UndoRequest.prototype.toString = function() {
	return "UndoRequest(" + [this.user, this.vector].join(", ") + ")";
};

UndoRequest.prototype.toHTML = function() {
	return "UndoRequest(" + [this.user, this.vector.toHTML()].join(", ")
		+ ")";
};

UndoRequest.prototype.copy = function() {
	return new UndoRequest(this.user, this.vector);
};

/** Finds the corresponding DoRequest to this UndoRequest.
 *  @param {Array} log The log to search
 *  @type DoRequest
 */
UndoRequest.prototype.associatedRequest = function(log) {
	var sequence = 1;
	var index = _indexOf(log, this);
	
	if(index == -1)
		index = log.length - 1;
	
	for(; index >= 0; index--)
	{
		if(log[index] === this || log[index].user != this.user)
			continue;
		if(log[index].vector.get(this.user) > this.vector.get(this.user))
			continue;
		
		if(log[index] instanceof UndoRequest)
			sequence += 1;
		else
			sequence -= 1;
		
		if(sequence == 0)
			return log[index];
	}
};

/** Instantiates a new redo request.
 *  @class Represents an redo request made by an user at a certain time.
 *  @param {Number} user
 *  @param {Vector} vector The time at which the request was issued.
 */
function RedoRequest(user, vector) {
	this.user = user;
	this.vector = vector;
}

RedoRequest.prototype.toString = function() {
	return "RedoRequest(" + [this.user, this.vector].join(", ") + ")";
};

RedoRequest.prototype.toHTML = function() {
	return "RedoRequest(" + [this.user, this.vector.toHTML()].join(", ") + ")";
};

RedoRequest.prototype.copy = function() {
	return new RedoRequest(this.user, this.vector);
};

/** Finds the corresponding UndoRequest to this RedoRequest.
 *  @param {Array} log The log to search
 *  @type UndoRequest
 */
RedoRequest.prototype.associatedRequest = function(log) {
	var sequence = 1;
	var index = _indexOf(log, this);
	
	if(index == -1)
		index = log.length - 1;
	
	for(; index >= 0; index--)
	{
		if(log[index] === this || log[index].user != this.user)
			continue;
		if(log[index].vector.get(this.user) > this.vector.get(this.user))
			continue;
		
		if(log[index] instanceof RedoRequest)
			sequence += 1;
		else
			sequence -= 1;
		
		if(sequence == 0)
			return log[index];
	}
};

/** Helper function to provide an implementation of an Array's indexOf method.
 *  This is necessary for browsers that don't support JavaScript 1.6, such as
 *  Internet Explorer 6. It uses the browsers native implementation when
 *  available.
 *  @param {Array} array
 *  @param searchElement
 *  @param {Number} [fromIndex]
 */
function _indexOf(array, searchElement, fromIndex)
{
	if(array.indexOf)
		return array.indexOf(searchElement, fromIndex);
	else {
		if(typeof(fromIndex) != "number")
			fromIndex = 0;
		
		for(var index = 0; index < array.length; index ++)
		{
			if(array[index] === searchElement)
				return index;
		}
		
		return -1;
	}
}
/*
Copyright (c) 2009-2011 Simon Veith <simon@jinfinote.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

/**
 * @class Stores state vectors.
 * @param [value] Pre-initialize the vector with existing values. This can be
 * a Vector object, a generic Object with numeric properties, or a string of
 * the form "1:2;3:4;5:6".
 */
function Vector(value) {
	if(typeof(value) == "object")
	{
		for(var user in value) {
			if(user.match(Vector.user_regex) && value[user] > 0)
				this[user] = value[user];
		}
	} else if (typeof(value) == "string") {
		var match = Vector.timestring_regex.exec(value);
		while (match != null) {
			this[match[1]] = parseInt(match[2]);
			match = Vector.timestring_regex.exec(value);
		}
	}
}

/** @ignore
 *  @static */
Vector.user_regex = /\d+/;
/** @ignore
 *  @static */
Vector.timestring_regex = /(\d+):(\d+)/g;

/** Helper function to easily iterate over all users in this vector.
 *  @param {function} callback Callback function which is called with the user
 *  and the value of each component. If this callback function returns false,
 *  iteration is stopped at that point and false is returned.
 *  @type Boolean
 *  @returns True if the callback function has never returned false; returns
 *  False otherwise.
 */
Vector.prototype.eachUser = function(callback) {
	for(var user in this) {
		if(user.match(Vector.user_regex)) {
			if(callback(parseInt(user), this[user]) == false)
				return false;
		}
	}
	
	return true;
};

/** Returns this vector as a string of the form "1:2;3:4;5:6"
 *  @type String
 */
Vector.prototype.toString = function() {
	var components = new Array();
	
	this.eachUser(function(u, v) {
		if(v > 0)
			components.push(u + ":" + v);
	});
	
	components.sort();
	
	return components.join(";");
};

Vector.prototype.toHTML = Vector.prototype.toString;

/** Returns the sum of two vectors.
 *  @param {Vector} other
 */ 
Vector.prototype.add = function(other) {
	var result = new Vector(this);
	
	other.eachUser(function(u, v) {
		result[u] = result.get(u) + v;
	});
	
	return result;
};

/** Returns a copy of this vector. */
Vector.prototype.copy = function() {
	return new Vector(this);
};

/** Returns a specific component of this vector, or 0 if it is not defined.
 *  @param {Number} user Index of the component to be returned
 */
Vector.prototype.get = function(user) {
	if(this[user] != undefined)
		return this[user];
	else
		return 0;
};

/** Calculates whether this vector is smaller than or equal to another vector.
 *  This means that all components of this vector are less than or equal to
 *  their corresponding components in the other vector.
 *  @param {Vector} other The vector to compare to
 *  @type Boolean
 */
Vector.prototype.causallyBefore = function(other) {
	return this.eachUser(function(u, v) {
		return v <= other.get(u);
	});
};

/** Determines whether this vector is equal to another vector. This is true if
 *  all components of this vector are present in the other vector and match
 *  their values, and vice-versa.
 *  @param {Vector} other The vector to compare to
 *  @type Boolean
 */
Vector.prototype.equals = function(other) {
	var eq1 = this.eachUser(function(u, v) {
		return other.get(u) == v;
	});
	
	var self = this;
	var eq2 = other.eachUser(function(u, v) {
		return self.get(u) == v;
	});
	
	return eq1 && eq2;
};

/** Returns a new vector with a specific component increased by a given
 *  amount.
 *  @param {Number} user Component to increase
 *  @param {Number} [by] Amount by which to increase the component (default 1)
 *  @type Vector
 */
Vector.prototype.incr = function(user, by) {
	var result = new Vector(this);
	
	if(by == undefined)
		by = 1;
	
	result[user] = result.get(user) + by;
	
	return result;
}

/** Calculates the least common successor of two vectors.
 *  @param {Vector} v1
 *  @param {Vector} v2
 *  @type Vector
 */
Vector.leastCommonSuccessor = function(v1, v2) {
	var result = v1.copy();
	
	v2.eachUser(function(u, v) {
		var val1 = v1.get(u);
		var val2 = v2.get(u);
		
		if(val1 < val2)
			result[u] = val2;
		//else
		//	result[u] = val1; // This is already the case since we copied v1
	});
	
	return result;
};

/** Instantiates a new state object.
 *  @class Stores and manipulates the state of a document by keeping track of
 *  its state vector, content and history of executed requests.
 *  @param {Buffer} [buffer] Pre-initialize the buffer
 *  @param {Vector} [vector] Set the initial state vector
 */
function State(buffer, vector) {
	if(buffer instanceof Buffer)
		this.buffer = buffer.copy();
	else
		this.buffer = new Buffer();
	
	this.vector = new Vector(vector);
	this.request_queue = new Array();
	this.log = new Array();
	this.cache = {};
}

/** Translates a request to the given state vector.
 *  @param {Request} request The request to translate
 *  @param {Vector} targetVector The target state vector
 *  @param {Boolean} [nocache] Set to true to bypass the translation cache.
 */
State.prototype.translate = function(request, targetVector, noCache) {	
	if(request instanceof DoRequest && request.vector.equals(targetVector)) {
		// If the request vector is not an undo/redo request and is already
		// at the desired state, simply return the original request since
		// there is nothing to do.
		return request.copy();
	}
	
	// Before we attempt to translate the request, we check whether it is
	// cached already.
	var cache_key = [request, targetVector].toString();
	if(this.cache != undefined && !noCache) {
		if(!this.cache[cache_key])
			this.cache[cache_key] = this.translate(request, targetVector, true);
		
		// FIXME: translated requests are not cleared from the cache, so this
		// might fill up considerably.
		return this.cache[cache_key];
	}
	
	if(request instanceof UndoRequest || request instanceof RedoRequest)
	{
		// If we're dealing with an undo or redo request, we first try to see
		// whether a late mirror is possible. For this, we retrieve the
		// associated request to this undo/redo and see whether it can be
		// translated and then mirrored to the desired state.
		var assocReq = request.associatedRequest(this.log);
		
		// The state we're trying to mirror at corresponds to the target
		// vector, except the component of the issuing user is changed to
		// match the one from the associated request.
		var mirrorAt = targetVector.copy();
		mirrorAt[request.user] = assocReq.vector.get(request.user);
		
		if(this.reachable(mirrorAt))
		{			
			var translated = this.translate(assocReq, mirrorAt);
			var mirrorBy = targetVector.get(request.user) -
				mirrorAt.get(request.user);
			
			var mirrored = translated.mirror(mirrorBy);
			return mirrored;
		}
		
		// If mirrorAt is not reachable, we need to mirror earlier and then
		// perform a translation afterwards, which is attempted next.
	}
	
	for(var _user in this.vector)
	{
		// We now iterate through all users to see how we can translate
		// the request to the desired state.
		
		if(!_user.match(Vector.user_regex))
			continue;
		
		var user = parseInt(_user);
		
		// The request's issuing user is left out since it is not possible
		// to transform or fold a request along its own user.
		if(user == request.user)
			continue;
		
		// We can only transform against requests that have been issued
		// between the translated request's vector and the target vector.
		if(targetVector.get(user) <= request.vector.get(user))
			continue;
		
		// Fetch the last request by this user that contributed to the
		// current state vector.
		var lastRequest = this.requestByUser(user, targetVector.get(user) - 1);
		
		if(lastRequest instanceof UndoRequest || lastRequest instanceof RedoRequest)
		{
			// When the last request was an undo/redo request, we can try to
			// "fold" over it. By just skipping the do/undo or undo/redo pair,
			// we pretend that nothing has changed and increase the state
			// vector.
			
			var foldBy = targetVector.get(user) -
				lastRequest.associatedRequest(this.log).vector.get(user);
			
			if(targetVector.get(user) >= foldBy)
			{
				var foldAt = targetVector.incr(user, -foldBy);
				
				// We need to make sure that the state we're trying to
				// fold at is reachable and that the request we're translating
				// was issued before it.
				
				if(this.reachable(foldAt) && request.vector.causallyBefore(foldAt))
				{
					var translated = this.translate(request, foldAt);
					var folded = translated.fold(user, foldBy);
					
					return folded;
				}
			}
		}
		
		// If folding and mirroring is not possible, we can transform this
		// request against other users' requests that have contributed to
		// the current state vector.
		
		var transformAt = targetVector.incr(user, -1);
		if(transformAt.get(user) >= 0 && this.reachable(transformAt))
		{
			var lastRequest = this.requestByUser(user, transformAt.get(user));
			
			var r1 = this.translate(request, transformAt);
			var r2 = this.translate(lastRequest, transformAt);
			
			var cid_req;
			
			if(r1.operation.requiresCID)
			{
				// For the Insert operation, we need to check whether it is
				// possible to determine which operation is to be transformed.
				var cid = r1.operation.cid(r2.operation);
			
				if(!cid)
				{
					// When two requests insert text at the same position,
					// the transformation result is undefined. We therefore
					// need to perform some tricks to decide which request
					// has to be transformed against which.
					
					// The first try is to transform both requests to a
					// common successor before the transformation vector.
					var lcs = Vector.leastCommonSuccessor(request.vector,
						lastRequest.vector);
					
					if(this.reachable(lcs))
					{
						var r1t = this.translate(request, lcs);
						var r2t = this.translate(lastRequest, lcs);
						
						// We try to determine the CID at this vector, which
						// hopefully yields a result.
						var cidt = r1t.operation.cid(r2t.operation);
						
						if(cidt == r1t.operation)
							cid = r1.operation;
						else if(cidt == r2t.operation)
							cid = r2.operation;
					}
					
					if(!cid) {
						// If we arrived here, we couldn't decide for a CID,
						// so we take the last resort: use the user ID of the
						// requests to decide which request is to be
						// transformed. This behavior is specified in the
						// Infinote protocol.
						
						if(r1.user < r2.user)
							cid = r1.operation;
						if(r1.user > r2.user)
							cid = r2.operation;
					}
				}
				
				if(cid == r1.operation)
					cid_req = r1;
				if(cid == r2.operation)
					cid_req = r2;
			}
			
			return r1.transform(r2, cid_req);
		}
	}
	
	throw "Could not find a translation path";
};

/** Adds a request to the request queue.
 *  @param {Request} request The request to be queued.
 */
State.prototype.queue = function(request) {
	this.request_queue.push(request);
};

/** Checks whether a given request can be executed in the current state.
 *  @type Boolean
 */
State.prototype.canExecute = function(request) {
	if(request == undefined)
		return false;
	
	if(request instanceof UndoRequest || request instanceof RedoRequest) {
		return request.associatedRequest(this.log) != undefined;
	} else {
		return request.vector.causallyBefore(this.vector);
	}
};

/** Executes a request that is executable.
 *  @param {Request} [request] The request to be executed. If omitted, an
 *  executable request is picked from the request queue instead.
 *  @returns The request that has been executed, or undefined if no request
 *  has been executed.
 */
State.prototype.execute = function(request) {
	if(request == undefined)
	{
		// Pick an executable request from the queue.
		for(var index = 0; index < this.request_queue.length; index ++)
		{
			request = this.request_queue[index];
			if(this.canExecute(request))
			{
				this.request_queue.splice(index, 1);
				break;
			}
		}
	}
	
	if(!this.canExecute(request))
	{
		// Not executable yet - put it (back) in the queue.
		if(request != undefined)
			this.queue(request);
		
		return;
	}

	if(request.vector.get(request.user) < this.vector.get(request.user)) {
		// If the request has already been executed, skip it, but record it into the
		// log.
		// FIXME: this assumes the received request is already reversible
		this.log.push(request);
		return;
	}
	
	request = request.copy();
	
	if(request instanceof UndoRequest || request instanceof RedoRequest) {
		// For undo and redo requests, we change their vector to the vector
		// of the original request, but leave the issuing user's component
		// untouched.
		var assocReq = request.associatedRequest(this.log);
		var newVector = new Vector(assocReq.vector);
		newVector[request.user] = request.vector.get(request.user);
		request.vector = newVector;
	}
	
	var translated = this.translate(request, this.vector);
	
	if(request instanceof DoRequest && request.operation instanceof Operations.Delete) {
		// Since each request might have to be mirrored at some point, it
		// needs to be reversible. Delete requests are not reversible by
		// default, but we can make them reversible.
		this.log.push(request.makeReversible(translated, this));
	} else {
		this.log.push(request);
	}
	
	translated.execute(this);
	
	if(this.onexecute)
		this.onexecute(translated);
	
	return translated;
};

/** Executes all queued requests that are ready for execution. */
State.prototype.executeAll = function() {
	do {
		var executed = this.execute();
	} while(executed);
};

/** Determines whether a given state is reachable by translation.
 *  @param {Vector} vector
 *  @type Boolean
 */
State.prototype.reachable = function(vector) {
	var self = this;
	return this.vector.eachUser(function(u, v) {
		return self.reachableUser(vector, u);
	});
};

State.prototype.reachableUser = function(vector, user) {
	var n = vector.get(user);
	var firstRequest = this.firstRequestByUser(user);
	var firstRequestNumber = firstRequest ? firstRequest.vector.get(user) :
		this.vector.get(user);

	while(true) {
		if(n == firstRequestNumber)
			return true;
		
		var r = this.requestByUser(user, n - 1);
		
		if(r == undefined)
		{
			return false;
		}

		if(r instanceof DoRequest)
		{
			var w = r.vector;
			return w.incr(r.user).causallyBefore(vector);
		} else {
			var assocReq = r.associatedRequest(this.log);
			n = assocReq.vector.get(user);
		}
	}
};

/** Retrieve an user's request by its index.
 *  @param {Number} user
 *  @param {Number} index The number of the request to be returned
 */
State.prototype.requestByUser = function(user, getIndex) {
	for(var reqIndex in this.log)
	{
		var request = this.log[reqIndex];

		if(request.user == user && request.vector.get(user) == getIndex)
		{
			return request;
		}
	}
}

/** Retrieve the first request in the log that was issued by the given user.
 *  @param {Number} user
 */
State.prototype.firstRequestByUser = function(user) {
	var firstRequest;
	for(var reqIndex in this.log) {
		var request = this.log[reqIndex];

		if(request.user == user && (!firstRequest || firstRequest.vector.get(user) > request.vector.get(user) ))
		{
			firstRequest = request;
		}
	}

	return firstRequest;
}
/*
Copyright (c) 2009-2011 Simon Veith <simon@jinfinote.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

/** Creates a new Segment instance given a user ID and a string.
 *  @param {Number} user User ID
 *  @param {String} text Text
 *  @class Stores a chunk of text together with the user it was written by.
 */
function Segment(user, text) {
	this.user = user;
	this.text = text;
}

Segment.prototype.toString = function() {
	return this.text;
};

Segment.prototype.toHTML = function() {
	var text = this.text
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
	;
	
	return '<span class="segment user-' + this.user + '">' + text + '</span>';
};

/** Creates a copy of this segment.
 *  @returns {Segment} A copy of this segment.
 */
Segment.prototype.copy = function() {
	return new Segment(this.user, this.text)
};

/**
 * Creates a new Buffer instance from the given array of
 * segments.
 * @param {Array} [segments] The segments that this buffer should be
 * pre-filled with.
 * @class Holds multiple Segments and provides methods for modifying them at
 * a character level.
 */
function Buffer(segments) {
	this.segments = new Array();
	
	if(segments && segments.length)
	{
		for(var index in segments)
			this.segments.push(segments[index].copy());
	}
}

Buffer.prototype.toString = function() { return this.segments.join(""); };

Buffer.prototype.toHTML = function() {
	var result = '<span class="buffer">';
	for(var index = 0; index < this.segments.length; index++)
		result += this.segments[index].toHTML();
	result += '</span>';
	return result;
};

/** Creates a deep copy of this buffer.
 * @type Buffer
 */
Buffer.prototype.copy = function() {
	return this.slice(0);
};

/** Cleans up the buffer by removing empty segments and combining adjacent
 *  segments by the same user.
 */
Buffer.prototype.compact = function() {
	var segmentIndex = 0;
	while(segmentIndex < this.segments.length)
	{
		if(this.segments[segmentIndex].text.length == 0)
		{
			// This segment is empty, remove it.
			this.segments.splice(segmentIndex, 1);
			continue;
		} else if(segmentIndex < this.segments.length - 1 && 
			this.segments[segmentIndex].user == 
			this.segments[segmentIndex+1].user) {
			
			// Two consecutive segments are from the same user; merge them
			// into one.
			this.segments[segmentIndex].text +=
				this.segments[segmentIndex+1].text;
			
			this.segments.splice(segmentIndex+1, 1);
			continue;
		}
		
		segmentIndex += 1;
	}
};

/** Calculates the total number of characters contained in this buffer.
 * @returns Total character count in this buffer
 * @type Number
 */
Buffer.prototype.getLength = function() {
	var length = 0;
	for(var index = 0; index < this.segments.length; index++)
		length += this.segments[index].text.length;
	
	return length;
}

/** Extracts a deep copy of a range of characters in this buffer and returns
 *  it as a new Buffer object.
 *  @param {Number} begin Index of first character to return
 *  @param {Number} [end] Index of last character (exclusive). If not
 *  provided, defaults to the total length of the buffer.
 *  @returns New buffer containing the specified character range.
 *  @type Buffer
 */
Buffer.prototype.slice = function(begin, end) {
	var result = new Buffer();
	
	var segmentIndex = 0, segmentOffset = 0, sliceBegin = begin,
		sliceEnd = end;
	
	if(sliceEnd == undefined)
		sliceEnd = Number.MAX_VALUE;
	
	while(segmentIndex < this.segments.length && sliceEnd >= segmentOffset)
	{
		var segment = this.segments[segmentIndex];
		if(sliceBegin - segmentOffset < segment.text.length &&
			sliceEnd - segmentOffset > 0)
		{
			var newText = segment.text.slice(sliceBegin - segmentOffset,
				sliceEnd - segmentOffset);
			var newSegment = new Segment(segment.user, newText);
			result.segments.push(newSegment);
			
			sliceBegin += newText.length;
		}
		
		segmentOffset += segment.text.length;
		segmentIndex += 1;
	}
	
	result.compact();
	
	return result;
}

/**
 *  Like the Array "splice" method, this method allows for removing and
 *  inserting text in a buffer at a character level.
 *  @param {Number} index    The offset at which to begin inserting/removing
 *  @param {Number} [remove] Number of characters to remove
 *  @param {Buffer} [insert] Buffer to insert
 */
Buffer.prototype.splice = function(index, remove, insert) {
	if(index > this.getLength())
		throw "Buffer splice operation out of bounds";
	
	var segmentIndex = 0, segmentOffset = 0, spliceIndex = index,
		spliceCount = remove, spliceInsertOffset = undefined;
	while(segmentIndex < this.segments.length)
	{
		var segment = this.segments[segmentIndex];
		
		if(spliceIndex >= 0 && spliceIndex < segment.text.length)
		{
			// This segment is part of the region to splice.
			
			// Store the text that this splice operation removes to adjust the
			// splice offset correctly later on.
			var removedText = segment.text.slice(spliceIndex, spliceIndex +
				spliceCount);
			
			if(spliceIndex == 0) {
				// abcdefg
				// ^        We're splicing at the beginning of a segment
				
				if(spliceIndex + spliceCount < segment.text.length)
				{
					// abcdefg
					// ^---^    Remove a part at the beginning
					
					if(spliceInsertOffset == undefined)
						spliceInsertOffset = segmentIndex;
					
					segment.text = segment.text.slice(spliceIndex +
						spliceCount);
				} else {
					// abcdefg
					// ^-----^  Remove the entire segment
					
					if(spliceInsertOffset == undefined)
						spliceInsertOffset = segmentIndex;
					
					segment.text = "";
					this.segments.splice(segmentIndex, 1);
					segmentIndex -= 1;
				}
			} else {
				// abcdefg
				//   ^	    We're splicing inside a segment
			
				if(spliceInsertOffset == undefined)
					spliceInsertOffset = segmentIndex + 1;
				
				if(spliceIndex + spliceCount < segment.text.length)
				{
					// abcdefg
					//   ^--^   Remove a part in between
					
					// Note that if spliceCount == 0, this function only
					// splits the segment in two. This is necessary in case we
					// want to insert new segments later.
					
					var splicePost = new Segment(segment.user,
						segment.text.slice(spliceIndex + spliceCount));
					segment.text = segment.text.slice(0, spliceIndex);
					this.segments.splice(segmentIndex + 1, 0, splicePost);
				} else {
					// abcdefg
					//   ^---^  Remove a part at the end	
					
					segment.text = segment.text.slice(0, spliceIndex);
				}
			}
			
			spliceCount -= removedText.length;
		}
		
		if(spliceIndex < segment.text.length && spliceCount == 0)
		{
			// We have removed the specified amount of characters. No need to
			// continue this loop since nothing remains to be done.
			
			if(spliceInsertOffset == undefined)
				spliceInsertOffset = spliceIndex;
			
			break;
		}
		
		spliceIndex -= segment.text.length;
		
		segmentIndex += 1;
	}
	
	if(insert instanceof Buffer)
	{
		// If a buffer has been given, we insert copies of its segments at the
		// specified position.
		
		if(spliceInsertOffset == undefined)
			spliceInsertOffset = this.segments.length;
		
		for(var insertIndex = 0; insertIndex < insert.segments.length;
			insertIndex ++)
		{
			this.segments.splice(spliceInsertOffset + insertIndex, 0,
				insert.segments[insertIndex].copy());
		}
	}
	
	// Clean up since the splice operation might have fragmented some segments.
	this.compact();
}
