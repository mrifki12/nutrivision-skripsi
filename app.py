import os
import time
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mb_preprocess
from tensorflow.keras.applications.efficientnet import preprocess_input as ef_preprocess
from tensorflow.keras.applications.resnet_v2 import preprocess_input as rs_preprocess

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CLASS_NAMES = [
    'Ayam Goreng', 'Bakso', 'Gado-Gado', 'Kentang Goreng', 
    'Martabak', 'Mie Goreng', 'Nasi Goreng', 'Nasi Padang', 
    'Pisang Goreng', 'Rendang', 'Sate', 'Seblak', 
    'Siomay', 'Soto', 'Tempe Tahu Goreng'
]

# Database Kandungan Gizi & Saran Coach AI (Per 100g / Porsi Standar)
NUTRITION_DB = {
    'Ayam Goreng': {
        'status': 'Tinggi Kalori & Lemak',
        'kalori': '260.0', 'protein': '16.0', 'lemak': '18.0', 'karbo': '5.0',
        'coach_komentar': 'Ayam goreng mengandung protein yang baik, namun proses penggorengan *deep fry* membuatnya tinggi lemak jenuh dan kalori.',
        'coach_sayuran': ['Lalapan segar (kemangi, kol, ketimun) tanpa digoreng.', 'Tumis sayur bening.'],
        'coach_protein': ['Tidak perlu tambahan protein hewani lagi.', 'Bisa tambah tempe/tahu rebus.'],
        'coach_alternatif': ['Buang kulit ayam sebelum dimakan.', 'Pilih bagian dada daripada paha/sayap.']
    },
    'Bakso': {
        'status': 'Tinggi Natrium',
        'kalori': '190.0', 'protein': '11.0', 'lemak': '10.0', 'karbo': '14.0',
        'coach_komentar': 'Bakso daging memberikan asupan protein, namun kuah kaldunya biasanya sangat tinggi garam (natrium) dan MSG.',
        'coach_sayuran': ['Perbanyak sawi hijau dan tauge rebus.', 'Tambahkan irisan seledri dan daun bawang.'],
        'coach_protein': ['Tahu putih rebus.', 'Telur ayam rebus.'],
        'coach_alternatif': ['Jangan minum kuahnya sampai habis.', 'Kurangi penambahan kecap/saus botolan.']
    },
    'Gado-Gado': {
        'status': 'Seimbang',
        'kalori': '132.0', 'protein': '4.5', 'lemak': '5.2', 'karbo': '15.1',
        'coach_komentar': 'Kalori Gado-Gado tergolong rendah dan penuh serat sayur. Protein nabatinya baik, namun kalori bisa melonjak tajam dari bumbu kacang dan kerupuk.',
        'coach_sayuran': ['Kangkung/bayam (rebus) untuk zat besi.', 'Timun/wortel mentah (serat lebih utuh).', 'Tauge (kaya vitamin C).'],
        'coach_protein': ['Telur rebus (tanpa digoreng).', 'Tempe atau tahu kukus/panggang.'],
        'coach_alternatif': ['Kurangi porsi bumbu kacang.', 'Pisahkan kuah.', 'Ganti kerupuk dengan emping porsi kecil.']
    },
    'Kentang Goreng': {
        'status': 'Tinggi Karbohidrat & Lemak',
        'kalori': '311.0', 'protein': '3.4', 'lemak': '15.0', 'karbo': '41.0',
        'coach_komentar': 'Kentang adalah sumber karbohidrat yang baik, namun menggorengnya menghilangkan banyak nutrisi dan melipatgandakan lemak jenuh.',
        'coach_sayuran': ['Salad sayur segar dengan dressing olive oil.', 'Brokoli rebus.'],
        'coach_protein': ['Dada ayam panggang (grilled).', 'Ikan tuna kukus.'],
        'coach_alternatif': ['Ganti metode pengolahan dengan dipanggang (baked potato) atau direbus.', 'Kurangi taburan garam ekstra.']
    },
    'Martabak': {
        'status': 'Sangat Tinggi Kalori & Gula',
        'kalori': '350.0', 'protein': '7.0', 'lemak': '16.0', 'karbo': '46.0',
        'coach_komentar': 'Martabak manis (terang bulan) adalah bom kalori yang padat akan gula, mentega/margarin, dan tepung olahan. Sangat cepat menaikkan gula darah.',
        'coach_sayuran': ['Tidak cocok dimakan bersama sayur. Imbangi dengan makan buah segar setelahnya (seperti apel/pepaya).'],
        'coach_protein': ['Segelas susu rendah lemak hangat.', 'Edamame rebus sebagai camilan penetral.'],
        'coach_alternatif': ['Beli setengah porsi atau bagi dengan teman.', 'Minta kurangi takaran mentega (wisman) dan gula pasirnya.']
    },
    'Mie Goreng': {
        'status': 'Tinggi Karbo & Natrium',
        'kalori': '280.0', 'protein': '6.0', 'lemak': '12.0', 'karbo': '38.0',
        'coach_komentar': 'Mie goreng sebagian besar adalah karbohidrat sederhana yang cepat dicerna, sehingga cepat membuat lapar kembali. Bumbunya tinggi natrium.',
        'coach_sayuran': ['Tambahkan potongan wortel, sawi, dan buncis dua kali lipat lebih banyak.', 'Tomat segar cincang.'],
        'coach_protein': ['Telur orak-arik (sedikit minyak).', 'Irisan dada ayam rebus.', 'Udang kupas.'],
        'coach_alternatif': ['Porsi mie dikurangi setengah, diganti sayur.', 'Jangan tambahkan nasi putih (double karbo).']
    },
    'Nasi Goreng': {
        'status': 'Tinggi Kalori & Lemak',
        'kalori': '250.0', 'protein': '5.0', 'lemak': '9.0', 'karbo': '35.0',
        'coach_komentar': 'Kombinasi nasi (karbohidrat padat) dan minyak goreng membuat kalori nasi goreng sangat tinggi. Minim vitamin jika tanpa sayur.',
        'coach_sayuran': ['Perbanyak irisan tomat dan mentimun segar.', 'Campurkan mixed-vegetables (kacang polong, jagung, wortel).'],
        'coach_protein': ['Telur mata sapi dadar.', 'Suwiran ayam panggang.'],
        'coach_alternatif': ['Gunakan minyak kelapa/zaitun yang lebih sedikit.', 'Ganti nasi putih dengan nasi merah/shirataki.']
    },
    'Nasi Padang': {
        'status': 'Tinggi Kalori, Lemak & Kolesterol',
        'kalori': '450.0', 'protein': '20.0', 'lemak': '22.0', 'karbo': '45.0',
        'coach_komentar': 'Masakan Padang kaya akan rempah, namun penggunaan santan kental yang dipanaskan berulang kali menjadikannya sumber lemak jenuh dan kolesterol tinggi.',
        'coach_sayuran': ['Perbanyak daun singkong rebus.', 'Minta ekstra ketimun potong.', 'Sayur nangka (tiriskan kuahnya).'],
        'coach_protein': ['Pilih lauk ikan bakar atau ayam pop (tanpa kulit).'],
        'coach_alternatif': ['Pisahkan kuah gulai/santan dari nasi (jangan disiram).', 'Kurangi porsi nasi putih setengahnya.']
    },
    'Pisang Goreng': {
        'status': 'Tinggi Lemak & Karbohidrat',
        'kalori': '220.0', 'protein': '2.0', 'lemak': '11.0', 'karbo': '31.0',
        'coach_komentar': 'Pisang sebenarnya sehat, tetapi balutan tepung terigu dan proses deep-fry membuatnya menyerap minyak jenuh dan melipatgandakan kalori.',
        'coach_sayuran': ['Bukan untuk dimakan dengan sayur. Imbangi makan besar selanjutnya dengan ekstra serat.'],
        'coach_protein': ['Minum yogurt tawar (plain yogurt).', 'Segelas susu kedelai murni tanpa gula.'],
        'coach_alternatif': ['Konsumsi maksimal 1-2 potong saja.', 'Ganti metode dengan pisang rebus atau pisang panggang teflon.']
    },
    'Rendang': {
        'status': 'Tinggi Protein & Lemak Jenuh',
        'kalori': '320.0', 'protein': '22.0', 'lemak': '24.0', 'karbo': '5.0',
        'coach_komentar': 'Rendang adalah sumber protein hewani yang sangat padat. Namun proses masaknya yang lama membuat bumbu santan berubah menjadi lemak jenuh yang sulit dicerna.',
        'coach_sayuran': ['Salad daun selada segar.', 'Daun singkong rebus tawar.', 'Timun serut.'],
        'coach_protein': ['Protein sudah cukup tinggi, tidak perlu tambahan lauk hewani.'],
        'coach_alternatif': ['Pilih potongan daging tanpa lemak (gandik).', 'Batasi konsumsi bumbu/dedaknya yang berminyak.', 'Makan bersama nasi merah.']
    },
    'Sate': {
        'status': 'Tinggi Protein (Bergantung Daging)',
        'kalori': '250.0', 'protein': '20.0', 'lemak': '15.0', 'karbo': '10.0',
        'coach_komentar': 'Sate (ayam/kambing) merupakan asupan protein yang sangat baik jika dibakar tanpa gosong. Hati-hati dengan bumbu kacang atau kecap yang tinggi gula/lemak.',
        'coach_sayuran': ['Wajib konsumsi acar (timun, wortel, bawang merah) untuk menetralisir.', 'Tomat potong segar.'],
        'coach_protein': ['Tahu/tempe bacem bakar.'],
        'coach_alternatif': ['Minta sate daging murni tanpa selipan lemak/kulit.', 'Pisahkan bumbu kacang dan cukup dicocol sedikit.', 'Buang bagian yang gosong (karsinogenik).']
    },
    'Seblak': {
        'status': 'Sangat Tinggi Karbo, Lemak & Natrium',
        'kalori': '400.0', 'protein': '8.0', 'lemak': '18.0', 'karbo': '50.0',
        'coach_komentar': 'Seblak modern yang berisi kerupuk basah, makaroni, mie, dan sosis adalah tumpukan karbohidrat kompleks. Bumbu cabai dan penyedapnya memicu iritasi lambung dan retensi air.',
        'coach_sayuran': ['Sawi hijau, pakcoy, dan kol (perbanyak 3x lipat).', 'Jamur enoki/kancing.'],
        'coach_protein': ['Telur rebus.', 'Dada ayam suwir (bukan sosis/bakso olahan).'],
        'coach_alternatif': ['Kurangi level kepedasan untuk menjaga lambung.', 'Kurangi isian kerupuk/makaroni, ganti dengan sayur.', 'Jangan seruput habis kuahnya.']
    },
    'Siomay': {
        'status': 'Karbo & Lemak Tersembunyi',
        'kalori': '210.0', 'protein': '9.0', 'lemak': '8.0', 'karbo': '25.0',
        'coach_komentar': 'Siomay ikan yang dikukus itu sehat, namun seringkali adonannya lebih banyak tepung sagu daripada ikan. Bumbu kacangnya menyumbang kalori terbesar.',
        'coach_sayuran': ['Pilih varian pare dan kol kukus lebih banyak.', 'Tambahkan kentang kukus (sebagai pengganti nasi).'],
        'coach_protein': ['Tahu putih kukus.', 'Telur ayam rebus utuh.'],
        'coach_alternatif': ['Minta bumbu kacang dipisah dan cocol sedikit saja.', 'Hindari makan siomay bersamaan dengan nasi putih (double karbo).']
    },
    'Soto': {
        'status': 'Cukup Seimbang',
        'kalori': '200.0', 'protein': '15.0', 'lemak': '10.0', 'karbo': '12.0',
        'coach_komentar': 'Soto ayam kuah bening adalah salah satu makanan berkuah yang cukup sehat karena direbus. Soto daging/kuah santan kalori dan lemaknya lebih tinggi.',
        'coach_sayuran': ['Tauge segar, kol iris, dan tomat.', 'Perasan jeruk nipis (vitamin C membantu penyerapan zat besi).'],
        'coach_protein': ['Telur rebus utuh.', 'Dada ayam suwir ekstra.'],
        'coach_alternatif': ['Pilih soto kuah bening daripada soto bersantan/susu.', 'Jangan tambah kerupuk udang/emping berlebihan.', 'Konsumsi dengan nasi setengah porsi.']
    },
    'Tempe Tahu Goreng': {
        'status': 'Tinggi Protein Nabati & Lemak',
        'kalori': '250.0', 'protein': '12.0', 'lemak': '18.0', 'karbo': '10.0',
        'coach_komentar': 'Tempe dan Tahu adalah superfood nabati terbaik. Namun jika digoreng garing (Apalagi mendoan/bertepung), mereka menyerap minyak jenuh sangat banyak yang merusak nutrisi aslinya.',
        'coach_sayuran': ['Tumis kangkung terasi (sedikit minyak).', 'Sayur asem bening.', 'Pecel sayur (bumbu tipis).'],
        'coach_protein': ['Sudah kaya protein nabati. Boleh tambah pepes ikan.'],
        'coach_alternatif': ['Ubah cara olah menjadi: Tahu bacem kukus, tempe panggang teflon, atau sayur lodeh.', 'Tiriskan minyak dengan tisu dapur sebelum dimakan.']
    }
}

# KITA HANYA MEMUAT MODEL TERBAIK (EFFICIENTNETB0) UNTUK DEPLOYMENT
BEST_MODEL_NAME = 'EfficientNetB0'
BEST_MODEL_PATH = 'output_EfficientNetB0/best_model_EfficientNetB0.keras'

print("="*50)
print(f"[*] MEMUAT MODEL TERBAIK ({BEST_MODEL_NAME}) KE DALAM MEMORI...")
print("="*50)

best_model = None
if os.path.exists(BEST_MODEL_PATH):
    try:
        best_model = load_model(BEST_MODEL_PATH)
        print(f"    [OK] {BEST_MODEL_NAME} berhasil dimuat.")
    except Exception as e:
        print(f"    [ERROR] Gagal memuat {BEST_MODEL_NAME}: {e}")
else:
    print(f"    [WARNING] File {BEST_MODEL_PATH} tidak ditemukan.")

print("="*50)
print("[*] SERVER SIAP BERJALAN")
print("="*50)

def prepare_image(image_path, preprocess_func, target_size=(224, 224)):
    img = Image.open(image_path).convert('RGB')
    img = img.resize(target_size)
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_func(img_array)
    return img_array

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file gambar yang diunggah'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'File gambar kosong'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        if best_model is None:
            return jsonify({'error': f'Model {BEST_MODEL_NAME} belum dimuat.'}), 500
            
        try:
            preprocess_func = ef_preprocess # Gunakan preprocessor EfficientNetB0
            
            img_array = prepare_image(filepath, preprocess_func)
            
            start_time = time.time()
            predictions = best_model.predict(img_array)
            inference_time = time.time() - start_time
            
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx]) * 100
            
            # Batasan Prediksi OOD (Benda / Bukan Makanan)
            if confidence < 45.0:
                return jsonify({
                    'error': f'Gambar tidak dikenali (Keyakinan terlalu rendah: {confidence:.2f}%). Pastikan gambar yang diunggah adalah salah satu dari 15 kelas makanan Indonesia.',
                    'confidence': f"{confidence:.2f}%"
                }), 400
                
            predicted_class_name = CLASS_NAMES[predicted_class_idx]
            
            # Fetch Nutrition & Coach data
            nutrition_data = NUTRITION_DB.get(predicted_class_name, {})

            return jsonify({
                'success': True,
                'prediction': predicted_class_name,
                'confidence': f"{confidence:.2f}%",
                'inference_time': f"{inference_time:.3f}s",
                'model_used': BEST_MODEL_NAME,
                'image_url': f'/{filepath}',
                'nutrition': nutrition_data
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
