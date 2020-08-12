config = {
        'server': {
            'url': 'https://mit.kairosconnect.app/',
            'token_file': '.token',
            },

        'business': {
            'id': '0001',
            'full_name': 'Grupo Comercializador Latino S.A de C.V',
            'short_name': 'Gato Barato',
            'country': 'Mexico',
            'country_id': 'MX',
            'state': 'Morelos',
            'state_id': '12',
            'store_id': '2',
            'store_name': '2',
            },

        'parameters': {
            'output_file_path': '/tmp/',
            'class': 'person',
            'configs': 'yolo-coco/yolov3.cfg',
            'weights': '../yolov3.weights',
            'classes': 'yolo-coco/coco.names',
            'confidence': 0.35, # between 0.1 and .99
            'threshold': 0.25, # between 0.1 and .49
            },

        'video': {
            'input': {
                'input_type': 'video', # rtsp
                #'source': '/home/edgar/Downloads/MV12_-_Pasillo_1592579461_1592580424.mp4',
                #'source': '/home/edgar/Desktop/MV12_Ent_Sal_1592857982_1592858645.mp4',
                'source': 'videos/shopping_mall.mkv', # or rtsp uri for streaming "rtsp://admin:<port>@<ip>/xyz/video.smp"
                'camera_id': '0001-MX-12-2-fe80::adc4:3105:77aa:eca',
                'camera_name': 'pasillo 1',
                },
            'output': {
                'enable': True,
                'file': '/tmp/video_23.avi',
                },
            },

        'intersection_line': {
            'show': False,
            'coordinates': [(0,250), (1920, 601)],
            'color': (0, 155, 155),
            'width': 4,
            },

        'service': {
            'people_counting': {
                'enabled': False,
                'frequency': 32,
                },
            'counting_in_and_out': {
                'enabled': True,
                'outside_area': 1, # 1 defines A1 as inside, 2 defines A2 as inside area
                'report_frequency': 5,
                },
            'social_distance': {
                'enabled': False,
                'tolerated_distance': 150,
                'persistence_time': 3,
                'enabled_draw_line': False,
                'enabled_draw_rectangle': False,
                'line_width': 3,
                'line_color': (50, 120 ,255),
                },
            'object_intersection': {
                'enabled': False,
                },
            'trace_objects': {
                'enabled': False,
                'frequency': 32,
                },
            'object_speed': {
                'show': True,
                'text_width': 2,
                'text_x_offset': 0,
                'text_y_offset': 28,
                },
            },

        'summary_info': {
            'show': False,
            'text_id_text': {
                'horizontal': ['Up', 'Down', 'Status'],
                'vertical': ['Left', 'Right', 'Status'],
                },
            'text_id_width': 2,
            'text_id_color': (0, 255, 200),
            },

        'counting_results': {
            'show': True,
            'frame_counting': True,
            'text1': 'Entrando',
            'text2': 'Saliendo',
            'coordinates': (170, 930),
            'color': (0, 90, 255),
            'size': 2.0,
            'width': 4,
            },

        'rectangle': {
            'show': False,
            'width': 2,
            },
        }
