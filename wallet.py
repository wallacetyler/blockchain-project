# This package helps with generating keys
from Crypto.PublicKey import RSA
# This package helps generate a signature
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

import Crypto.Random
import binascii

class Wallet:
    """ Create, load, and hold private and public keys. Handles transaction
    signing and verification. 
    """

    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id

    def create_keys(self):
        """ Create a new pair of private and public keys. """
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key
        try:
            # Store keys to text file (obviously not advisable for a real cryptocurrency)
            with open('wallet.txt', mode='w') as f:
                f.write(public_key)
                f.write('\n')
                f.write(private_key)
        except (IOError, IndexError):
            print('Saving wallet failed...')

    def load_keys(self):
        """ Loads the keys from the wallet.txt file into memory. """
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode='r') as f:
                keys = f.readlines()
                # Get both keys from file, avoid getting the '\n' character in the first line
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError, IndexError):
            print('Loading wallet failed...')
            return False

    def save_keys(self):
        """ Saves the keys to the wallet.txt file. """
        # Make sure we have keys to save
        if self.public_key != None and self.private_key != None:
            try:
                # Store keys to text file (obviously not advisable for a real cryptocurrency)
                with open('wallet-{}.txt'.format(self.node_id), mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True
            except (IOError, IndexError):
                print('Saving wallet failed...')
                return False

    def generate_keys(self):
        """ Generate a new pair of private and public key. """
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()
        # Return a string version of our public and private keys as a tuple
        return (
            binascii
            .hexlify(private_key.exportKey(format = 'DER'))
            .decode('ascii'), 
            binascii.hexlify(public_key.exportKey(format = 'DER'))
            .decode('ascii')
        )

    def sign_transaction(self, sender, recipient, amount):
        """ Sign a transaction and return the signature. 
        
        Arguments:
            :sender: The sender of the transaction.
            :recipient: The recipient of the transaction.
            :amount: The amount of the transaction.
        """
        signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        # Create a payload hash converting from string back to binary values
        h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode('utf8'))
        # Generate a signature using our hash payload
        signature = signer.sign(h)
        # Return signature as a string
        return binascii.hexlify(signature).decode('ascii')

    # Set to static method since we never access the class
    @staticmethod
    def verify_transaction(transaction):
        """Verify the signature of a transaction.

        Arguments:
            :transaction: The transaction that should be verified.
        """
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        # Create a payload hash converting from string back to binary values
        h = SHA256.new((str(transaction.sender) + str(transaction.recipient) + 
                        str(transaction.amount)).encode('utf8'))
        # Return binary version of verification
        return verifier.verify(h, binascii.unhexlify(transaction.signature))