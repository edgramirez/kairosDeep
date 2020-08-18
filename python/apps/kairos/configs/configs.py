config = {
        'parameter': {
            'input_type': 'video', # valid values 'video' or 'rtsp'
            'source': '/media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
            'camera_id': 'Negocio0001-Tienda12-fe80::adc4:3105:77aa:eca',
            # 'source': 'rtsp://192.168.28.2:9000/live/video',
            },

        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },

        'services': {
              # 1 defines A1 as outside, 2 defines A2 as outside area 
            'aforo': {'enabled': True,'outside_area': 1, 'aforo_reference_line_coordinates': [(510, 740), (1050, 740)]},
            'people_counting': {'enabled': False,'frequency': 32},
            'social_distance': {'enabled': True,'tolerated_distance': 150,'persistence_time': 1,'enabled_draw_line': False,'enabled_draw_rectangle': False,'line_width': 3,'line_color': (50, 120 ,255)}},
            '},

        }
