document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const uploadSection = document.getElementById('upload-section');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const imagePreview = document.getElementById('image-preview');
    const btnRemoveImage = document.getElementById('btn-remove-image');
    const btnPredict = document.getElementById('btn-predict');
    const btnReset = document.getElementById('btn-reset');
    
    const loadingOverlay = document.getElementById('loading-overlay');
    const resultPanel = document.getElementById('result-panel');
    
    // Result elements
    const resultImage = document.getElementById('result-image');
    const primaryClass = document.getElementById('primary-class');
    const primaryConfidence = document.getElementById('primary-confidence');
    const confidenceStrong = document.getElementById('confidence-strong');
    const classStrong = document.getElementById('class-strong');
    const inferenceTime = document.getElementById('inference-time');

    // Nutrition & Coach Elements
    const nutritionStatus = document.getElementById('nutrition-status');
    const nutritionValues = document.getElementById('nutrition-values');
    const coachKomentar = document.getElementById('coach-komentar');
    const coachSayuran = document.getElementById('coach-sayuran');
    const coachProtein = document.getElementById('coach-protein');
    const coachAlternatif = document.getElementById('coach-alternatif');

    // Error Modal Elements
    const errorModal = document.getElementById('error-modal');
    const errorModalMessage = document.getElementById('error-modal-message');
    const errorModalGauge = document.getElementById('error-modal-gauge');
    const errorModalGaugeFill = document.getElementById('error-modal-gauge-fill');
    const errorModalGaugeValue = document.getElementById('error-modal-gauge-value');
    const errorModalGaugeHint = document.getElementById('error-modal-gauge-hint');
    const btnCloseModal = document.getElementById('btn-close-modal');

    let currentFile = null;

    // ===== ERROR MODAL FUNCTIONS =====
    function showErrorModal(message, confidence) {
        // Set a more friendly, actionable message
        errorModalMessage.textContent = message || 'Coba foto ulang dengan pencahayaan yang lebih baik, atau pastikan objeknya adalah makanan Indonesia.';
        
        if (confidence) {
            // Parse the numeric value from "28.86%"
            const numVal = parseFloat(confidence);
            
            errorModalGauge.classList.remove('hidden');
            errorModalGaugeValue.textContent = confidence;
            
            // Determine human-friendly hint
            let hint = 'Terlalu rendah untuk diklasifikasikan';
            if (numVal >= 50) hint = 'Hampir mirip, tapi belum cukup yakin';
            else if (numVal >= 30) hint = 'Sedikit mirip, tapi belum cukup meyakinkan';
            errorModalGaugeHint.textContent = hint;
            
            // Animate the gauge fill after a tiny delay
            setTimeout(() => {
                errorModalGaugeFill.style.width = numVal + '%';
            }, 100);
        } else {
            errorModalGauge.classList.add('hidden');
            errorModalGaugeFill.style.width = '0%';
        }

        errorModal.classList.remove('hidden', 'closing');
        lucide.createIcons();
        document.body.style.overflow = 'hidden';
    }

    function closeErrorModal() {
        errorModal.classList.add('closing');
        setTimeout(() => {
            errorModal.classList.add('hidden');
            errorModal.classList.remove('closing');
            errorModalGaugeFill.style.width = '0%';
            document.body.style.overflow = '';
        }, 300);
    }

    btnCloseModal.addEventListener('click', closeErrorModal);

    // Close modal when clicking overlay background
    errorModal.addEventListener('click', (e) => {
        if (e.target === errorModal) closeErrorModal();
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !errorModal.classList.contains('hidden')) {
            closeErrorModal();
        }
    });

    // ===== FILE HANDLING =====
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            showErrorModal('File yang diunggah bukan gambar. Harap unggah file berformat JPG, PNG, atau WEBP.');
            return;
        }

        currentFile = file;
        const reader = new FileReader();
        
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            resultImage.src = e.target.result;
            
            uploadPlaceholder.classList.add('hidden');
            imagePreview.classList.remove('hidden');
            btnRemoveImage.classList.remove('hidden');
            
            btnPredict.classList.remove('hidden');
            resultPanel.classList.add('hidden');
        };
        
        reader.readAsDataURL(file);
    }

    btnRemoveImage.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUI();
    });

    btnReset.addEventListener('click', () => {
        resetUI();
        window.scrollTo(0, 0);
    });

    function resetUI() {
        currentFile = null;
        fileInput.value = '';
        imagePreview.src = '';
        
        // Show upload section back
        uploadSection.classList.remove('hidden');
        uploadPlaceholder.classList.remove('hidden');
        imagePreview.classList.add('hidden');
        btnRemoveImage.classList.add('hidden');
        
        btnPredict.classList.add('hidden');
        resultPanel.classList.add('hidden');
    }

    btnPredict.addEventListener('click', () => {
        if (currentFile) doPrediction();
    });

    async function doPrediction() {
        const formData = new FormData();
        formData.append('file', currentFile);

        loadingOverlay.classList.remove('hidden');
        btnPredict.disabled = true;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                showErrorModal(data.error, data.confidence || null);
                return;
            }

            // Update Prediction UI
            primaryClass.textContent = data.prediction;
            primaryConfidence.textContent = data.confidence;
            confidenceStrong.textContent = data.confidence;
            classStrong.textContent = data.prediction;
            inferenceTime.textContent = `Waktu Inferensi: ${data.inference_time}`;

            // Update Nutrition & Coach UI
            if (data.nutrition && Object.keys(data.nutrition).length > 0) {
                const nut = data.nutrition;
                
                nutritionStatus.textContent = nut.status;
                nutritionValues.innerHTML = `Kalori: <strong>${nut.kalori} kkal</strong> | Protein: <strong>${nut.protein}g</strong> | Lemak: <strong>${nut.lemak}g</strong> | Karbo: <strong>${nut.karbo}g</strong>`;
                
                coachKomentar.innerHTML = nut.coach_komentar;
                
                // Helper function to populate lists
                const populateList = (element, arr) => {
                    element.innerHTML = '';
                    arr.forEach(item => {
                        const li = document.createElement('li');
                        // highlight the first word/bolding
                        li.innerHTML = item.replace(/^(.*?)\s/, '<span>$1 </span>');
                        element.appendChild(li);
                    });
                };

                populateList(coachSayuran, nut.coach_sayuran);
                populateList(coachProtein, nut.coach_protein);
                populateList(coachAlternatif, nut.coach_alternatif);
            } else {
                nutritionValues.textContent = "Data gizi tidak tersedia untuk makanan ini.";
            }

            // Hide upload section & show results (prevent double image)
            uploadSection.classList.add('hidden');
            resultPanel.classList.remove('hidden');
            btnPredict.classList.add('hidden');
            
            // Scroll to results smoothly
            setTimeout(() => {
                resultPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);

        } catch (error) {
            console.error(error);
            showErrorModal('Terjadi kesalahan saat memproses gambar. Silakan coba lagi.');
        } finally {
            loadingOverlay.classList.add('hidden');
            btnPredict.disabled = false;
        }
    }
});
