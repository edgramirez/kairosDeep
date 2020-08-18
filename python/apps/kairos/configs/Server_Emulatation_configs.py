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
            'aforo': {
                'enabled': True,
                'outside_area': 1, # 1 defines A1 as outside, 2 defines A2 as outside area
                'aforo_reference_line_coordinates': [(0, 250), (1920, 601)],
                },},

        }
