{
    "9c:7b:ef:2a:b6:07":
    {
        "camera_mac_1": 
        {
	        "aforo": 
	        {
	            "enabled": true,
                    "source": "file:///tmp/shopping_mall.mkv",
	            "reference_line": 
	            {
	                "coordinates": ["(130, 270)", "(550, 200)"],
	                "reference_line_width": 5,
	                "reference_line_color": ["1", "1", "1", "1"],
	                "outside_area": 2
	            },
	            "area_of_interest": 
	            {
	                "area_of_interest_type": "horizontal",
	                "up": 100,
	                "down": 550,
	                "left": 0,
	                "right": 0
	            }
	        },
	        "social_distance": 
	        {
	            "enabled": false,
	            "tolerated_distance": 100,
	            "persistence_time": 1
	        }
        },
        "camera_mac_2":
        {
	        "people_counting": 
	        {
                    "source": "rtsp://192.168.128.3:9000/live",
	            "enabled": false
	        }
        },
        "camera_mac_3":
        {
	        "mask_detection": 
	        {
                    "source": "rtsp://192.168.128.3:9000/live",
	            "enabled": false
	        }
        }
    }
}
