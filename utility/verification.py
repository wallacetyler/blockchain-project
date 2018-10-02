""" Provides verification helper methods. """

from utility.hash_util import hash_string_256, hash_block
from wallet import Wallet


class Verification:
    """ A helper class which offers various statis and class-based verification methods. """
    # Using staticmethod decorator since it isn't accessing anything from inside the class
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        """ Generates a valid new hashes by checking to see if it fits our difficulty criteria.
        In our case its two leading 0's. Ideally this would get harder with time.

        Arguments:
            :transactions: Transactions of new block for which the proof
            is created
            :last_hash: Hash of previous block in the blockchain, will be
            stored in the current block
            :proof: Proof number
        """
        # Hash not the same as the previous hash since index is not considered.
        # The string is encoded into 'utf-8' characters.
        # IMPORTANT this converts transactions, which is an ordered dict. This means it is 
        #           is converted into a string with '[OrderedDict()]' at the start of the
        #           the list of transactions
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        # Calculate hash of new guess using custom function defined in hash_util
        guess_hash = hash_string_256(guess)
        # Only a hash (which is based on the above inputs) which starts with two 00's is a valid hash.
        # This is the hash difficulty and can be changed to be more difficult.
        return guess_hash[0:2] == '00'


    # Using classmethod decorator since the verifychain() method does access the class but doesn't 
    # need an instance
    @classmethod
    def verify_chain(cls, blockchain):
        """ Verify the current blockchain and return True if it's valid,
        false otherwise. 
        """
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            # Excluding reward transactions since the reward transaction is included
            # after the proof of work
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print('Proof of work is invalid')
                return False
        return True


    # Method only working with the inputs its given
    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds = True):
        """ Verify a transaction by checking whether the sender has sufficent balance 
        
        Arguments:
            :transaction: The transaction that should be verified
            :get_balance:
            :check_funds:
        """
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)


    # Method needs access to the class but doesn't need an instance
    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        """ Verified all open transactions. """
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])