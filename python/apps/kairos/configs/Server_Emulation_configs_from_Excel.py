{
    "CajaLosAndes-ac:17:c8:62:08:5b": 
    {
        "video-maskDetection": 
        {
            "source": "/home/mit-mexico/gente_con_cubrebocas.mp4", 
            "enabled": "False"
        }, 
        "video-socialDistancing": 
        {
            "tolerated_distance": "150.0", 
            "source": "rtsp://192.168.127.2:9000/live", 
            "persistence_time": "2.0", 
            "enabled": "False"
        }, 
        "video-people": 
        {
            "reference_line_coordinates": "(520, 700), (1120, 700)", 
            "MaxAforo": "", 
            "reference_line_outside_area": "1.0", 
            "source": "rtsp://192.168.127.2:9000/live", 
            "area_of_interest": "", 
            "enabled": "True", 
            "area_of_interest_type": ""
        }
    }, 
    "DTevar-culhuacan-34:56:fe:a3:99:de": 
    {
        "video-socialDistancing": 
        {
            "tolerated_distance": "100.0", 
            "source": "rtsp://192.168.128.3:9000/live", 
            "persistence_time": "2.0", 
            "enabled": "False"
        }, 
        "video-people": 
        {
            "reference_line_coordinates": "(500, 720), (1100, 720)", 
            "MaxAforo": "20.0", 
            "reference_line_outside_area": "1.0", 
            "source": "rtsp://192.168.128.3:9000/live", 
            "area_of_interest": "90,90,0,0", 
            "enabled": "False", 
            "area_of_interest_type": "horizontal"
        }
    }, 
    "OK": true
}
