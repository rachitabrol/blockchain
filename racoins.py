import datetime
import json
import hashlib
from flask import jsonify ,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    
    def __init__(self):
        self.chain=[]
        self.transactions = []
        self.create_block(proof=1,previous_hash=0)
        self.nodes = set()
        
    def create_block(self,proof,previous_hash):
        block={'index':len(self.chain)+1,
               'timestamp':datetime.datetime.now(),
               'proof':proof,
               'previous_hash':previous_hash,
               'transactions':self.transactions}
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            hash_operation=hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1
        return new_proof


    def hash_bl (self,block):
        encode_block=json.dumps(block,sort_keys=True,indent=1,default=str).encode()
        hash_operation=hashlib.sha256(encode_block).hexdigest()
        return hash_operation
    
    def is_chain_valid(self,chain):
        previous_block=chain[0]
        block_index=1
        while block_index < len(chain):
            block=chain[block_index]
            if block['previous_hash'] != self.hash_bl(previous_block):
                return False
            previous_proof=previous_block['proof']
            proof=block['proof']
            hash_operation=hashlib.sha256(str(proof**2-previous_proof**2).encode()).hexdigest()
            if(hash_operation[:4]!='0000'):
                return False
            previous_block=block
            block_index+=1
        return True
    def add_transaction(self,sender,reciever,amount):
        self.transactions.append({'sender':sender,
                                  'reciever':reciever,
                                  'amount':amount})
        previous_block=self.get_previous_block()
        return previous_block['index']+1
    def add_node(self,address):

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code ==200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length=length
                    longest_chain=chain
        if longest_chain:
            self.chain=longest_chain
            return True
        return False
            
        
#creating_web_app
from flask import Flask
app = Flask (__name__)

#creating blockchain
blockchain= Blockchain()

#creating address for the node 5000 port
node_address= str(uuid4()).replace('-','')

#mining a block
@app.route('/mine_block',methods=['GET'])
def mine_block():
    previous_block=blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof=blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash_bl(previous_block)
    blockchain.add_transaction(sender = node_address, reciever='badelin', amount=1)
    block= blockchain.create_block(proof, previous_hash)
    response= {'message':'congrats on mining a block successfully',
               'index':block['index'],
               'timestamp':block['timestamp'],
               'proof':block['proof'],
               'previous_hash':block['previous_hash'],
               'transactions':block['transactions']
               }
    return jsonify(response), 200

#getting full blockchain
@app.route('/get_chain',methods=['GET'])
def get_chain():
    response={'chain':blockchain.chain,
              'length':len(blockchain.chain)}
    return jsonify(response), 200
#adding transaction to blockchain
@app.route('/add_trasaction',methods=['POST'])
def add_trasaction():
    json = request.get_json()
    transaction_keys = ['sender','reciever','amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing.',400
    index = blockchain.add_transaction(json['sender'], json['reciever'], json['amount'])
    response = {'message' : f'This Transaction will be added to block {index}'}
    return jsonify(response),201

#connecting nodes
@app.route('/connect_node',methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No Node",400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message':'All the nodes are connected',
                'Total nodes':list(blockchain.nodes)}
    return jsonify(response),201

#check if chain is valid 
@app.route('/is_valid',methods=['GET'])
def is_valid():
    is_valid= blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message':'The chain is Valid'}
    else:
        response= {'message':'The Blockchain is not valid'}
    return jsonify(response),200
    

#replacing the chain  by the longest chain
@app.route('/replace_chain',methods=['GET'])
def replace_chain():
    is_chain_replaced= blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message':'The nodes had different chains. So chain  was replaced by the longest one',
                    'new_chain':blockchain.chain}
    else:
        response= {'message':'The chain is the largest one',
                   'Actual Chain':blockchain.chain}
    return jsonify(response),200


#running the app
app.run(host='0.0.0.0',port=5000)            
            
        
        
    