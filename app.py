# Import the libraries.

from flask import Flask, render_template, jsonify, request
import datetime
from hashlib import sha256
import json


app = Flask(__name__)  # Initialize Flask application.

# Class implementation for Block.


class Block:
    """
    Block representing a single block in a blockchain.

    Attributes:
        index (int): Block's unique index within the chain.
        data (str): Data stored in the block.
        timestamp (str): ISO 8601 timestamp of block creation.
        previous_hash (str): Hash of the previous block.
        nonce (int): Nonce used for Proof-of-Work (PoW).
        hash (str): Calculated SHA-256 hash of the block.
        is_valid (bool): Flag indicating block validity.
    """

    def __init__(self, index, data, timestamp, previous_hash):
        self.index = index  # Index of the block.
        self.data = data  # Data of the block.
        self.timestamp = (
            timestamp.isoformat()
            if isinstance(timestamp, datetime.datetime)
            else timestamp
        )  # Timestamp of the block
        self.previous_hash = previous_hash  # Hash of the previous block.
        self.nonce = 0  # Nonce of the block
        self.hash = self.proof_of_work(Blockchain.difficulty)
        self.is_valid = True  # Initially, every block is valid

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def proof_of_work(self, difficulty):
        self.nonce = 0
        computed_hash = self.compute_hash()
        while not computed_hash.startswith("0" * difficulty):
            self.nonce += 1
            computed_hash = self.compute_hash()
        return computed_hash

    def update_data(self, new_data):
        self.data = new_data
        # Invalidate the hash by recalculating without trying to meet the difficulty
        self.hash = (
            self.compute_hash()
        )  # This now just recalculates the hash normally without PoW
        self.is_valid = False  # Explicitly mark as invalid


class Blockchain:
    difficulty = 3

    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "Genesis Block", datetime.datetime.now(), "0")
        genesis_block.hash = genesis_block.proof_of_work(Blockchain.difficulty)
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        new_block = Block(
            len(self.chain), data, datetime.datetime.now(), self.last_block.hash
        )
        new_block.hash = new_block.proof_of_work(Blockchain.difficulty)
        new_block.is_valid = self.is_block_valid(new_block)  # Set initial validity
        self.chain.append(new_block)

    def is_block_valid(self, block):
        if block.index == 0:
            return (
                block.hash.startswith("0" * self.difficulty)
                and block.previous_hash == "0"
                and block.is_valid
            )
        else:
            previous_block = self.chain[block.index - 1]
            return (
                block.hash.startswith("0" * self.difficulty)
                and block.previous_hash == previous_block.hash
                and block.is_valid
            )

    def is_chain_valid(self):
        for block in self.chain:
            if not self.is_block_valid(block):
                return False
        return True


blockchain = Blockchain()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chain", methods=["GET"])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        block_info = block.__dict__
        block_info["is_valid"] = blockchain.is_block_valid(
            block
        )  # Ensure this function exists and is accurate
        chain_data.append(block_info)
    return jsonify(length=len(chain_data), chain=chain_data)


@app.route("/mine", methods=["POST"])
def mine():
    data = request.json["data"]
    blockchain.add_block(data)
    return jsonify(blockchain.last_block.__dict__)


@app.route("/update_data", methods=["POST"])
def update_data():
    block_index = int(request.json["index"])
    new_data = request.json["data"]
    if block_index == 0:
        return jsonify({"error": "Modification of the Genesis Block is not allowed"})
    if block_index < len(blockchain.chain):
        if new_data != blockchain.chain[block_index].data:
            # Update and mark the block as invalid
            blockchain.chain[block_index].update_data(new_data)
            # Mark all subsequent blocks as invalid as well
            for i in range(block_index + 1, len(blockchain.chain)):
                blockchain.chain[i].is_valid = False
            return jsonify(
                {
                    "success": True,
                    "message": "Block and subsequent blocks marked as invalid",
                }
            )
        else:
            return jsonify({"error": "No change in data"})
    return jsonify({"error": "Index out of range"}), 400


if __name__ == "__main__":
    app.run(debug=True)
