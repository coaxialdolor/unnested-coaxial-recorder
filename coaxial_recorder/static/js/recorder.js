// Recording functionality for Voice Dataset Manager

class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.stream = null;
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.animationId = null;
        
        // DOM elements
        this.recordButton = document.getElementById('recordButton');
        this.stopButton = document.getElementById('stopButton');
        this.saveButton = document.getElementById('saveButton');
        this.discardButton = document.getElementById('discardButton');
        this.recordingStatus = document.getElementById('recordingStatus');
        this.recordingTimer = document.getElementById('recordingTimer');
        this.audioVisualizer = document.getElementById('audioVisualizer');
        this.currentPrompt = document.getElementById('currentPrompt');
        
        // State
        this.recordingStartTime = null;
        this.currentAudioBlob = null;
        this.currentVoiceProfile = null;
        this.currentPromptList = null;
        this.currentPromptIndex = 0;
        this.prompts = [];
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        if (this.recordButton) {
            this.recordButton.addEventListener('click', () => this.startRecording());
        }
        if (this.stopButton) {
            this.stopButton.addEventListener('click', () => this.stopRecording());
        }
        if (this.saveButton) {
            this.saveButton.addEventListener('click', () => this.saveRecording());
        }
        if (this.discardButton) {
            this.discardButton.addEventListener('click', () => this.discardRecording());
        }
        
        // Voice profile and prompt list selection
        const voiceProfileSelect = document.getElementById('voiceProfileSelect');
        const promptListSelect = document.getElementById('promptListSelect');
        
        if (voiceProfileSelect) {
            voiceProfileSelect.addEventListener('change', () => this.loadVoiceProfile());
        }
        if (promptListSelect) {
            promptListSelect.addEventListener('change', () => this.loadPromptList());
        }
    }
    
    async loadVoiceProfile() {
        const voiceProfileSelect = document.getElementById('voiceProfileSelect');
        if (voiceProfileSelect && voiceProfileSelect.value) {
            this.currentVoiceProfile = voiceProfileSelect.value;
            try {
                const response = await fetch(`/api/voice-profiles/${this.currentVoiceProfile}`);
                const data = await response.json();
                console.log('Loaded voice profile:', data);
                
                // Populate prompt list dropdown with downloadable options
                await this.populatePromptListDropdown();
            } catch (error) {
                console.error('Error loading voice profile:', error);
                VoiceDatasetManager.showAlert('Error loading voice profile', 'danger');
            }
        }
    }
    
    async loadPromptList() {
        const promptListSelect = document.getElementById('promptListSelect');
        if (promptListSelect && promptListSelect.value) {
            this.currentPromptList = promptListSelect.value;
            
            try {
                // First try to load existing prompt list
                const response = await fetch(`/api/prompt-lists/${this.currentPromptList}`);
                
                if (response.ok) {
                    const data = await response.json();
                    this.prompts = data.prompts || [];
                    this.currentPromptIndex = 0;
                    this.displayCurrentPrompt();
                    this.updateProgress();
                } else if (response.status === 404) {
                    // Prompt list doesn't exist, check if we should download it
                    await this.downloadPromptListIfNeeded();
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                console.error('Error loading prompt list:', error);
                VoiceDatasetManager.showAlert('Error loading prompt list', 'danger');
            }
        }
    }
    
    async downloadPromptListIfNeeded() {
        // Check if this is a downloadable prompt list
        const promptListSelect = document.getElementById('promptListSelect');
        const selectedOption = promptListSelect.options[promptListSelect.selectedIndex];
        
        if (selectedOption && selectedOption.dataset.downloadable === 'true') {
            // Show download dialog
            const downloadModal = new bootstrap.Modal(document.getElementById('downloadPromptModal'));
            downloadModal.show();
            
            // Set up the download form
            const downloadForm = document.getElementById('downloadPromptForm');
            downloadForm.onsubmit = async (e) => {
                e.preventDefault();
                
                const formData = new FormData(downloadForm);
                formData.append('prompt_list_name', this.currentPromptList);
                formData.append('source', selectedOption.dataset.source);
                formData.append('language', selectedOption.dataset.language);
                formData.append('category', selectedOption.dataset.category);
                
                try {
                    const downloadResponse = await fetch(`/api/profiles/${this.currentVoiceProfile}/prompts/download`, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (downloadResponse.ok) {
                        const result = await downloadResponse.json();
                        VoiceDatasetManager.showAlert(result.message, 'success');
                        downloadModal.hide();
                        
                        // Now try to load the downloaded prompt list
                        const loadResponse = await fetch(`/api/prompt-lists/${this.currentPromptList}`);
                        const data = await loadResponse.json();
                        this.prompts = data.prompts || [];
                        this.currentPromptIndex = 0;
                        this.displayCurrentPrompt();
                        this.updateProgress();
                    } else {
                        const error = await downloadResponse.json();
                        VoiceDatasetManager.showAlert(error.detail || 'Download failed', 'danger');
                    }
                } catch (error) {
                    console.error('Error downloading prompt list:', error);
                    VoiceDatasetManager.showAlert('Error downloading prompt list', 'danger');
                }
            };
        } else {
            VoiceDatasetManager.showAlert('Prompt list not found', 'warning');
        }
    }
    
    displayCurrentPrompt() {
        if (this.currentPrompt && this.prompts.length > 0 && this.currentPromptIndex < this.prompts.length) {
            const prompt = this.prompts[this.currentPromptIndex];
            this.currentPrompt.innerHTML = `
                <div class="text-center">
                    <h5>Prompt ${this.currentPromptIndex + 1} of ${this.prompts.length}</h5>
                    <p class="lead mb-3">${prompt}</p>
                    <small class="text-muted">Click Record to start recording this prompt</small>
                </div>
            `;
        } else if (this.prompts.length === 0) {
            this.currentPrompt.innerHTML = `
                <div class="text-center text-muted">
                    <h5>No prompts loaded</h5>
                    <p>Select a prompt list to begin recording</p>
                </div>
            `;
        } else {
            this.currentPrompt.innerHTML = `
                <div class="text-center text-success">
                    <h5>All prompts completed!</h5>
                    <p>You have recorded all prompts in this list.</p>
                </div>
            `;
        }
    }
    
    updateProgress() {
        const progressBar = document.getElementById('recordingProgress');
        const progressText = document.getElementById('progressText');
        
        if (progressBar && this.prompts.length > 0) {
            const progress = ((this.currentPromptIndex + 1) / this.prompts.length) * 100;
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${this.currentPromptIndex + 1} / ${this.prompts.length}`;
        }
    }
    
    async startRecording() {
        if (!this.currentVoiceProfile || !this.currentPromptList) {
            VoiceDatasetManager.showAlert('Please select both a voice profile and prompt list', 'warning');
            return;
        }
        
        if (this.currentPromptIndex >= this.prompts.length) {
            VoiceDatasetManager.showAlert('All prompts have been completed', 'info');
            return;
        }
        
        try {
            // Get user media
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    sampleRate: 44100,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // Set up audio context for visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            
            const source = this.audioContext.createMediaStreamSource(this.stream);
            source.connect(this.analyser);
            
            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.currentAudioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.onRecordingComplete();
            };
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            // Update UI
            this.recordButton.disabled = true;
            this.stopButton.disabled = false;
            this.recordingStatus.innerHTML = '<i class="fas fa-circle text-danger me-2"></i>Recording...';
            this.recordingStatus.className = 'badge bg-danger';
            
            // Start timer
            this.startTimer();
            
            // Start visualization
            this.startVisualization();
            
            VoiceDatasetManager.showAlert('Recording started', 'success');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            VoiceDatasetManager.showAlert('Error starting recording. Please check microphone permissions.', 'danger');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop stream
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
            
            // Stop audio context
            if (this.audioContext) {
                this.audioContext.close();
            }
            
            // Stop timer
            this.stopTimer();
            
            // Stop visualization
            this.stopVisualization();
            
            // Update UI
            this.recordButton.disabled = false;
            this.stopButton.disabled = true;
            this.recordingStatus.innerHTML = '<i class="fas fa-check-circle text-success me-2"></i>Recording complete';
            this.recordingStatus.className = 'badge bg-success';
            
            VoiceDatasetManager.showAlert('Recording stopped', 'info');
        }
    }
    
    onRecordingComplete() {
        this.saveButton.disabled = false;
        this.discardButton.disabled = false;
        
        // Show recording preview
        if (this.currentAudioBlob) {
            const audioUrl = URL.createObjectURL(this.currentAudioBlob);
            const audioElement = document.createElement('audio');
            audioElement.controls = true;
            audioElement.src = audioUrl;
            audioElement.className = 'w-100 mt-3';
            
            const previewDiv = document.getElementById('recordingPreview');
            if (previewDiv) {
                previewDiv.innerHTML = '';
                previewDiv.appendChild(audioElement);
                
                // Add audio analysis
                VoiceDatasetManager.analyzeAudio(this.currentAudioBlob)
                    .then(analysis => {
                        const analysisDiv = document.createElement('div');
                        analysisDiv.className = 'mt-2 small text-muted';
                        analysisDiv.innerHTML = `
                            Duration: ${VoiceDatasetManager.formatDuration(analysis.duration)} | 
                            Volume: ${analysis.volume.toFixed(1)} dB
                        `;
                        previewDiv.appendChild(analysisDiv);
                    })
                    .catch(error => {
                        console.error('Audio analysis error:', error);
                    });
            }
        }
    }
    
    async saveRecording() {
        if (!this.currentAudioBlob || !this.currentVoiceProfile || !this.currentPromptList) {
            VoiceDatasetManager.showAlert('Missing required data for saving', 'warning');
            return;
        }
        
        const currentPrompt = this.prompts[this.currentPromptIndex];
        const formData = new FormData();
        formData.append('audio', this.currentAudioBlob, `recording_${Date.now()}.wav`);
        formData.append('voice_profile_id', this.currentVoiceProfile);
        formData.append('prompt_list_id', this.currentPromptList);
        formData.append('prompt_text', currentPrompt);
        formData.append('prompt_index', this.currentPromptIndex.toString());
        
        try {
            const response = await fetch('/api/recordings', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                VoiceDatasetManager.showAlert('Recording saved successfully!', 'success');
                
                // Add to recording history
                this.addToRecordingHistory(result);
                
                // Move to next prompt
                this.currentPromptIndex++;
                this.displayCurrentPrompt();
                this.updateProgress();
                
                // Reset recording UI
                this.resetRecordingUI();
                
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save recording');
            }
            
        } catch (error) {
            console.error('Error saving recording:', error);
            VoiceDatasetManager.showAlert(`Error saving recording: ${error.message}`, 'danger');
        }
    }
    
    discardRecording() {
        this.currentAudioBlob = null;
        this.resetRecordingUI();
        VoiceDatasetManager.showAlert('Recording discarded', 'info');
    }
    
    resetRecordingUI() {
        this.saveButton.disabled = true;
        this.discardButton.disabled = true;
        this.recordButton.disabled = false;
        this.recordingStatus.innerHTML = '<i class="fas fa-microphone text-muted me-2"></i>Ready to record';
        this.recordingStatus.className = 'badge bg-secondary';
        this.recordingTimer.textContent = '00:00';
        
        const previewDiv = document.getElementById('recordingPreview');
        if (previewDiv) {
            previewDiv.innerHTML = '';
        }
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            if (this.recordingStartTime) {
                const elapsed = Date.now() - this.recordingStartTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                this.recordingTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    startVisualization() {
        const canvas = this.audioVisualizer;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
        
        const draw = () => {
            if (!this.isRecording) return;
            
            this.animationId = requestAnimationFrame(draw);
            
            if (this.analyser && this.dataArray) {
                this.analyser.getByteFrequencyData(this.dataArray);
                
                ctx.fillStyle = 'rgb(248, 249, 250)';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                const barWidth = (canvas.width / this.dataArray.length) * 2.5;
                let barHeight;
                let x = 0;
                
                for (let i = 0; i < this.dataArray.length; i++) {
                    barHeight = (this.dataArray[i] / 255) * canvas.height;
                    
                    const r = Math.floor(barHeight + 25);
                    const g = Math.floor(250 * (i / this.dataArray.length));
                    const b = 50;
                    
                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                    ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                    
                    x += barWidth + 1;
                }
            }
        };
        
        draw();
    }
    
    stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        const canvas = this.audioVisualizer;
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
    
    addToRecordingHistory(recording) {
        const historyDiv = document.getElementById('recordingHistory');
        if (!historyDiv) return;
        
        const recordingElement = document.createElement('div');
        recordingElement.className = 'list-group-item';
        recordingElement.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">Prompt ${recording.prompt_index + 1}</h6>
                <small class="text-muted">${new Date(recording.created_at).toLocaleTimeString()}</small>
            </div>
            <p class="mb-1 small">${recording.prompt_text}</p>
            <small class="text-muted">Duration: ${VoiceDatasetManager.formatDuration(recording.duration)}</small>
        `;
        
        // Insert at top
        historyDiv.insertBefore(recordingElement, historyDiv.firstChild);
        
        // Keep only last 10 recordings
        while (historyDiv.children.length > 10) {
            historyDiv.removeChild(historyDiv.lastChild);
        }
    }
    
    async populatePromptListDropdown() {
        const promptListSelect = document.getElementById('promptListSelect');
        if (!promptListSelect) return;
        
        // Clear existing options
        promptListSelect.innerHTML = '<option value="">Select a prompt list...</option>';
        
        try {
            // Get available prompt sources
            const response = await fetch('/api/prompt-sources');
            if (!response.ok) throw new Error('Failed to fetch prompt sources');
            
            const data = await response.json();
            
            // Add existing prompt lists from current profile
            if (this.currentVoiceProfile) {
                try {
                    const profileResponse = await fetch(`/api/voice-profiles/${this.currentVoiceProfile}`);
                    if (profileResponse.ok) {
                        const profileData = await profileResponse.json();
                        if (profileData.prompt_lists && profileData.prompt_lists.length > 0) {
                            const existingGroup = document.createElement('optgroup');
                            existingGroup.label = 'Existing Prompt Lists';
                            
                            profileData.prompt_lists.forEach(promptList => {
                                const option = document.createElement('option');
                                option.value = `${this.currentVoiceProfile}/${promptList}`;
                                option.textContent = promptList;
                                existingGroup.appendChild(option);
                            });
                            
                            promptListSelect.appendChild(existingGroup);
                        }
                    }
                } catch (error) {
                    console.warn('Could not load existing prompt lists:', error);
                }
            }
            
            // Add downloadable prompt sources
            data.sources.forEach(source => {
                const sourceGroup = document.createElement('optgroup');
                sourceGroup.label = source.name;
                
                source.languages.forEach(lang => {
                    source.categories.forEach(category => {
                        const option = document.createElement('option');
                        const optionValue = `download_${source.id}_${lang.code}_${category}`;
                        option.value = optionValue;
                        option.textContent = `${lang.display} - ${category}`;
                        option.dataset.downloadable = 'true';
                        option.dataset.source = source.id;
                        option.dataset.language = lang.code;
                        option.dataset.category = category;
                        sourceGroup.appendChild(option);
                    });
                });
                
                promptListSelect.appendChild(sourceGroup);
            });
            
        } catch (error) {
            console.error('Error populating prompt list dropdown:', error);
            VoiceDatasetManager.showAlert('Error loading prompt sources', 'danger');
        }
    }
}

// Initialize recorder when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('recordButton')) {
        window.audioRecorder = new AudioRecorder();
    }
});