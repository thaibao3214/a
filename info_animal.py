from database import db

animal_data = {
    'meo': {
        'scientific_name': 'Felis catus',
        'description': 'Mèo nhà là một loài động vật có vú nhỏ, có lông, ăn thịt.',
        'habitat': 'Được tìm thấy trên toàn thế giới như vật nuôi và mèo hoang',
        'diet': 'Ăn thịt - con mồi nhỏ như chuột, chim, cá',
        'lifespan': '12-18 năm'
    },
    'cho': {
        'scientific_name': 'Canis lupus familiaris',
        'description': 'Chó nhà là một loài sói đã được thuần hóa và là thành viên của họ Chó.',
        'habitat': 'Được tìm thấy trên toàn thế giới như động vật bầu bạn',
        'diet': 'Ăn tạp (cả thực vật và động vật)',
        'lifespan': '10-13 năm'
    },
    'bo': {
        'scientific_name': 'Bos taurus',
        'description': 'Bò là loài gia súc được nuôi để lấy sữa, thịt và làm sức kéo.',
        'habitat': 'Trang trại, đồng cỏ, vùng nông thôn',
        'diet': 'Ăn cỏ, rơm rạ và thức ăn chăn nuôi',
        'lifespan': '15-20 năm'
    },
    'buom': {
        'scientific_name': 'Rhopalocera',
        'description': 'Bướm là côn trùng có cánh sặc sỡ, phát triển từ ấu trùng.',
        'habitat': 'Rừng, vườn hoa, đồng cỏ',
        'diet': 'Chủ yếu hút mật hoa',
        'lifespan': '1 tuần - vài tháng tùy loài'
    },
    'cuu': {
        'scientific_name': 'Ovis aries',
        'description': 'Cừu là loài động vật có vú được nuôi để lấy lông và thịt.',
        'habitat': 'Trang trại, vùng núi, thảo nguyên',
        'diet': 'Ăn cỏ, lá cây',
        'lifespan': '10-12 năm'
    },
    'ga': {
        'scientific_name': 'Gallus gallus domesticus',
        'description': 'Gà là loài gia cầm phổ biến, được nuôi để lấy thịt và trứng.',
        'habitat': 'Nông trại, vườn nhà',
        'diet': 'Thức ăn tổng hợp, hạt, sâu bọ',
        'lifespan': '5-10 năm'
    },
    'ngua': {
        'scientific_name': 'Equus ferus caballus',
        'description': 'Ngựa là động vật có vú được thuần hóa để cưỡi và kéo xe.',
        'habitat': 'Trang trại, đồng cỏ',
        'diet': 'Cỏ, cám, yến mạch',
        'lifespan': '25-30 năm'
    },
    'nhen': {
        'scientific_name': 'Araneae',
        'description': 'Nhện là loài chân khớp có tám chân, thường tạo tơ để bắt mồi.',
        'habitat': 'Khắp nơi: nhà ở, rừng, hang đá',
        'diet': 'Côn trùng nhỏ',
        'lifespan': '1-2 năm, một số loài sống lâu hơn'
    },
    'soc': {
        'scientific_name': 'Sciuridae',
        'description': 'Sóc là loài gặm nhấm nhanh nhẹn, sống chủ yếu trên cây.',
        'habitat': 'Rừng, công viên, khu đô thị',
        'diet': 'Hạt, quả, côn trùng nhỏ',
        'lifespan': '6-12 năm'
    },
    'sutu': {
        'scientific_name': 'Panthera leo',
        'description': 'Sư tử là loài mèo lớn sống thành bầy, là động vật ăn thịt.',
        'habitat': 'Thảo nguyên và rừng thưa châu Phi',
        'diet': 'Ăn thịt - săn mồi như linh dương, ngựa vằn',
        'lifespan': '10-14 năm (tự nhiên), đến 20 năm (nuôi nhốt)'
    },
    'voi': {
        'scientific_name': 'Elephas maximus / Loxodonta africana',
        'description': 'Voi là động vật có vú lớn nhất trên cạn, thông minh và sống theo bầy.',
        'habitat': 'Rừng, thảo nguyên châu Á và châu Phi',
        'diet': 'Thực vật: cỏ, lá, vỏ cây',
        'lifespan': '60-70 năm'
    }
}

def populate_db():
    for class_name, info in animal_data.items():
        success, message = db.add_animal_info(class_name, info)
        print(f"Đang thêm {class_name}: {message}")

if __name__ == '__main__':
    populate_db()
