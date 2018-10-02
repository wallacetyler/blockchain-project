from functools import reduce
import hashlib as hl
import json
import requests

# Imports from our hash_util.py file. 
from utility.hash_util import hash_block 
from utility.verification import Verification

from block import Block
from transaction import Transaction
from wallet import Wallet

# The mining reward (reward for creating new block)
MINING_REWARD = 10

print(__name__)

class Blockchain:
    """ Manages the chain of blocks as well as open transactions and 
    managing the node which it is running on.

    Attributes:
        :chain: The list of block.
        :open_transactions (private): The list of open transactions.
        :hosting_node: The connected node
    """

    def __init__(self, public_key, node_id):
        # Creating the gensis block by creating a Block object
        genesis_block = Block(0, '', [], 100, 0)
        # Initializing our (empty) blockchain list
        self.chain = [genesis_block]
        # Initializing our list of pending transactions (is a private attribute)
        self.__open_transactions = []
        # Set hosting_node id
        self.public_key = public_key
        # Create a set because it can only hold unique values
        self.__peer_nodes = set()
        # Set node_id to the node_id received as an argument
        self.node_id = node_id
        # Switch to see if we need to resolve any conflicts
        self.resolve_conflicts = False
        # Load any saved data from txt file
        self.load_data()

    # Turns the chain attribute into a property with a getter (method below)
    # and a setter (@chain.setter)
    @property
    def chain(self):
        return self.__chain[:]

    # Setter for chain property
    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        """ Returns a copy of the open transaction list. """
        return self.__open_transactions[:]

    def load_data(self):
        """ Initialize blockchain = open transactions data from file. """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                # Tells the function to use globally defined variables do not create new local ones
                global blockchain
                global open_transactions
                # Use json lib to convert the json string back into python object
                # being sure to grab everything except the '\n' char using range selector [:-1]
                # json.loads deserielizes a string in json format and gives back a python obj
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                # IMPORTANT when we call valid_proof() we convert the list of transactions to 
                #           a string and this adds '[OrderedDict()]' at the start of that list
                #           therefor we must loop through the blockchain read in from file and 
                #           adjust transactions to be an ordered dict using a list comp in the 
                #           transactions portion
                # Loop to create block objects for each block in our saved file
                for block in blockchain:
                    converted_tx = [Transaction(
                        tx['sender'], 
                        tx['recipient'], 
                        tx['signature'], 
                        tx['amount']) for tx in block['transactions']]
                    updated_block = Block(
                        block['index'], 
                        block['previous_hash'], 
                        converted_tx,
                        block['proof'],
                        block['timestamp']
                    )
                    # Append the newly updated block to our updated blockchain list
                    updated_blockchain.append(updated_block)

                # Update the entire blockchain
                self.chain = updated_blockchain

                # Use json lib to convert the json string back into python object
                # json.loads deserielizes a string in json format and gives back a python obj
                open_transactions = json.loads(file_content[1][:-1])
                updated_transactions = []
                # IMPORTANT open_transactions will be unordered dict therefore we must convert
                #           newly read in open_transactions to an OrderedDict
                for tx in open_transactions:
                    # Losing the ordering but we will fix when needed
                    updated_transaction = Transaction(
                        tx['sender'], 
                        tx['recipient'], 
                        tx['signature'], 
                        tx['amount']
                    )
                    # Append the newly updated transaction to our updated transactions list
                    updated_transactions.append(updated_transaction)
                # Update the entire list of open_transactions now that they have been converted to an OrderedDict
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError): 
            print('Handled exception...')


    def save_data(self):
        """ Save blockchain + open_transactions snapshot to a file """
        try:
            """Writes our blockchain and open transactions to a txt file in json format"""
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                # Create a list of dictionaries based on our block objects to dump using json and convert each transaction in a block to an dictionary
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')


    def proof_of_work(self):
        """Increments the proof of work number until a valid proof is found"""
        # Grabs the last block in the blockchain
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        # Try different PoW numbers and return the first valid one
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof


    def get_balance(self, sender=None):
        """Calculate and return the balance for a participant.
        
        Arguments:
            :participant: The person for whom to calculate the balance.
        """

        if sender == None:
            # Check to see if we have a public key yet
            if self.public_key == None:
                return None
            participant = self.public_key
        else:
            participant = sender

        # Use nested list comprehensions to obtain a list of transaction amounts
        # if the sender is a participant, the second list comp is used to go through
        # each block in the blockchain.
        # This is a list of transaction amounts that are currently in the blockchain
        # for the given participant.
        tx_sender = [[tx.amount for tx in block.transactions
            if tx.sender == participant] for block in self.__chain]
        # Use nested list comprehension to get a list of transaction amounts that are
        # currently in open_transactions for the participant
        open_tx_sender = [tx.amount for tx in self.__open_transactions 
            if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        # Use reduce to sum list of open transactions down to one value
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)
        # This fetches received coin amounts of transactions that were already in
        # the blockchain

        # We ignore open transactions here because you shouldn't be able to spend
        # coin that is tied up in open transactions
        tx_recipient = [[tx.amount for tx in block.transactions   
            if tx.recipient == participant] for block in self.__chain]
        # Use reduce to sum list of open transactions down to one value
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)
        return amount_received - amount_sent


    def get_last_blockchain_value(self):
        """" Returns the last value of the current blockchain. """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]



    def add_transaction(self, 
                        recipient, 
                        sender, 
                        signature, 
                        amount = 1.0, 
                        is_receiving = False):
        """ Append a new value as well as the last blockchain value to the blockchain list

        Arguments:
            :sender: The sender of the coins
            :recipient: The recipient of the coins
            :amount: The amount of coins sent (default of 1.0)
        """

        # Create new transaction object
        transaction = Transaction(sender, recipient, signature, amount)
        # Verify transaction
        if Verification.verify_transaction(transaction, self.get_balance):
            # If successful append to open transactions
            self.__open_transactions.append(transaction)
            # Add anyone included in the transaction to the set of participants
            # remember that sets are unique
            self.save_data()
            if not is_receiving:
                # Loop through each node in our node set
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, 
                                                 json={
                                                    'sender': sender, 
                                                    'recipient': recipient, 
                                                    'amount': amount, 
                                                    'signature': signature
                                                 })
                        if (response.status_code == 400 or 
                            response.status_code == 500):
                            print('Transaction declined, needs resolving')
                            return False
                    # If we cant find that specific node, continue to the next node
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False


    def mine_block(self):
        """ Create a new block and add open transactions to it. """
        if self.public_key == None:
            return None
        # Fetch the currently last block of the blockchain
        last_block = self.__chain[-1]
        # Hash the list block
        hashed_block = hash_block(last_block)
        # Get the NONCE that uses the outstanding transactions and the previous
        # block that leads to a valid hash
        proof = self.proof_of_work()

        # Create reward transaction using OrderedDict which uses a list of tuples
        # to create ('key', value) pairs. Pass in a empty string for the signature
        # since we never verify it using a signature
        reward_transaction = Transaction('MINING', self.public_key, '', MINING_REWARD)

        # Copy transaction instead of manupulating the original open_transactions
        # This ensures that if for some reason the mining should fail, we don't
        # have a reward sitting in the open transaction
        copied_transactions = self.__open_transactions[:]
        # Verify all transactions before appending the reward transaction
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)

        # Creating new block object
        # Proof is the NONCE that leads to a valid hash of the newly created block
        # that it's in.
        block = Block(
            len(self.__chain), 
            hashed_block, 
            copied_transactions, 
            proof
        )
        # Add the newly created block to the blockchain
        self.__chain.append(block)
        # Update open transactions to be emtpy
        self.__open_transactions = []
        self.save_data()

        # Now broadcast to peer nodes
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            # Convert block object to dictionary
            converted_block['transactions'] = [tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json = {'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block


    def add_block(self, block):
        """ Add a block which was received via broadcasting to the 
        local blockchain.
        """
        # Extract transaction data from received block and create a list of these transactions
        transactions = [Transaction(
            tx['sender'], 
            tx['recipient'], 
            tx['signature'], 
            tx['amount']) for tx in block['transactions']]
        # Check to see if transaction data form receieved block in valid
        # Use 'transactions[:-1]' to grab every transaction except for the last one to make sure the reward
        # transaction is not included since it wasn't part of calculating the proof of work.
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        # Safe to add block if passes all checks
        # Convert block from dictionary to a new block object
        converted_block = Block(
            block['index'], 
            block['previous_hash'], 
            transactions, 
            block['proof'], 
            block['timestamp'])
        # Append the block to local blockchain
        self.__chain.append(converted_block)
        # Update open transactions
        # Create a copy of the open transactions on the node
        stored_transactions = self.__open_transactions[:]
        # For every incoming transaction check to see if it is a part of local open transactions
        for itx in block['transactions']:
            for opentx in stored_transactions:
                # Checking all variables of local transactions are equal to transactions, if so then it is the same transaction
                if opentx.sender == (itx['sender'] and 
                        opentx.recipient == itx['recipient'] and 
                        opentx.amount == itx['amount'] and 
                        opentx.signature == itx['signature']):
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed.')

        self.save_data()
        return True


    def resolve(self):
        """Resolve conflicts. Essentially just checking for longer/shorter chains. 
        Will replace the local one with a longer valid chain.
        """
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                # Get response from the 'get' chain
                response = requests.get(url)
                # The response includes the blockchain of that node, store in node_Chain
                node_chain = response.json()
                # Extract from dictionary (since it is obtained from json) and create a list of 
                # block objects. Using a nested list comp to also update the list of transactions
                # to transaction objects.
                node_chain = [Block(block['index'], block['previous_hash'], 
                    [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']], 
                        block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                # If the peer node blockchain is longer than ours then we want to use its blockchain 
                # rather than our out of date local one
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            # If you can not reach a specific node just continue
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        # Replace our chain with the longest valid chain from the peer nodes surveyed
        self.chain = winner_chain
        # If we need to update our chain, then we can assume our open transactions might be 
        # wrong and therefore we must clear them. 
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace


    def add_peer_node(self, node):
        """"Adds a new node to the peer node set.
        
        Arguments:
            :node: The node URL which should be added
        """
        self.__peer_nodes.add(node)
        self.save_data()


    def remove_peer_nodes(self, node):
        """"Removes a node from the peer node set.
        
        Arguments:
            :node: The node URL which should be added
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    
    def get_peer_nodes(self):
        """Returns a list of all connected peer nodes."""
        return list(self.__peer_nodes)