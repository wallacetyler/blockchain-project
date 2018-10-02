import hashlib as hl
import json


def hash_string_256(string):
    """Helper function that uses hashlib.sha256 and automatically converts the byte hash to normal printable chars with hexdigest()

    Arguments:
        :string: Any string but for our purposes a block turned into a string
    """
    return hl.sha256(string).hexdigest()


def hash_block(block):
    """Hashes a block and returns a string representation of it.

    Arguments:
        :block: The block that should be hashed.
    """
    # Creates a dictionary version of the block so that it can be processed by json.
    # Must use '.copy()' to create a new copy of the dictionary every time as not to disturb
    # the reference.  
    hashable_block = block.__dict__.copy()

    # Access the list of transaction objects in the given block and convert to ordered dictionaries
    hashable_block['transactions'] = [tx.to_ordered_dict() for tx in hashable_block['transactions']]

    # hashlib.sha256() creates a 64 character hash on a string
    # json.dumps() creates a json string from an object using sort_keys to
    # make sure the keys are always in the same order since it isn't guaranteed
    # with dictionaries
    # encode() encodes the json string as 'utf-8' which is needed for sha256
    return hash_string_256(json.dumps(hashable_block, sort_keys = True).encode())
