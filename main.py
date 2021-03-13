import json
from flask import Flask, jsonify, request
from web3 import Web3, HTTPProvider
from web3.eth import Account
import os

# not sure if dotenv will work in google cloud (can't pip install it)
try :
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

app = Flask(__name__)

print('starting..')
web3 = Web3(HTTPProvider(os.getenv('HTTPProvider')))

# do this a a test of connectivity
print('block', web3.eth.blockNumber)

GAP = int(60/4) # Kovan updates every 4 seconds, let's wait for a minute (60)

compiler_contract_path = '../build/contracts/GameOfLife.json'
compiler_contract_path = 'GameOfLife.json'

deployed_contract_address = os.getenv('contract_address')

contract_json = json.load(open(compiler_contract_path))
contract_abi = contract_json['abi']

deployed_contract_address=Web3.toChecksumAddress(deployed_contract_address)
print('deployed contract address',deployed_contract_address)
contract = web3.eth.contract(
    address=deployed_contract_address, 
    abi=contract_abi,
    )

rows = 32
cols = 32

cells = [0 for x in range(rows*cols)]
blocks = 0


# use to this to print the network name to the web app
network_name = os.getenv('network_name')
print('network name',network_name)


@app.route('/<cmd>', methods=['GET','POST','OPTIONS'])
def gameoflife(cmd):

    # just extract the full path as the decorator's dont work in a google cloud environment
    cmd = request.path
    print("cmd",cmd)
    if cmd =='/data':
        return get_data()
    elif cmd in ['/step','/setcells']:
        return do_command(cmd)
    else:
        return jsonify({'unknown cmd':cmd})


def do_command(cmd):

    # not sure if this particular bit is needed, but it referenced in the google cloud function docs
    if request.method == 'OPTIONS':
    # Allows GET requests from any origin with the Content-Type
    # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return jsonify({'status':'ok'}), 204, headers

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    if cmd in ['/step','/setcells']:
        pass
    else :
        return jsonify({"unknown cmd":cmd})
        

    private_key = os.getenv('private_key')
    print('private_key',private_key)

    acct = Account.from_key(private_key)
    caller_address = acct.address

    print('caller_address',caller_address)

    nonce = web3.eth.getTransactionCount(caller_address)
    chainId = int(os.getenv('chain_id'))

    gwei = 1_000_000_000
    gasPrice = 1 * gwei

    caller_balance0 = web3.eth.get_balance(caller_address)

    gasPrice = Web3.toWei(1, 'gwei')

    myblock = contract.functions.getMyBlock().call()

    print('myblock',myblock)
    
    if 'setcells' in cmd:
        print("setcells")
    
        data = request.data

        print('type',type(data))
        print('data',data)
        # convert from text to dict 
        try :
            cells = json.loads(data)
            print("cells",cells)
        except Exception as e:
            return jsonify({'status':str(e)})

        # convert array into 4 x 256 bit elements
        try:
            cell4 = generate_cell4(cells['cells'])
            print("cell4",cell4)
        except Exception as e:
            return jsonify({'code':str(e)})


        txn = contract.functions.setCells(cell4[0],cell4[1],cell4[2],cell4[3]).buildTransaction(
            {
                'chainId' : chainId,
                'nonce': nonce,
                'gasPrice': gasPrice,
            }
        )
    else :
        print("starting step..")

        # check when the last step was done
        # compare to current block
        # only execute the step if the time is greater than one minute
        myblock = contract.functions.getMyBlock().call()
        current = web3.eth.blockNumber

        target  = myblock + GAP
        print(f"current {current} target {target}")
        
        if current < target :
            return jsonify({'code':f'current block is {current}, skipping until block {target}'})    

        txn = contract.functions.step().buildTransaction(
            {
                'chainId' : chainId,
                'nonce': nonce,
                'gasPrice': gasPrice,
            }
        )
    print('txn',txn)

    
    signed_txn = web3.eth.account.sign_transaction(
        txn,
        private_key=private_key
    )

    try: 
        result = web3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print('result',result)
        txn['status'] = 'ok'
    except Exception as e:
        print(type(e))
        print(e)
        txn = {'status':str(e)}

    response = txn

    caller_balance1 = web3.eth.get_balance(caller_address)

    
    response['block'] = web3.eth.blockNumber
    response['balance_before'] = caller_balance0
    response['balance_after'] = caller_balance1
    response['cost'] = caller_balance0 - caller_balance1
    response['myblock'] = contract.functions.getMyBlock().call()

    return jsonify(response), 200 , headers



# take an array of 4 x uint256 and convert into a linear array of 1s and 0s.
def generate_cells(cell4):
    cells = [0 for x in range(rows*cols)]
    index = 0
    for row in range(rows):
        for col in range(cols):
            pos = (col + row*cols) % (rows*cols)
            i = int(pos / 256)
            j = pos % 256
            #print(row,col,pos,i,j,cells[i])
            if (cell4[i] >> j) & 0x01:
                cells[index] = 1
            else:
                cells[index] = 0

            index += 1
    return cells

# take an array of 1s and 0s and create an 4 x uint256 array
def generate_cell4(cells):
    cell4 = [0,0,0,0]
    
    for row in range(rows):
        for col in range(cols):
            pos = (col + row*cols) % (rows*cols)
            i = int(pos / 256)
            j = pos % 256
            if cells[pos] == 1:
                cell4[i] |= ( 1 << j)

    return cell4

def get_data():

    
    # not sure if this particular bit is needed, but it referenced in the google cloud function docs
    if request.method == 'OPTIONS':
    # Allows GET requests from any origin with the Content-Type
    # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    cell4 = contract.functions.getCells().call()
    print("cells ", cell4)

    cells = generate_cells(cell4)

    private_key = os.getenv('private_key')
    print('private_key',private_key)

    acct = Account.from_key(private_key)
    caller_address = acct.address
    caller_balance = web3.eth.get_balance(caller_address)
    
    # convert balance into ether..
    caller_balance = str(web3.fromWei(caller_balance,'ether'))
    
    block = web3.eth.blockNumber
    myblock = contract.functions.getMyBlock().call()

    response = {
        'status'          : 'ok',
        'network'         : network_name,
        'block'           : block,
        'myblock'         : myblock,
        'caller_address'  : caller_address,
        'caller_balance'  :  caller_balance,
        'contract_address': deployed_contract_address,
        'contract_balance' : web3.eth.get_balance(deployed_contract_address),
        'target'            : myblock + GAP,
        'rows' : rows,
        'cols' : cols,
        'cells' : cells
        
    }
    return jsonify(response), 200 , headers
