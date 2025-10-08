# https://www.geeksforgeeks.org/python/how-to-write-a-configuration-file-in-python/

import configparser

def create_config():
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    config['General'] = {'debug': True, 'log_level': 'info'}
    config['Path'] = {'root': '',
        'pdfs':'/files-test', #'pdfs':'/files-1-1',
        'txts':'/xfiles'
        }
    config['Embedding'] = {'name': 'embeddinggemma'}
    config['Llm'] = {'name': 'llama3.2'}

    # Write the configuration to a file
    with open('config.ini', 'w') as configfile:
        config.write(configfile)


if __name__ == "__main__":
    create_config()

create_config()