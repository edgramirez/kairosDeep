#                'source': 'file:///tmp/1.mkv',
config = {
        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },
        'cameras': {
            'DTevar-culhuacan-34:56:fe:a3:99:de':
                {
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
                'aforo': {
                    'enabled': False,
                    'reference_line': {
                        'outside_area': 1,
                        'coordinates': [(660, 500), (1000, 500)],
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
                    'enabled': True,
                    'tolerated_distance': 100,
                    'persistence_time': .01,
                    },
                },
            'CajaLosAndes-ac:17:c8:62:08:5b':
                {
                'source': "rtsp://192.168.127.2:9000/live",
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
                    'tolerated_distance': 300,
                    'persistence_time': 1,
                    },
                },
            },

        }


'''
                'source': "rtsp://192.168.128.3:9000/live",
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',

                    'area_of_interest': {
                        'type': 'fixed',
                        'topx': 600,
                        'topy': 300,
                        'width': 230,
                        'height': 230,
                        }, # type = follow, fixed, horizontal ['horizontal' is the default]


                'aforo': {
                    'enabled': True,
                    'reference_line': {
                        'outside_area': 1, 
                        'coordinates': [(660, 500), (1000, 500)], 
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




                'aforo': {
                    'enabled': True,
                    },


                    'area_of_interest': {
                        'type': 'fixed',
                        'topx': 500,
                        'topy': 200,
                        'width': 280,
                        'height': 280,
                        }, # type = follow, fixed, horizontal ['horizontal' is the default]




                    'reference_line': {
                        'outside_area': 1, 
                        'coordinates': [(660, 300), (660, 630)], 
                        'width': 5, 
                        'color': [1, 1, 1, 1],
                        }, 
                    'area_of_interest': {
                        'type': 'horizontal',
                        'up': 0,
                        'down': 0,
                        'left': 80,
                        'right': 80,
                        },



config = {
        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },
        'cameras': {
            'DTevar-culhuacan-34:56:fe:22:22:22': 
                {
                'source': "rtsp://192.168.128.3:9000/live",
                'aforo': {
                    'enabled': True,
                    'reference_line': {
                        'outside_area': 1, 
                        'coordinates': [(550, 610), (990, 410)], 
                        'width': 5, 
                        'color': [1, 1, 1, 1],
                        }, 
                    'area_of_interest': {
                        'type': 'horizontal',
                        'up': 90,
                        'down': 90,
                        'left': 0,
                        'right': 0,
                        }, # type = follow, fixed, horizontal ['horizontal' is the default]
                    },
                'social_distance': {
                    'enabled': False,
                    'tolerated_distance': 50,
                    'persistence_time': 1,
                    },
                },
            },

        }











                'source': 'file:///home/edgar/Downloads/160820_028_NYC_GrandCentralStation4_1080p.mp4',
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
                'source': 'file:///media/edgar/external_sdcard/MV12_Ent_Sal_20Agst2020ERM.mp4',
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},


                    'polygon': [(360,360), (460,440), (560,540), (440, 640), (300,620)],
                    'aforo_area_of_interest': {'top': 360, 'left': 400, 'height': 100, 'width': 750}, 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                'source': "rtsp://192.168.128.3:9000/live",
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
                'source' es un campo obligorio y no puede faltar en cada una de las camaras



                'source': 'file:///media/edgar/external_sdcard/MV12_Ent_Sal_20Agst2020ERM.mp4',
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
            'DTevar-culhuacan-34:56:fe:a3:99:de': {
                'source': 'file:///media/edgar/external_sdcard/MV12_Ent_Sal_20Agst2020ERM.mp4',
                'aforo': {
                    'enabled': True,
                    'outside_area': 1, 
                    'aforo_reference_line_coordinates': [(510, 700), (1100, 700)], 
                    'aforo_area_of_interest': {'top': 360, 'left': 400, 'height': 100, 'width': 750}, 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                    },
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
                'source': 'file:///media/edgar/external_sdcard/respaldo_anterior_instalacion/githubs/kairosconnect-vision/videos/shopping_mall.mkv',
            'DTevar-culhuacan-34:56:fe:22:22:22': {
                'source': 'file:///media/edgar/external_sdcard/MV12_Ent_Sal_20Agst2020.mp4',
                'aforo': {
                    'enabled': True,
                    'outside_area': 1, 
                    'aforo_reference_line_coordinates': [(510, 700), (1100, 700)], 
                    'aforo_area_of_interest': {'top': 360, 'left': 400, 'height': 100, 'width': 750}, 
                    'line_width': 5,
                    'line_color': [1, 1, 1, 1],
                    },
                'social_distance': {'enabled': False,'tolerated_distance': 150,'persistence_time': 1,'line_width': 5,'line_color': (50, 120 ,255)},
                'people_counting': {'enabled': False},
                },
'''
