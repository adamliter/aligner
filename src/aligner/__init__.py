import os
import yaml


module_dir, _ = os.path.split(__file__)
with open(os.path.join(module_dir, 'log_conf.yml'), 'r') as f:
    log_conf = yaml.load(f, Loader=yaml.FullLoader)
