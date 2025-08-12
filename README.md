# Base Domain Register

An asynchronous Python tool for registering `.base.eth` domains on the Base network using multiple wallet accounts.

## Features

- **Asynchronous Operations**: Built with `asyncio` and `aiohttp` for high performance
- **Multi-Wallet Support**: Process multiple wallets from seed phrases or private keys
- **Smart Domain Generation**: Random domain name generation with name combinations
- **Gas Optimization**: Automatic gas estimation and priority fee calculation
- **Concurrent Processing**: Configurable thread limits for parallel domain registration
- **Error Handling**: Robust error handling with detailed logging

## Installation

0. Install **python 3.11+** from https://www.python.org/downloads/
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit the configuration constants in `main.py`:

```python
CHAIN_NAME = "base"
CHAIN_ID = 8453
RPC_ENDPOINT = "https://base.llamarpc.com"
MAX_REGISTER_DOMAIN = 4      # Maximum domains per wallet
MAX_THREAD = 1               # Maximum concurrent operations
```

## Usage

### 1. Prepare Wallet Data

Create a `wallet_data.txt` file with your wallet information:

```
# Seed phrases (12+ words)
word1 word2 word3 ... word12
another seed phrase here

# Or private keys
0x1234567890abcdef...
0xabcdef1234567890...

# Or seed phrases (12+ words) and private keys (mix)
0x1234567890abcdef...
word1 word2 word3 ... word12
0xabcdef1234567890...
```

### 2. Run the Script

```bash
python main.py
```

## How It Works

### Wallet Processing
- **Seed Phrases**: Automatically derives private keys using BIP32/BIP44 standards
- **Private Keys**: Direct usage for immediate processing
- **Address Generation**: Creates checksum addresses for each wallet

### Domain Registration Process
1. **Domain Check**: Verifies current domain count for each wallet
2. **Name Generation**: Creates random domain names using first/last name combinations
3. **Availability Check**: Verifies domain availability on-chain
4. **Transaction Building**: Constructs registration transaction with resolver data
5. **Gas Estimation**: Calculates optimal gas parameters
6. **Transaction Signing**: Signs and broadcasts transaction
7. **Result Logging**: Records success/failure with transaction hash

### Asynchronous Architecture
- **HTTP Sessions**: Reusable aiohttp sessions for API calls
- **Web3 Integration**: AsyncWeb3 for non-blocking blockchain operations
- **Concurrency Control**: Semaphore-based thread limiting
- **Parallel Processing**: Multiple wallets processed simultaneously

## Class Structure

### `AggregateWallet`
Handles wallet key derivation and management:
- `aggregate_seed()`: Derives keys from seed phrases
- `aggregate_private_key()`: Processes direct private keys
- `get_private_key()`: Universal key extraction method

### `AsyncBaseDomainRegister`
Main domain registration class:
- `get_all_domains()`: Fetches existing domains via API
- `check_available_domain()`: On-chain availability verification
- `build_tx()`: Transaction construction with resolver data
- `sign_tx()`: Transaction signing and broadcasting
- `buy_base_domain()`: Complete registration workflow

## API Endpoints

- **Base Names API**: `https://www.base.org/api/basenames/getUsernames`
- **RPC Endpoint**: `https://base.llamarpc.com`

## Smart Contracts

- **Registrar Controller**: `0x4cCb0BB02FCABA27e82a56646E81d8c5bC4119a5`
- **L2 Resolver**: `0x4cCb0BB02FCABA27e82a56646E81d8c5bC4119a5`

## Dependencies

- `web3~=7.8.0`: Ethereum Web3 library
- `aiohttp~=3.9.1`: Asynchronous HTTP client
- `eth-account~=0.13.7`: Ethereum account management
- `mnemonic~=0.21`: BIP39 mnemonic handling
- `bip32utils~=0.3.post4`: BIP32 key derivation
- `eth-keys~=0.6.1`: Ethereum key operations
- `loguru~=0.7.3`: Advanced logging

## Error Handling

The system includes comprehensive error handling:
- Invalid wallet data detection
- Network connection failures
- Transaction failures
- Gas estimation errors
- Domain availability issues

## Performance Features

- **Asynchronous I/O**: Non-blocking operations
- **Connection Pooling**: HTTP session reuse
- **Batch Processing**: Multiple wallets processed in parallel
- **Resource Management**: Automatic cleanup of connections

## Security Features

- **Private Key Protection**: Keys never logged or exposed
- **Secure Derivation**: BIP32/BIP44 compliant key generation
- **Transaction Validation**: On-chain verification of operations

## Logging

Comprehensive logging using Loguru:
- Success/failure notifications
- Transaction hashes
- Error details
- Performance metrics

## Example Output

```
[INFO] Loading: 3 wallet. Run script of 1 thread...
[SUCCESS] [0x1234...] Success buy domain: johnsmith1990.base.eth | Hash: 0xabcd...
[SUCCESS] [0x5678...] Success buy domain: janedoe1985.base.eth | Hash: 0xefgh...
[INFO] Registration completed. Successful: 2, Failed: 0
```

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and legitimate use only. 