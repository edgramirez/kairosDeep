import time
from datetime import datetime
import services as service


retries = 11
got_config_from_server = False

for retries in range(retries):
    nano_config = service.get_server_info(abort_if_exception=False)

    if nano_config:
        got_config_from_server = True
        config_file = 'configs/Server_Emulation_configs_from_Excel.py'

        content = str(nano_config)
        if not service.file_exists(config_file):
            print('Creating physical config file')
            service.create_file(config_file, content)
        break
    else:
        now = datetime.now()
        print('{} - Unable to get server information: {}'.format(now, nano_config))

if not got_config_from_server:
    print('not connected after {} reties'.format(retries))
else:
    print('got config from server ...')
