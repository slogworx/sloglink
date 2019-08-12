'''
    I use this to encrypt database credentials or other small messages for web stuff.
    Please change the key filename, and set the permissions properly.
'''
from cryptography.fernet import Fernet
import sys

SECRET_KEY = '.keep_me_secret.key'


def new_key():
    key = Fernet.generate_key()
    with open(SECRET_KEY, 'w') as kf:
        kf.write(key.decode(encoding='utf-8'))
    return key


def load_text(filename):
    text = ""
    with open(filename, 'r') as tf:
        text = tf.readlines()
    return ' '.join(text).encode(encoding='utf-8')


def save_text(text, filename):
    with open(filename, 'w') as tf:
        tf.write(text)


def cred_crypto(btext, bkey, action):
    '''Ensure btext and bkey are type byte and action is encrypt or decrypt.'''
    do = Fernet(bkey)
    if action == 'encrypt':
        result = do.encrypt(btext)
    elif action == 'decrypt':
        result = do.decrypt(btext)
    else:
        print('Invalid action argument passed to cred_crypto().')
        exit()
    return result


def main(argv):
    if len(argv) == 2:  # New message, generate a new key.
        key = new_key()
        text = get_text(argv[1])
        save_text(cred_crypto(text, key, 'encrypt').decode(encoding='utf-8'), argv[1])

    elif len(argv) == 4:  # Use existing key to encrypt/decrypt.
        key = load_key(argv[2])
        text = get_text(argv[1])
        save_text(cred_crypto(text, key, argv[3]).decode(encoding='utf-8'), argv[1])
    else:
        print(f"usage: {argv[0]} txt_filename [key_filename] [action]")


if __name__ == "__main__":
    main(sys.argv)
