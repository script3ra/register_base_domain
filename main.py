import random
import json
from typing import Any, List, Optional, Tuple, Dict
import asyncio
import aiohttp
from eth_account.messages import encode_typed_data
from eth_account.signers.local import LocalAccount
from eth_typing import ChecksumAddress
from web3 import Web3, Account, AsyncWeb3
from ens.utils import normal_name_to_hash
from eth_account import Account
from mnemonic import Mnemonic
from bip32utils import BIP32Key, BIP32_HARDEN
from eth_keys import keys

from logger import logger
from constants import (
    BASE_REGISTRAR_CONTROLLER_ABI,
    BASE_REGISTRAR_CONTROLLER_ADDRESS,
    BASE_COINTYPE,
    L2_RESOLVER_ABI,
    L2_RESOLVER_ADDRESS,
    first_name,
    last_name
)

CHAIN_NAME = "base"
CHAIN_ID = 8453
RPC_ENDPOINT = "https://base.llamarpc.com"

MAX_REGISTER_DOMAIN = 4
MAX_THREAD = 1


class AggregateWallet:
    def aggregate_seed(self, wallet_data: str):
        count_seed = len(wallet_data.split(' '))
        if count_seed < 12:
            return
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(wallet_data)

        root_key = BIP32Key.fromEntropy(seed)
        child_key = root_key.ChildKey(44 + BIP32_HARDEN).ChildKey(60 + BIP32_HARDEN).ChildKey(
            0 + BIP32_HARDEN).ChildKey(0).ChildKey(0)

        private_key_bytes = child_key.PrivateKey()
        private_key_hex = private_key_bytes.hex()

        public_key_bytes = keys.PrivateKey(bytes.fromhex(private_key_hex)).public_key
        wallet_address = Web3.to_checksum_address(public_key_bytes.to_checksum_address())
        return [wallet_address, wallet_data, private_key_hex]

    def aggregate_private_key(self, wallet_data: str):
        account = Account.from_key(wallet_data)
        wallet_address = Web3.to_checksum_address(account.address)
        return [wallet_address, "none_seed", wallet_data]

    def get_private_key(self, data: str):
        try: return self.aggregate_private_key(data)[2]
        except: pass

        try: return self.aggregate_seed(data)[2]
        except: pass

        return None


class AsyncBaseDomainRegister:
    def __init__(self, evm_private_key: str):
        self.account: LocalAccount = Account.from_key(evm_private_key)
        self.web3: AsyncWeb3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(RPC_ENDPOINT))
        self.owner_address: ChecksumAddress = self.account.address

        self.l2resolver = self.web3.eth.contract(
            address=AsyncWeb3.to_checksum_address(L2_RESOLVER_ADDRESS),
            abi=json.loads(L2_RESOLVER_ABI)
        )

        self.registrar_controller = self.web3.eth.contract(
            address=AsyncWeb3.to_checksum_address(BASE_REGISTRAR_CONTROLLER_ADDRESS),
            abi=json.loads(BASE_REGISTRAR_CONTROLLER_ABI)
        )

    async def get_all_domains(self, session: aiohttp.ClientSession):
        url = "https://www.base.org/api/basenames/getUsernames"
        params = {
            "address": str(self.owner_address),
            "network": "base-mainnet"
        }

        async with session.get(url, params=params) as response:
            data = await response.json()

        count = data.get("total_count", 0)
        all_domain = data.get("data", [])
        domains = []
        if all_domain:
            domains = [_['domain'] for _ in all_domain]

        return count, domains

    async def get_gas_params(self) -> Dict[str, int]:
        latest_block = await self.web3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.web3.eth.max_priority_fee
        max_fee = base_fee + max_priority_fee

        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }

    def get_random_domain(self) -> str:
        r = random.Random()
        login = ""

        for dm in range(1000):
            f_name = random.choice(first_name)
            l_name = random.choice(last_name)
            f_name = f_name.lower()
            l_name = l_name.lower()
            login = ""
            try:
                bool_cut_fname = r.choice([True, False])
                cut_f_name = ""
                if bool_cut_fname:
                    try:
                        cut_f_name = f_name[:r.randint(0, len(f_name))]
                    except:
                        cut_f_name = f_name
                else:
                    cut_f_name = f_name

                bool_cut_lname = r.choice([True, False])
                cut_l_name = ""
                if bool_cut_lname:
                    try:
                        cut_l_name = l_name[:r.randint(0, len(l_name))]
                    except:
                        cut_l_name = l_name
                else:
                    cut_l_name = l_name

                bool_add_digit = r.choice([True, False])
                digit = ""
                if bool_add_digit:
                    td = r.randint(0, 2)
                    if td == 0:
                        digit = str(r.randint(1980, 2006))
                    elif td == 1:
                        digit = str(r.randint(5, 999)).zfill(3)
                    elif td == 2:
                        digit = str(r.randint(5, 9999)).zfill(4)
                    else:
                        digit = str(r.randint(1980, 2006))

                rd = r.randint(0, 1)
                if rd == 0:
                    login = f"{cut_f_name}{cut_l_name}{digit}"
                else:
                    login = f"{cut_l_name}{cut_f_name}{digit}"

            except Exception as e:
                pass

            if login and not login.startswith("_") and not login.endswith("_") and len(login) > 6:
                break

        return login

    async def check_available_domain(self, domain_name: str) -> bool:
        return await self.registrar_controller.functions.available(domain_name).call()

    async def build_tx(self, domain_name: str) -> Dict[str, Any]:
        reg_duration = await  self.registrar_controller.functions.MIN_REGISTRATION_DURATION().call()
        reg_price = await self.registrar_controller.functions.registerPrice(
            domain_name,
            reg_duration
        ).call()

        full_domain_name = f"{domain_name}.base.eth"
        domain_bytes = normal_name_to_hash(full_domain_name)

        item1 = self.l2resolver.functions.setAddr(domain_bytes, Web3.to_checksum_address(self.owner_address))
        item2 = self.l2resolver.functions.setAddr(domain_bytes, BASE_COINTYPE, Web3.to_bytes(hexstr=self.owner_address) )
        item3 = self.l2resolver.functions.setName(domain_bytes, full_domain_name)

        reg_data = self.registrar_controller.functions.register(
            (
                str(domain_name),
                self.owner_address,
                int(reg_duration),
                Web3.to_checksum_address(L2_RESOLVER_ADDRESS),
                [
                    item1._encode_transaction_data(),
                    item2._encode_transaction_data(),
                    item3._encode_transaction_data()
                ],
                True
            )
        )

        gas_params = await self.get_gas_params()

        transaction = {
            "from": self.owner_address,
            "to": Web3.to_checksum_address(BASE_REGISTRAR_CONTROLLER_ADDRESS),
            "data": reg_data._encode_transaction_data(),
            "value": int(reg_price),
            "chainId": CHAIN_ID,
            "type": 2,
        }

        estimated_gas = await self.web3.eth.estimate_gas(transaction)
        estimated_gas = int(estimated_gas * random.uniform(1.15, 1.3))

        nonce = await self.web3.eth.get_transaction_count(self.owner_address, "latest")

        transaction.update(
            {
                "nonce": nonce,
                "gas": estimated_gas,
                **gas_params,
            }
        )

        return transaction

    async def sign_tx(self, transaction):
        signed_tx = self.web3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = await self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return Web3.to_hex(tx_hash)

    async def buy_base_domain(self, session: aiohttp.ClientSession):
        try:
            count, domains = await self.get_all_domains(session)
        
            if count < MAX_REGISTER_DOMAIN:
                domain_name: str = ''
                available: bool = False

                while not available:
                    domain_name = self.get_random_domain()
                    available = await self.check_available_domain(domain_name)
                    if available:
                        break
                    await asyncio.sleep(1)

                tx_hash = await self.sign_tx(await self.build_tx(domain_name))
                logger.success(f"[{self.owner_address}] Success buy domain: {domain_name}.base.eth | Hash: {tx_hash}")
                return True
            else:
                logger.success(f"[{self.owner_address}] {count} base domains already register: {domains}")
                return True
        except Exception as e:
            logger.error(f"[{self.owner_address}] Error domain reg: {e}")
            return False


async def register_multiple_domains(private_keys: list, max_concurrent: int = 1):
    async def register_single_domain(private_key: str, session: aiohttp.ClientSession):
        register = AsyncBaseDomainRegister(private_key)
        res = await register.buy_base_domain(session)
        return res

    semaphore = asyncio.Semaphore(max_concurrent)

    async def register_with_semaphore(private_key: str, session: aiohttp.ClientSession):
        async with semaphore:
            return await register_single_domain(private_key, session)

    async with aiohttp.ClientSession() as session:
        tasks = [
            register_with_semaphore(private_key, session)
            for private_key in private_keys
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = 0
        failed = 0

        for result in results:
            if result:
                successful += 1
            else:
                failed += 1

        logger.info(f"Registration completed. Successful: {successful}, Failed: {failed}")
        return results


async def main():
    with open("wallet_data.txt", "r", encoding="utf-8") as f:
        wallet_data = [line.strip() for line in f if line.strip()]

    if len(wallet_data) > 0:
        private_keys = []

        for _ in wallet_data:
            pk = AggregateWallet().get_private_key(_)
            if pk:
                private_keys.append(pk)

        if len(private_keys) > 0:
            logger.warning(f"Loading: {len(private_keys)} wallet. Run script of {MAX_THREAD} thread...")
            results = await register_multiple_domains(private_keys, max_concurrent=MAX_THREAD)
        else:
            logger.error(f"Count of private key - 0! Check validity of wallet data!")
    else:
        logger.error(f"No wallet data (seed or private key) in wallet_data.txt")


if __name__ == "__main__":
    asyncio.run(main())













