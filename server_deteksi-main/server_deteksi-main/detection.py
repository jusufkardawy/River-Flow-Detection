import cv2, time, pandas
from datetime import datetime
from time import sleep, time
import time
import math
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__) #Panggil fungsi menjalanklan flask
CORS(app) #Menerima request dari luar (tanpa token)
@app.route('/', methods = ['POST']) #router (addres untuk menerima request post)
def index(): #fungsi index (fungsi utama)

    uploaded_file = request.files['file'] #Menerima request file (video)

    if uploaded_file.filename != '': #check apakah filenya ada (jika tidak maka stop)
        uploaded_file.save('sungai.mp4') #simpan file video (timpa yang sebelumnya)

    #deklarasi awal
    dist_from_camera = 3 #jarak kamera ke object
    theta = 45
    object_count = 0;
    speed = 0.0;
    speed_kmph = 0.0
    road_length = dist_from_camera * math.tan(theta) * 2 #mencari panjang jangkauan yang ditangkap kamera
    static_back = None;
    motion_list = [None, None];
    time = []
    df = pandas.DataFrame(columns=["Start", "End"]) #Menentukan frame yang diambil dari awal hingga akhir
    video = cv2.VideoCapture('sungai.mp4') #Menyimpan video dalam variable
    check, frame = video.read() #baca variable videonya
    sleep(2)
    frame_count = 0;
    last_frame_motion = 0;
    delta_t = 0
    motion = 0;
    stk = [];
    x_cor = [];
    t = datetime.now()
    average_speed = []
    speed_result = 0;


    # continuous video stream
    while True: #looping untuk membaca perframe
        check, frame = video.read()
        if motion == 0: #jika tidak ada objek
            last_frame_motion = 0 #maka catat objek frame 0
        else:
            last_frame_motion = 1 #maka object di frame ada
        motion = 0
        if not check: #jika frame video telah habis maka berhenti
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) #convert dari rgb ke gray
        gray = cv2.GaussianBlur(gray, (21, 21), 0) #membuat blur menggunakan gausianblur
        if static_back is None: #jika nilai awal kosong
            static_back = gray #simpan hasilnya di gray
            continue

        diff_frame = cv2.absdiff(static_back, gray) #perbedaan frame sebelumnya dengan frame looping sekarang
        thresh_frame = cv2.threshold(diff_frame, 25, 255, cv2.THRESH_BINARY)[1] #menentukan treshold (ambang batas) dari warna 25 hingga 255
        thresh_frame = cv2.dilate(thresh_frame, None, iterations=2) #meningkatkan kontras warna putih (biar lebih jelas lagi)

        # moving regions
        (cnts, _) = cv2.findContours(thresh_frame.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #pinggiran object #tresh frame = mengambil

        for contour in cnts:  #jika ada object yang terdeteksi maka jalankan fungsi looping ini
            if cv2.contourArea(contour) < 10000: #batasan besar object yang dideteksi
                continue
            motion = 1 #membuat nilai motion menjadi 1 jika tedapat object
            (x, y, w, h) = cv2.boundingRect(contour) #melihat contour-contour yang ada di frame
            centroid_x = int((x + x + w) / 2) #mencari posisi dari x contour
            centroid_y = int((y + y + h) / 2) #mencari posisi dari y contour
            t = datetime.now() #deklar waktu awal
            object_count += 1 #menambah jumlah objek
            stk.append(t) #menyimpan waktu sekarang
            x_cor.append(centroid_x) #menyimpan koordinat sekarang
            # region marked in green
            img = cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3) #membuat bounding box dari object
            # centroid
            cv2.circle(frame, (centroid_x, centroid_y), 5, (0, 0, 255), -1) #titik tengah object
            cv2.putText(img, "Object No: " + str(object_count), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0),2) #masukin text untuk jumlah objectnya
        if motion == 0 and last_frame_motion == 1 and stk: #jika object ditemukan
            delta_t = t - stk[0] #mengetahui waktu yang dihabiskan untuk perpindahan object
            dx = abs(centroid_x - x_cor[0]) #jarak pindahnya object
            stk.pop()
            x_cor.pop()
            str_time = str(delta_t) #bentuk string dari object
            str_time = str_time.split(':') #pemisahnya titik dua dan menyimpannya ke dalam array0
            sec = int(str_time[0]) * 3600 + int(str_time[1]) * 60 + float(str_time[2]) #ubah bentuk jadi waktu detik
            try:
                speed = road_length / sec #rumus kecepatan
            except:
                print("Error: Object Moved Too Fast")

        frame_count += 1 #hitung frame
        # reset the threshold frame
        if frame_count % 40 == 0: #batasan 40 frame
            average_speed.append(speed) #simpan kecepatan setiap frame kedalam array
            static_back = gray #menyimpan frame sekarang

    #looping perhitungan kecepatan rata"
    for i in range(len(average_speed)):
        speed_result += average_speed[i]
    message = speed_result / len(average_speed)
    return { "data": message }


if __name__ == '__main__': #method yang dijalankan
    app.run(port = 5000) #membuka port 5000
    app.run(debug=True) #Menampilkan error