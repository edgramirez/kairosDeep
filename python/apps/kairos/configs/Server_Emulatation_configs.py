config = {
        'parameter': {
            'input_type': 'video', # valid values 'video' or 'rtsp'
            'source': '/media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
            },
            #'camera_id': 'Negocio0001-Tienda12-fe80::adc4:3105:77aa:eca',
            # 'source': 'rtsp://192.168.28.2:9000/live/video',

        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },

        'cameras': {
            'Negocio0001-Tienda12-fe80::adc4:3105:77aa:e11': {
                'aforo': {'enabled': True,'outside_area': 1, 'aforo_reference_line_coordinates': [(510, 740), (1050, 740)]},
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'enabled_draw_line': False,'enabled_draw_rectangle': False,'line_width': 3,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
            'Negocio0001-Tienda12-fe80::adc4:3105:77aa:e22': {
                'aforo': {'enabled': True,'outside_area': 1, 'aforo_reference_line_coordinates': [(510, 740), (1050, 740)]},
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'enabled_draw_line': False,'enabled_draw_rectangle': False,'line_width': 3,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
            'Negocio0001-Tienda12-fe80::adc4:3105:77aa:e33': {
                'aforo': {'enabled': True,'outside_area': 1, 'aforo_reference_line_coordinates': [(510, 740), (1050, 740)]},
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'enabled_draw_line': False,'enabled_draw_rectangle': False,'line_width': 3,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
            }
        }
