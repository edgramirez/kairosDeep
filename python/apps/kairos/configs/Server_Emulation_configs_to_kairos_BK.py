#                'source': "file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv",
# home/aaeon/Downloads/ejercicio2/video2-1.mp4
# CajaAndesCrop.mp4 
# /opt/nvidia/deepstream/deepstream-5.0/samples/streams/sample_1080p_h264.mp4
config = {
        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },
        'cameras': {
            'DTevar-culhuacan-34:56:fe:a3:99:de':
                {
                'source': "file:///home/aaeon/Downloads/ejercicio2/video3.mp4",
                'aforo': {
                    'enabled': False,
                    'reference_line': {
                        'outside_area': 1,
                        'coordinates': [(500, 720), (1100, 720)],
                        'width': 5,
                        'color': [1, 1, 1, 1],
                        },
                    'area_of_interest': {
                        'type': 'horizontal',
                        'up': 90,
                        'down': 90,
                        'left': 0,
                        'right': 0,
                        },
                    },
                'social_distance': {
                    'enabled': False,
                    'tolerated_distance': 100,
                    'persistence_time': 1,
                    },
                'people_counting': {
                    'enabled': False,
                    },
                'mask_detection': {
                    'enabled': True,
                    },
                },
            },
        }
'''        
            'CajaLosAndes-ac:17:c8:62:08:5b': 
                {
                'source': "file:///home/aaeon/Downloads/ejercicio2/video2-1.mp4",
                'aforo': {
                    'enabled': False,
                    'reference_line': {
                        'outside_area': 1, 
                        'coordinates': [(750, 440), (1400, 370)], 
                        'width': 5, 
                        'color': [1, 1, 1, 1],
                        }, 
                    'area_of_interest': {
                        'type': 'horizontal',
                        'up': 90,
                        'down': 90,
                        'left': 0,
                        'right': 0,
                        },
                    },
                'social_distance': {
                    'enabled': False,
                    'tolerated_distance': 150,
                    'persistence_time': .01,
                    },
                'people_counting': {
                    'enabled': False,
                    },
                },
            },
        }
#                'source': "rtsp://192.168.128.3:9000/live",
#                'source': "rtsp://192.168.127.2:9000/live", 
'''
