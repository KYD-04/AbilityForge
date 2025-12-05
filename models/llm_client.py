import requests
import json
import logging
from typing import Dict, Any, Optional

class OllamaClient:
    """
    Клиент для работы с локальной LLM через Ollama API
    """
    
    def __init__(self, url: str = "http://localhost:11434"):
        self.base_url = url
        self.logger = logging.getLogger(__name__)
        
    def test_connection(self) -> bool:
        """
        Проверяет доступность Ollama сервера
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def get_available_models(self) -> list:
        """
        Получает список доступных моделей
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}")
            return []
    
    def generate_ability_description(self, 
                                     concept: str, 
                                     parameters: Dict[str, Any],
                                     keywords: str = '') -> Optional[Dict[str, str]]:
        """
        Генерирует название и описание способности на основе концепции и параметров
        """
        try:
            # Формируем промпт для генерации способности
            prompt = self._build_ability_prompt(concept, parameters, keywords)
            
            payload = {
                "model": "gpt-oss:latest",  # Можно сделать настраиваемым
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "num_predict": 2000,  # Увеличиваем максимальное количество токенов
                    "temperature": 0.8,   # Немного повышаем креативность
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('message', {}).get('content', '')
                return self._parse_ability_response(content)
            else:
                self.logger.error(f"LLM request failed with status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to generate ability description: {e}")
            return None
    
    def generate_character_summary(self, concept: str, abilities: list) -> Optional[str]:
        """
        Генерирует общее описание персонажа на основе концепции и способностей
        """
        try:
            prompt = self._build_summary_prompt(concept, abilities)
            
            payload = {
                "model": "llama3.1:latest",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('message', {}).get('content', '')
                return self._parse_summary_response(content)
            else:
                self.logger.error(f"LLM request failed with status {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to generate character summary: {e}")
            return None
    
    def _build_ability_prompt(self, 
                              concept: str, 
                              parameters: Dict[str, Any],
                              keywords: str = '') -> str:
        """
        Строит промпт для генерации описания способности
        """
        param_descriptions = []
        for param_name, param_data in parameters.items():
            value = param_data.get('value', 0)
            description = param_data.get('description', '')
            param_descriptions.append(f"'{param_name}': {description} (значение: {value})")
        
        params_text = "; ".join(param_descriptions)

        keywords_section = ""
        if keywords and keywords.strip():
            keywords_section = f"\nКлючевые слова для способности: {keywords}\nОбязательно учитывай эти ключевые слова при генерации описания способности.\n"
        
        prompt = f"""Ты генератор способностей для игровых персонажей. 

Концепция персонажа: {concept}

Ключевые слова для способности: {keywords_section}
Параметры способности: {params_text}

По этим данным придумай название для способности и текстовое описание, которое суммаризирует данную способность. Ответ на русском языке, строго по шаблону:
(название:'<название способности>';описание:'<описание способности>')

Не используй кавычки внутри названия и описания."""
        
        return prompt
    
    def _build_summary_prompt(self, concept: str, abilities: list) -> str:
        """
        Строит промпт для генерации общего описания персонажа
        """
        abilities_text = "\n".join([f"- {ability.get('name', 'Безымянная способность')}: {ability.get('description', 'Без описания')}" 
                                   for ability in abilities])
        
        prompt = f"""По данной информации выше, опиши в целом способности этого персонажа.

Концепция персонажа: {concept}

Способности:
{abilities_text}

Ответ строго по шаблону (суммаризация:'<общее описание>')"""
        
        return prompt
    
    def _parse_ability_response(self, content: str) -> Optional[Dict[str, str]]:
        """
        Парсит ответ LLM для способности
        """
        try:
            # Ищем паттерн (название:'...';описание:'...')
            import re
            pattern = r'\(название:\'([^\']*)\';описание:\'([\s\S]*?)\'\)'
            match = re.search(pattern, content)
            
            if match:
                return {
                    'name': match.group(1),
                    'description': match.group(2)
                }
            else:
                # Если не удалось найти паттерн, пытаемся извлечь любым способом
                lines = content.split('\n')
                for line in lines:
                    if 'название' in line.lower() or 'способность' in line.lower():
                        # Простая эвристика для извлечения
                        return {
                            'name': 'Сгенерированная способность',
                            'description': content.strip()
                        }
                return None
        except Exception as e:
            self.logger.error(f"Failed to parse ability response: {e}")
            return None
    
    def _parse_summary_response(self, content: str) -> Optional[str]:
        """
        Парсит ответ LLM для суммаризации
        """
        try:
            # Ищем паттерн (суммаризация:'...')
            import re
            pattern = r'\(суммаризация:\'([^\']*)\'\)'
            match = re.search(pattern, content)
            
            if match:
                return match.group(1)
            else:
                # Если не удалось найти паттерн, возвращаем начало ответа
                return content[:300] + '...' if len(content) > 300 else content
        except Exception as e:
            self.logger.error(f"Failed to parse summary response: {e}")
            return None