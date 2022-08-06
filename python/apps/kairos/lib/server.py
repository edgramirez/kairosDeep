import codecs, json
import lib.common as com
import lib.validate as validate
import lib.json_methods as jsm


def get_server_info_from_server(header, abort_if_exception = True, quit_program=True):
    srv_info_url = com.GET_SERVER_CONFIG_URI
    for machine_id in com.get_machine_mac_addresses():
        #machine_id = '00:04:4b:eb:f6:dd'  # HARDCODED MACHINE ID
        #print('machine_id: ', machine_id)
        data = {"id": machine_id}
        
        if abort_if_exception:
            response = jsm.send_json(header, data, 'POST', srv_info_url)
        else:
            options = {'abort_if_exception': False}
            response = jsm.send_json(header, data, 'POST', srv_info_url, **options)
        
        if response.status_code == 200:
            try:
                if json.loads(response.text)['ERROR']:
                    com.log_debug("Server answered with errors: {}".format(json.loads(response.text)))
                    return False
            except KeyError:
                com.log_debug("No error detected in the response")
            return json.loads(response.text)
        else:
            return com.log_error("Unable to retrieve the device configuration from the Server. Server response: {}".
                                 format(response.text), quit_program)


def get_server_info_from_file(file_path, abort_if_exception = True):
    if com.file_exists(file_path):
        com.log_debug('Using local {} to get the service config'.format(file_path))
        with open(file_path) as json_file_handler:
            data = json.load(json_file_handler)
            if isinstance(data, dict):
                return data
    if abort_if_exception:
        return com.log_error("Unable to retrieve the device configuration from local file: {}".
                             format(file_path), abort_if_exception)
    return False


def get_server_info(header, abort_if_exception=True, quit_program=True):
    #scfg = get_server_info_from_server(header, abort_if_exception, quit_program)

    scfg = False
    if scfg is False:
        scfg = get_server_info_from_file('configs/Server_Emulatation_configs_from_Excel.py', abort_if_exception)

    # check the return information is actually for this machine by comparing the ID and validate all the parameters
    return validate.parse_parameters_and_values_from_config(scfg)
