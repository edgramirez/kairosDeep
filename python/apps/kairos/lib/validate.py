import lib.common as com
import lib.definitions as sd


def check_config_keys_exist(service_name, service_dictionary):
    joint_elements = []
    for group_of_parameters in com.SERVICE_DEFINITION[com.SERVICES[service_name]][service_name]:
        for defined_service_parameter in com.SERVICE_DEFINITION[com.SERVICES[service_name]][service_name][group_of_parameters]:
            joint_elements.append(defined_service_parameter)
    for service_name in service_dictionary:
        for service_parameter in service_dictionary[service_name]:
            if service_parameter != 'camera_mac_address' and service_parameter not in joint_elements:
                com.log_error("Configuration error - Pameter: {}, does not exist in the service definition:".
                              format(service_parameter))
    return True


def validate_sources(active_service_configs):
    '''
    Validate the configuration source recovered from server contains correct values
    '''
    for camera_mac in active_service_configs:
        for parameter in active_service_configs[camera_mac]:
            if "source" == parameter:
                if active_service_configs[camera_mac][parameter][:8] not in com.SOURCE_PATTERNS:
                    com.log_error("Configuration error - Source should be one of this values: {}".
                                  format(com.SOURCE_PATTERNS))
                if active_service_configs[camera_mac][parameter][:8] == com.SOURCE_PATTERNS[0]:
                    if com.file_exists(active_service_configs[camera_mac][parameter][7:]) is False:
                        com.log_error("source file:'{}' does'nt exist".
                                      format(active_service_configs[camera_mac][parameter][7:]))
            else:
                continue

    com.log_debug('All source values are correct')
    return True


def check_obligatory_keys(service_dictionaries, service_definition):
    '''
    Validate the configuration recovered from server provided the defined minimum parameters and their values are valid
    '''
    for defined_item in service_definition['obligatory'].keys():
        for service_name in service_dictionaries:
            if defined_item not in service_dictionaries[service_name]:
                com.log_error("Configuration error - Missing Obligatory parameter: {}".format(defined_item))
            if str(type(service_dictionaries[service_name][defined_item])).split("'")[1] \
                    != service_definition['obligatory'][defined_item]:
                com.log_error("Configuration error - Parameter '{}' value must be type : {}, Current value: {}"
                              .format(defined_item, service_definition['obligatory'][defined_item],
                                      str(type(service_dictionaries[defined_item])).split("'")[1]))
    com.log_debug("All obligatory parameters are OK")
    return True


def check_optional_keys(service_dictionaries, service):
    '''
    Validate the optional configuration recovered from server and its values
    '''
    if "optional" not in com.SERVICE_DEFINITION[com.SERVICES[service]]:
        com.log_debug("Service {} does not have optinal parameters, all OK".format(service))
        return True

    for defined_item in com.SERVICE_DEFINITION[com.SERVICES[service]]['optional'].keys():
        for service_name in service_dictionaries:
            if defined_item in service_dictionaries[service_name] and \
                    str(type(service_dictionaries[service_name][defined_item])).split("'")[1] != \
                    com.SERVICE_DEFINITION[com.SERVICES[service]]['optional'][defined_item]:
                    com.log_error("Configuration error - Parameter '{}' value must be type : {}, Current value: {}".
                        format(defined_item, com.SERVICE_DEFINITION[com.SERVICES[service]]['optional'][defined_item],
                               str(type(service_dictionaries[service][defined_item])).split("'")[1]))

    com.log_debug("All optional parameters are OK")
    return True


def check_service_against_definition(data):
    if not isinstance(data, dict):
        com.log_error("Configuration Error - Must be a  List/dictionaries - type: {} / content: {}".
                      format(type(data), data))

    for camera_mac in data.keys():
        for srv_camera_id in data[camera_mac].keys():
            if srv_camera_id == "source":
                if not isinstance(data[camera_mac][srv_camera_id], str):
                    com.log_error("source parameter should be string")
                continue
            for service_dict in data[camera_mac][srv_camera_id]:
                for service_id in service_dict:
                    for service in service_dict[service_id]:
                        com.log_debug("Validating services config: '--{} / {}--' against definition: \n\n{}\n\n".
                                      format(service, srv_camera_id, service_dict[service_id]))
                        check_config_keys_exist(service, service_dict[service_id])
                        check_obligatory_keys(service_dict[service_id],
                                              com.SERVICE_DEFINITION[com.SERVICES[service]][service])
                        check_optional_keys(service_dict[service_id], service)
    return True


def validate_service_exists(data):
    for camera_mac in data.keys():
        for camera_service_id in data[camera_mac].keys():
            if camera_service_id == "source":
                continue
            for service_item in data[camera_mac][camera_service_id]:
                for service_id in service_item:
                    for service_name in service_item[service_id]:
                        add_service_to_validate(service_name)
                        if service_name not in com.SERVICES:
                            com.log_error("Configuration error - Requested service: {} - Does not exist in the service "
                                          "list: {}".format(service_name, com.SERVICES))
    return True


def add_service_to_validate(service_name):
    if service_name == "whiteList":
        try:
            com.SERVICE_DEFINITION.append(sd.whitelist)
        except AttributeError as e:
            com.log_error("whitelist service parameters are not defined in definition.py file")
    elif service_name == "blackList":
        try:
            com.SERVICE_DEFINITION.append(sd.blacklist)
        except AttributeError as e:
            com.log_error("blackList service parameters are not defined in definition.py file")
    elif service_name == "ageAndGender":
        try:
            com.SERVICE_DEFINITION.append(sd.ageGender)
        except AttributeError as e:
            com.log_error("ageAndGender service parameters are not defined in definition.py file")
    elif service_name == "recurrence":
        try:
            com.SERVICE_DEFINITION.append(sd.recurrence)
        except AttributeError as e:
            com.log_error("recurrence service parameters are not defined in definition.py file")
    else:
        com.log_error("Unable to add Service: "+service_name+", not in the list of coded services")

    i = 0
    for item in com.SERVICE_DEFINITION:
        for service_name in item:
            com.SERVICES.update({service_name: (i)})
            i += 1


def get_config_filtered_by_active_service(config_data):
    if not isinstance(config_data, dict):
        com.log_error("Configuration error - Config must be a dictionary - type: {} / content: {}".
                      format(type(config_data), config_data))

    active_services = {}

    for camera_mac in config_data.keys():
        if 'source' not in config_data[camera_mac]: continue
        if 'services' not in config_data[camera_mac]: continue
        if len(config_data[camera_mac]['services']) == 0: continue

        for service_dict in config_data[camera_mac]['services']:
            for service in service_dict: 
                if 'enabled' in service_dict[service] and \
                    ((isinstance(service_dict[service]['enabled'], bool) and service_dict[service]['enabled']) or
                    ((isinstance(service_dict[service]['enabled'], str) and service_dict[service]['enabled'] == "True"))):
                    # updating from string "True" to True
                    service_dict[service]['enabled'] = True
                    # Create new key only for the active service
                    new_key_name = "camera_" + camera_mac + '_' + service

                    values = {new_key_name: {service: service_dict[service]}}
                    if camera_mac not in active_services:
                        service_list = []
                        services = {}
                        service_list.append(values)
                        services.update({"services": service_list})
                        active_services.update({camera_mac: services})
                        active_services[camera_mac].update({"source": config_data[camera_mac]['source']})
                    else:
                        service_list.append(values)

    if len(active_services) == 0:
        com.log_error("\nConfiguration does not contain any active service for this server: \n\n{}".format(config_data))

    return active_services


def mac_address_in_config(mac_config):
    for machine_id in com.get_machine_mac_addresses():
        if mac_config == machine_id:
            return True
    return False


def get_config_filtered_by_local_mac(config_data):
    '''
    By now we only support one nano server and one interface 
    but it can be a big server with multiple interfaces so I 
    leave the logic with to handle this option
    '''
    services_data = {}
    for key in config_data.keys():
        if mac_address_in_config(key):
            services_data[key] = config_data[key]
    if services_data:
        return services_data

    com.log_error("The provided configuration does not match any of server interfaces mac address")


def parse_parameters_and_values_from_config(config_data):
    # filter config and get only data for this server using the mac to match
    #scfg = get_config_filtered_by_local_mac(config_data)

    # filter config and get only data of active services
    scfg = get_config_filtered_by_active_service(config_data)

    # validate requested services exists in code
    validate_service_exists(scfg)

    # Check all obligatory and optional parameters and values types provided by the dashboard config
    check_service_against_definition(scfg)
    # Check all source values to ensure they are correct and in the case of files they actually exists
    validate_sources(scfg)

    return scfg
