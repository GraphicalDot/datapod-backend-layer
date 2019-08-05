
from  mnemonic import mnemonic as mnemoniclib

from bip32utils import BIP32Key
from bip32utils import BIP32_HARDEN
import os


def generate_entropy():
    strength_bits = 256
    entropy = os.urandom(strength_bits // 8)
    return entropy


def generate_mnemonic(lang):
    ##lang in which the entropy must be generated
    entropy = generate_entropy()
    wallet_generator = mnemoniclib.Mnemonic(lang)
    _mnemonic = wallet_generator.to_mnemonic(entropy)
    assert wallet_generator.to_entropy(_mnemonic) == entropy  # see, bijective!
    return _mnemonic



def child_keys(mnemonic, index):
    seed = mnemoniclib.Mnemonic.to_seed(mnemonic)
    rootkey = BIP32Key.fromEntropy(seed)

    childkey_object = rootkey.ChildKey(44 + BIP32_HARDEN)\
            .ChildKey(index + BIP32_HARDEN)\
            .ChildKey(index + BIP32_HARDEN)\
            .ChildKey(index).ChildKey(index)

    return {"private_key": childkey_object.WalletImportFormat(), 
            "public_key": childkey_object.PublicKey().hex(), 
            "address": childkey_object.Address()}