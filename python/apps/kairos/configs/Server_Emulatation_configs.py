config = {
        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },
        'cameras': {
            'DTevar-culhuacan-34:56:fe:33:33:11': {
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
                'aforo': {
                    'enabled': True,
                    'outside_area': 1, 
                    'aforo_reference_line_coordinates': [(510, 645), (1900, 645)], 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                    },
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
            'DTevar-culhuacan-34:56:fe:33:33:33': {
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
                'aforo': {
                    'enabled': True,
                    'outside_area': 1, 
                    'aforo_reference_line_coordinates': [(510, 645), (1900, 645)], 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                    },
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
            }
        }
'''
            'DTevar-culhuacan-34:56:fe:a3:99:de': {
                'source': 'file:///media/edgar/external_sdcard/MV12_Ent_Sal_20Agst2020ERM.mp4',
                'aforo': {
                    'enabled': True,
                    'outside_area': 1, 
                    'aforo_reference_line_coordinates': [(510, 700), (1100, 700)], 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                    },
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
            'DTevar-culhuacan-34:56:fe:22:22:22': {
                'source': 'file:///media/edgar/external_sdcard/MV12_Ent_Sal_20Agst2020.mp4',
                'aforo': {
                    'enabled': True,
                    'outside_area': 1, 
                    'aforo_reference_line_coordinates': [(510, 700), (1100, 700)], 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                    },
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
'''
