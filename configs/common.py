import configparser
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config = configparser.ConfigParser()
config.read(BASE_DIR+'/configs/common.ini')
conf = {}
for section in config.sections():

    conf[section] = {}
    for option in config.options(section):
        conf[section][option] = config.get(section, option)

dir_path = os.path.dirname(os.path.realpath(__file__))

conf['BASE_DIR'] = BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(conf['BASE_DIR'],'configs/mail.json'), 'r') as f :
    conf['mail'] = json.loads(f.read())
    
    
