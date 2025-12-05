from flask import Flask, render_template, request, jsonify, session, send_file # Добавляем send_file
import json
import logging
import io
from models.llm_client import OllamaClient
from models.ability_generator import AbilityGenerator

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'ability_generator_secret_key_2025'

# Инициализация компонентов
llm_client = OllamaClient()
ability_generator = AbilityGenerator(llm_client)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/test_llm', methods=['POST', 'GET'])
def test_llm():
    """Тестирование соединения с LLM"""
    try:
        # Get URL from request or use default
        if request.method == 'POST':
            data = request.get_json() or {}
            ollama_url = data.get('url', 'http://localhost:11434')
        else:
            ollama_url = 'http://localhost:11434'
        
        # Create temporary client with the specified URL
        from models.llm_client import OllamaClient
        temp_client = OllamaClient(url=ollama_url)
        
        is_connected = temp_client.test_connection()
        if is_connected:
            models = temp_client.get_available_models()
            return jsonify({
                'status': 'success',
                'connected': True,
                'models': models,
                'message': 'Соединение с Ollama успешно'
            })
        else:
            return jsonify({
                'status': 'error',
                'connected': False,
                'message': 'Не удается подключиться к Ollama. Убедитесь, что сервер запущен.'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'connected': False,
            'message': f'Ошибка подключения: {str(e)}'
        })

@app.route('/preview_ability', methods=['POST'])
def preview_ability():
    """Предварительный просмотр способности"""
    try:
        config = request.json
        preview = ability_generator.get_ability_preview(config)
        return jsonify({
            'status': 'success',
            'preview': preview
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка создания предварительного просмотра: {str(e)}'
        })

@app.route('/generate_abilities', methods=['POST'])
def generate_abilities():
    """Генерация способностей"""
    try:
        data = request.json
        concept = data.get('concept', '')
        ability_configs = data.get('abilities', [])
        
        if not concept:
            return jsonify({
                'status': 'error',
                'message': 'Описание концепции персонажа обязательно'
            })
        
        if not ability_configs:
            return jsonify({
                'status': 'error',
                'message': 'Необходимо указать хотя бы одну способность'
            })
        
        # Получаем URL из настроек (если передан)
        ollama_url = data.get('ollama_url', 'http://localhost:11434')
        
        # Создаем временный клиент с правильным URL
        from models.llm_client import OllamaClient
        temp_llm_client = OllamaClient(url=ollama_url)
        
        # Создаем временный генератор с правильным клиентом
        temp_generator = AbilityGenerator(temp_llm_client)
        
        # Генерируем способности
        abilities = temp_generator.generate_abilities(concept, ability_configs)
        
        return jsonify({
            'status': 'success',
            'abilities': abilities,
            'message': f'Успешно сгенерировано {len(abilities)} способностей'
        })
        
    except Exception as e:
        logger.error(f"Error generating abilities: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка генерации способностей: {str(e)}'
        })

@app.route('/regenerate_ability/<int:ability_index>', methods=['POST'])
def regenerate_ability(ability_index):
    """Перегенерация конкретной способности"""
    try:
        data = request.json
        concept = data.get('concept', '')
        
        if not concept:
            return jsonify({
                'status': 'error',
                'message': 'Концепция персонажа обязательна для перегенерации'
            })
        
        # Получаем URL из настроек (если передан)
        ollama_url = data.get('ollama_url', 'http://localhost:11434')
        
        # Создаем временный клиент с правильным URL
        from models.llm_client import OllamaClient
        temp_llm_client = OllamaClient(url=ollama_url)
        
        # Создаем временный генератор с правильным клиентом
        temp_generator = AbilityGenerator(temp_llm_client)
        
        # Сначала генерируем способности, чтобы получить исходные данные
        # Получаем данные о ранее сгенерированных способностях из сессии или другого источника
        # Для простоты используем существующий генератор и обновляем его клиент
        global ability_generator
        ability_generator.llm_client = temp_llm_client
        
        updated_ability = ability_generator.regenerate_ability_description(ability_index, concept)
        
        if updated_ability != {}:
            return jsonify({
                'status': 'success',
                'ability': updated_ability,
                'message': 'Способность успешно перегенерирована'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Не удалось перегенерировать способность'
            })
            
    except Exception as e:
        logger.error(f"Error regenerating ability: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка перегенерации способности: {str(e)}'
        })

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    """Генерация общего описания персонажа"""
    try:
        data = request.json
        concept = data.get('concept', '')
        
        # Получаем URL из настроек (если передан)
        ollama_url = data.get('ollama_url', 'http://localhost:11434')
        
        # Обновляем клиент глобального генератора
        from models.llm_client import OllamaClient
        temp_llm_client = OllamaClient(url=ollama_url)
        global ability_generator
        ability_generator.llm_client = temp_llm_client
        
        summary = ability_generator.generate_character_summary(concept)
        
        return jsonify({
            'status': 'success',
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка генерации описания: {str(e)}'
        })

@app.route('/save_project', methods=['POST'])
def save_project():
    """Отправляет данные проекта в браузер для сохранения через диалог"""
    try:
        data = request.json
        
        # 1. Сериализуем данные проекта в строку JSON
        json_data = json.dumps(data, indent=4, ensure_ascii=False)
        
        # 2. Создаем виртуальный файл в памяти (чтобы не сохранять его на сервере)
        buffer = io.BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0)
        
        # 3. Отправляем виртуальный файл обратно в браузер
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name='project_ability_data.json' # Предлагаемое имя файла
        )
        
    except Exception as e:
        logger.error(f"Ошибка подготовки файла для сохранения: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Ошибка сохранения: {str(e)}'
        })

# @app.route('/load_project', methods=['GET'])
# def load_project():
#     """Загрузка проекта"""
#     try:
#         project_data = session.get('project_data', {})
        
#         if project_data:
#             return jsonify({
#                 'status': 'success',
#                 'project': project_data
#             })
#         else:
#             return jsonify({
#                 'status': 'error',
#                 'message': 'Сохраненный проект не найден'
#             })
            
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': f'Ошибка загрузки: {str(e)}'
#         })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)