class AbilityGeneratorApp {
    constructor() {
        this.abilities = [];
        this.concept = '';
        this.editingAbilityIndex = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.testLLMConnection();
        this.updateGenerateButtonState();
    }

    bindEvents() {
        // Кнопки основного интерфейса
        document.getElementById('addAbilityBtn').addEventListener('click', () => this.showAbilityModal());
        document.getElementById('clearAbilitiesBtn').addEventListener('click', () => this.clearAbilities());
        document.getElementById('generateBtn').addEventListener('click', () => this.generateAbilities());
        document.getElementById('saveProjectBtn').addEventListener('click', () => this.saveProject());
        document.getElementById('loadProjectBtn').addEventListener('click', () => this.loadProject());
        document.getElementById('generateSummaryBtn').addEventListener('click', () => this.generateSummary());
        document.getElementById('characterConcept').addEventListener('input', (e) => {
            this.concept = e.target.value;
            this.updateGenerateButtonState();
        });

        // Модальное окно
        document.getElementById('close').addEventListener('click', () => this.hideAbilityModal());
        document.getElementById('addParamBtn').addEventListener('click', () => this.addParameterInput());
        document.getElementById('previewAbilityBtn').addEventListener('click', () => this.previewAbility());
        document.getElementById('saveAbilityBtn').addEventListener('click', () => this.saveAbilityConfig());
        document.getElementById('cancelAbilityBtn').addEventListener('click', () => this.hideAbilityModal());
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileSelect(e));

        // Закрытие модального окна при клике вне его
        document.addEventListener('click', (event) => {
            const modal = document.getElementById('parameterModal');
            const modalContent = document.querySelector('.modal-content');
            
            // Если клик внутри содержимого модального окна
            if (modal.style.display === 'block' && modalContent.contains(event.target)) {
                // НЕ останавливаем событие для кнопок закрытия
                const isCloseButton = event.target.classList.contains('close');
                const isCancelButton = event.target.id === 'cancelAbilityBtn';
                
                if (!isCloseButton && !isCancelButton) {
                    event.stopPropagation();
                }
            }
        });
    }

    async testLLMConnection() {
        try {
            const response = await fetch('/test_llm');
            const data = await response.json();
            
            const statusElement = document.getElementById('llmStatus');
            
            if (data.connected) {
                statusElement.className = 'llm-status connected';
                statusElement.innerHTML = '<i class="fas fa-check-circle"></i> Ollama подключен';
            } else {
                statusElement.className = 'llm-status disconnected';
                statusElement.innerHTML = '<i class="fas fa-times-circle"></i> Ollama недоступен';
            }
        } catch (error) {
            const statusElement = document.getElementById('llmStatus');
            statusElement.className = 'llm-status disconnected';
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Ошибка подключения';
        }
    }

    updateGenerateButtonState() {
        const generateBtn = document.getElementById('generateBtn');
        const hasConcept = this.concept.trim().length > 0;
        const hasAbilities = this.abilities.length > 0;
        
        generateBtn.disabled = !(hasConcept && hasAbilities);
    }

    showAbilityModal() {
        const modal = document.getElementById('parameterModal');
        modal.style.display = 'block';
        this.editingAbilityIndex = null;
        this.clearModalInputs();
        this.addParameterInput(); // Добавляем первый параметр по умолчанию
    }

    hideAbilityModal() {
        const modal = document.getElementById('parameterModal');
        modal.style.display = 'none';
    }

    clearModalInputs() {
        const paramInputs = document.querySelector('.param-inputs');
        paramInputs.innerHTML = '';
        const keywordsInput = document.getElementById('abilityKeywords');
        if (keywordsInput) {
            keywordsInput.value = '';
        }
    }

    addParameterInput() {
        const paramInputs = document.querySelector('.param-inputs');
        const paramCount = paramInputs.children.length;
        
        const paramDiv = document.createElement('div');
        paramDiv.className = 'param-config';
        paramDiv.innerHTML = `
            <div class="param-header">
                <h4>Параметр ${paramCount + 1}</h4>
                <button type="button" class="btn btn-secondary btn-sm" onclick="app.removeParameterInput(this)">
                    <i class="fas fa-trash"></i> Удалить
                </button>
            </div>
            <div class="param-inputs-grid">
                <div>
                    <label>Название параметра:</label>
                    <input type="text" placeholder="Например: сила выстрела" class="param-name-input">
                </div>
                <div>
                    <label>Модальное значение:</label>
                    <input type="number" value="5" class="param-mode-input">
                </div>
                <div>
                    <label>Минимальное значение:</label>
                    <input type="number" value="0" class="param-min-input">
                </div>
                <div>
                    <label>Максимальное значение:</label>
                    <input type="number" value="15" class="param-max-input">
                </div>
            </div>
            <div class="param-descriptions">
                <h5>Описания значений:</h5>
                <div class="description-input">
                    <label>При значении 0 (по умолчанию - параметр не используется):</label>
                    <input type="text" placeholder="Не оказывает влияния на силу выстрела" class="param-desc-0">
                </div>
                <div class="description-input">
                    <label>При минимальном значении (1):</label>
                    <input type="text" placeholder="Незначительно повышает силу выстрела" class="param-desc-1">
                </div>
                <div class="description-input">
                    <label>При модальном значении:</label>
                    <input type="text" placeholder="Повышает силу выстрела" class="param-desc-mode">
                </div>
                <div class="description-input">
                    <label>При максимальном значении:</label>
                    <input type="text" placeholder="Очень сильно повышает силу выстрела, делая его пробивающим большинство известных металлов" class="param-desc-max">
                </div>
            </div>
        `;
        
        paramInputs.appendChild(paramDiv);
    }

    removeParameterInput(button) {
        const paramDiv = button.closest('.param-config');
        paramDiv.remove();
    }

    async previewAbility() {
        const config = this.getAbilityConfigFromModal();
        if (!config) return;

        this.showLoading('Создание предварительного просмотра...');
        
        try {
            const response = await fetch('/preview_ability', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showPreviewResult(data.preview);
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Ошибка при создании предварительного просмотра');
        } finally {
            this.hideLoading();
        }
    }

    getAbilityConfigFromModal() {
        const paramInputs = document.querySelectorAll('.param-config');
        const parameters = {};

        const keywordsInput = document.getElementById('abilityKeywords');
        const keywords = keywordsInput ? keywordsInput.value.trim() : '';
        
        paramInputs.forEach(paramDiv => {
            const name = paramDiv.querySelector('.param-name-input').value.trim();
            if (!name) return;
            
            const min = parseInt(paramDiv.querySelector('.param-min-input').value) || 0;
            const mode = parseInt(paramDiv.querySelector('.param-mode-input').value) || 5;
            const max = parseInt(paramDiv.querySelector('.param-max-input').value) || 15;
            
            const descriptions = {};
            descriptions[0] = paramDiv.querySelector('.param-desc-0').value.trim();
            descriptions[1] = paramDiv.querySelector('.param-desc-1').value.trim();
            descriptions[mode] = paramDiv.querySelector('.param-desc-mode').value.trim();
            descriptions[max] = paramDiv.querySelector('.param-desc-max').value.trim();
            
            parameters[name] = {
                min: min,
                mode: mode,
                max: max,
                descriptions: descriptions
            };
        });
        
        if (Object.keys(parameters).length === 0) {
            this.showError('Необходимо добавить хотя бы один параметр');
            return null;
        }
        
        return { parameters: parameters, keywords: keywords };
    }

    showPreviewResult(preview) {
        // Создаем простое уведомление с предварительным просмотром
        const previewHtml = `
            <h4>Предварительный просмотр:</h4>
            <p><strong>Концепция:</strong> ${preview.concept_preview}</p>
            <div class="preview-params">
                <h5>Сгенерированные параметры:</h5>
                ${Object.entries(preview.parameters).map(([name, data]) => 
                    `<p><strong>${name}:</strong> ${data.value} - ${data.description}</p>`
                ).join('')}
            </div>
        `;
        
        this.showNotification(previewHtml, 'info');
    }

    saveAbilityConfig() {
        const config = this.getAbilityConfigFromModal();
        if (!config) return;

        if (this.editingAbilityIndex !== undefined && this.editingAbilityIndex !== null) {
            // Обновляем существующую способность
            this.abilities[this.editingAbilityIndex].config = config;
            this.editingAbilityIndex = null;
        } else {
            const abilityIndex = this.abilities.length;
            this.abilities.push({
                index: abilityIndex,
                config: config,
                id: `ability_${abilityIndex}`
            });
        }
        
        this.renderAbilitiesList();
        this.hideAbilityModal();
        this.updateGenerateButtonState();
    }

    renderAbilitiesList() {
        const container = document.getElementById('abilitiesContainer');
        container.innerHTML = '';
        
        this.abilities.forEach((ability, index) => {
            const keywords = ability.config.keywords || '';
            const keywordsHtml = keywords ? `
                <div class="ability-keywords">
                    <i class="fas fa-tags"></i> <strong>Ключевые слова:</strong> ${keywords}
                </div>
            ` : '';
            
            const abilityDiv = document.createElement('div');
            abilityDiv.className = 'ability-card';
            abilityDiv.innerHTML = `
                <div class="ability-header">
                    <div class="ability-title">Способность ${index + 1}</div>
                    <div class="ability-actions">
                        <button class="btn btn-secondary" onclick="app.editAbility(${index})">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-secondary" onclick="app.removeAbility(${index})">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </div>
                </div>
                ${keywordsHtml}
                <div class="ability-params">
                    ${Object.entries(ability.config.parameters).map(([name, config]) => `
                        <div class="param-item">
                            <div class="param-name">${name}</div>
                            <div class="param-values">
                                Диапазон: ${config.min} - ${config.max} (мода: ${config.mode})
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(abilityDiv);
        });
    }

    editAbility(index) {
        // Сохраняем индекс редактируемой способности
        this.editingAbilityIndex = index;
        
        // Показываем модальное окно
        const modal = document.getElementById('parameterModal');
        modal.style.display = 'block';
        this.clearModalInputs();
        
        // Загружаем данные способности
        const ability = this.abilities[index];
        if (!ability) return;
        
        // Устанавливаем ключевые слова
        const keywordsInput = document.getElementById('abilityKeywords');
        if (keywordsInput && ability.config.keywords) {
            keywordsInput.value = ability.config.keywords;
        }
        
        // Загружаем параметры
        const parameters = ability.config.parameters || {};
        for (const [name, config] of Object.entries(parameters)) {
            this.addParameterInputWithData(name, config);
        }
    }
    
    addParameterInputWithData(name, config) {
        const paramInputs = document.querySelector('.param-inputs');
        const paramCount = paramInputs.children.length;
        
        const paramDiv = document.createElement('div');
        paramDiv.className = 'param-config';
        paramDiv.innerHTML = `
            <div class="param-header">
                <h4>Параметр ${paramCount + 1}</h4>
                <button type="button" class="btn btn-secondary btn-sm" onclick="app.removeParameterInput(this)">
                    <i class="fas fa-trash"></i> Удалить
                </button>
            </div>
            <div class="param-inputs-grid">
                <div>
                    <label>Название параметра:</label>
                    <input type="text" value="${name}" class="param-name-input">
                </div>
                <div>
                    <label>Модальное значение:</label>
                    <input type="number" value="${config.mode || 5}" class="param-mode-input">
                </div>
                <div>
                    <label>Минимальное значение:</label>
                    <input type="number" value="${config.min || 0}" class="param-min-input">
                </div>
                <div>
                    <label>Максимальное значение:</label>
                    <input type="number" value="${config.max || 15}" class="param-max-input">
                </div>
            </div>
            <div class="param-descriptions">
                <h5>Описания значений:</h5>
                <div class="description-input">
                    <label>При значении 0 (по умолчанию - параметр не используется):</label>
                    <input type="text" value="${config.descriptions?.[0] || ''}" class="param-desc-0">
                </div>
                <div class="description-input">
                    <label>При минимальном значении (1):</label>
                    <input type="text" value="${config.descriptions?.[1] || ''}" class="param-desc-1">
                </div>
                <div class="description-input">
                    <label>При модальном значении:</label>
                    <input type="text" value="${config.descriptions?.[config.mode] || ''}" class="param-desc-mode">
                </div>
                <div class="description-input">
                    <label>При максимальном значении:</label>
                    <input type="text" value="${config.descriptions?.[config.max] || ''}" class="param-desc-max">
                </div>
            </div>
        `;
        
        paramInputs.appendChild(paramDiv);
    }

    removeAbility(index) {
        this.abilities.splice(index, 1);
        this.renderAbilitiesList();
        this.updateGenerateButtonState();
    }

    clearAbilities() {
        if (confirm('Вы уверены, что хотите удалить все способности?')) {
            this.abilities = [];
            this.renderAbilitiesList();
            this.updateGenerateButtonState();
        }
    }

    async generateAbilities() {
        const concept = this.concept.trim();
        if (!concept) {
            this.showError('Необходимо ввести описание концепции персонажа');
            return;
        }
        
        if (this.abilities.length === 0) {
            this.showError('Необходимо добавить хотя бы одну способность');
            return;
        }

        this.showLoading('Генерация способностей...');
        
        try {
            const response = await fetch('/generate_abilities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    concept: concept,
                    abilities: this.abilities.map(a => a.config)
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showResults(data.abilities);
                document.getElementById('resultsSection').style.display = 'block';
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Ошибка при генерации способностей');
        } finally {
            this.hideLoading();
        }
    }

    showResults(abilities) {
        const container = document.getElementById('abilitiesResults');
        container.innerHTML = '';
        
        abilities.forEach((ability, index) => {
            const chartId = `radarChart_${index}`;
            const keywords = ability.keywords || '';
            const keywordsHtml = keywords ? `
                <div class="result-keywords">
                    <i class="fas fa-tags"></i> <strong>Ключевые слова:</strong> ${keywords}
                </div>
            ` : '';
            
            const abilityDiv = document.createElement('div');
            abilityDiv.className = 'result-ability';
            abilityDiv.innerHTML = `
                <h4><i class="fas fa-star"></i> ${ability.name}</h4>
                <p>${ability.description}</p>
                ${keywordsHtml}
                <div class="ability-content-wrapper">
                    <div class="ability-params">
                        <h5>Параметры способности:</h5>
                        ${Object.entries(ability.parameters).map(([name, data]) => `
                            <div class="param-item">
                                <div class="param-name">${name}</div>
                                <div class="param-values">Значение: ${data.value} - ${data.description}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="radar-chart-container">
                        <h5><i class="fas fa-compass"></i> Роза ветров параметров</h5>
                        <canvas id="${chartId}"></canvas>
                    </div>
                </div>
                <button class="ability-regenerate" onclick="app.regenerateAbility(${index})">
                    <i class="fas fa-sync-alt"></i> Перегенерировать описание
                </button>
            `;
            container.appendChild(abilityDiv);
            this.createRadarChart(chartId, ability.parameters, ability.config);
        });
    }

    createRadarChart(chartId, parameters, config) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Подготовка данных для графика
        const labels = [];
        const values = [];
        const maxValues = [];
        
        for (const [name, data] of Object.entries(parameters)) {
            labels.push(name);
            values.push(data.value);
            
            // Получаем максимальное значение из конфигурации
            const rawConfig = data.raw_config || {};
            const maxVal = parseInt(rawConfig.max) || 15;
            maxValues.push(maxVal);
        }
        
        // Нормализуем значения для графика (0-100%)
        const normalizedValues = values.map((val, i) => {
            const maxVal = maxValues[i] || 15;
            return Math.round((val / maxVal) * 100);
        });
        
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Значение параметра (%)',
                    data: normalizedValues,
                    fill: true,
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const idx = context.dataIndex;
                                const actualValue = values[idx];
                                const maxVal = maxValues[idx];
                                return `${labels[idx]}: ${actualValue}/${maxVal} (${context.parsed.r}%)`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        pointLabels: {
                            color: '#4a5568',
                            font: {
                                size: 11,
                                weight: '500'
                            }
                        },
                        ticks: {
                            beginAtZero: true,
                            max: 100,
                            stepSize: 20,
                            color: '#718096',
                            backdropColor: 'transparent'
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                }
            }
        });
    }

    async regenerateAbility(index) {
        const concept = this.concept.trim();
        
        this.showLoading('Перегенерация описания способности...');
        
        try {
            const response = await fetch(`/regenerate_ability/${index}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ concept: concept })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showResults(data.abilities || [data.ability]);
                this.showNotification('Описание способности успешно перегенерировано', 'success');
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Ошибка при перегенерации способности');
        } finally {
            this.hideLoading();
        }
    }

    async generateSummary() {
        const concept = this.concept.trim();
        
        this.showLoading('Генерация описания персонажа...');
        
        try {
            const response = await fetch('/generate_summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ concept: concept })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const summaryDiv = document.getElementById('characterSummary');
                document.getElementById('summaryText').textContent = data.summary;
                summaryDiv.style.display = 'block';
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Ошибка при генерации описания персонажа');
        } finally {
            this.hideLoading();
        }
    }

    saveProject() {
        /**
         * Запускает скачивание файла, что инициирует диалог "Сохранить как..."
         */
        this.showLoading('Подготовка файла...');
        
        fetch('/save_project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Отправляем текущие данные проекта (abilities и concept)
            body: JSON.stringify({
                abilities: this.abilities,
                concept: document.getElementById('characterConcept').value,
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка HTTP: ' + response.statusText);
            }
            // Поскольку сервер возвращает файл, а не JSON, мы читаем его как Blob
            return response.blob(); 
        })
        .then(blob => {
            this.hideLoading();
            // Создаем ссылку для скачивания файла
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // Имя файла устанавливается заголовком 'download_name' на сервере, 
            // но здесь можно задать его как резерв
            a.download = 'project_ability_data.json'; 
            document.body.appendChild(a);
            a.click(); // Инициируем скачивание
            window.URL.revokeObjectURL(url);
            
            this.showNotification('Проект успешно выгружен! Выберите место для сохранения.', 'success');
        })
        .catch(error => {
            this.hideLoading();
            console.error('Save error:', error);
            this.showNotification('Ошибка сохранения проекта: ' + error.message, 'error');
        });
    }

    loadProject() {
        /**
         * Нажимает на скрытый input type="file" для открытия диалога выбора файла
         */
        document.getElementById('fileInput').click();
    }

    handleFileSelect(event) {
        /**
         * Обрабатывает выбранный пользователем файл
         */
        const file = event.target.files[0];
        if (!file) {
            return;
        }
        
        this.showLoading('Загрузка проекта...');
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                // Применяем данные проекта
                this.abilities = data.abilities || [];
                this.concept = data.concept || '';
                
                document.getElementById('characterConcept').value = this.concept;
                this.renderAbilitiesList(); // Обновляем интерфейс
                this.updateGenerateButtonState();
                
                this.showNotification(`Проект "${file.name}" успешно загружен!`, 'success');
            } catch (error) {
                console.error('Load error:', error);
                this.showNotification('Ошибка обработки файла: Убедитесь, что это корректный JSON-файл.', 'error');
            } finally {
                this.hideLoading();
                // Сбрасываем значение input, чтобы можно было загрузить тот же файл снова
                event.target.value = null; 
            }
        };
        
        reader.onerror = () => {
            this.hideLoading();
            this.showNotification('Ошибка чтения файла.', 'error');
        };

        reader.readAsText(file);
    }

    showLoading(text = 'Загрузка...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        loadingText.textContent = text;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Добавляем стили для уведомления
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
            padding: 15px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s ease;
        `;
        
        // Цвета для разных типов
        const colors = {
            success: '#48bb78',
            error: '#f56565',
            info: '#4299e1'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        // Анимация появления
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .notification-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .notification-content button {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                margin-left: 10px;
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(notification);
        
        // Автоматическое удаление через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Инициализация приложения
const app = new AbilityGeneratorApp();