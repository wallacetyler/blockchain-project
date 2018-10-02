from time import time
from utility.printable import Printable

class Block(Printable):
    """ A signle block of our blockchain.

    Attributes:
        :index: The index of this block.
        :previous_hash: The hash of the previous block.
        :timestamp: The timestamp of the block
        :transactions: A list of transactions which are included in the block.
        :proof: The proof of work number that produced the block.
    """

    # Constructor
    def __init__(self, index, previous_hash, transactions, proof, timestamp=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time() if timestamp is None else timestamp
        self.transactions = transactions
        self.proof = proof
