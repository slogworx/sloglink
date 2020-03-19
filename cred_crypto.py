'''
    I use this to encrypt database credentials or other small messages for web stuff.
    Please set the permissions properly on the files. 'chmod 600' should do the trick.
'''
from cryptography.fernet import Fernet
import sys


def new_key(key_filename):
    key = Fernet.generate_key()
    with open(key_filename, 'w') as kf:
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


def main(): 

    print('This script creates a key and encrypts it along with your SQLAlchemy connection string.')
    key_filename = input('Enter a filename to store your encryption key: ')
    key = new_key(key_filename)
    print(f'Your key is stored in \'{key_filename}\'. Please remember it, and make sure to \'chmod 600\' the file.')
    
    connection_string = input('Enter connection string (If you don\'t know what it is, see https://slog.link/BT): ').rstrip().encode(encoding='utf-8')
    encrypted_string = cred_crypto(connection_string, key, 'encrypt')
    cred_filename = input('Enter the filename to store your encrypted credentials: ').rstrip()
    save_text(str(encrypted_string,'utf-8'), cred_filename)
    print(f'Your credentials are stored in \'{cred_filename}\'. Please remember it, and make sure to \'chmod 600\' the file.\n')
    print('Make sure to edit sloglinkdb.py to update the filenames in connect(). Authentication wont work without that step.\n\n')
    



if __name__ == "__main__":
    main()