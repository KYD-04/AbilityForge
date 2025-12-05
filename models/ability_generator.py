import random
import math
from typing import Dict, List, Any, Tuple
# from models.llm_client import OllamaClient # Предполагаем, что этот импорт есть

class AbilityGenerator:
    """
    Основной генератор способностей персонажей
    """
    
    def __init__(self, llm_client):
        # Тип OllamaClient предполагается из контекста
        self.llm_client = llm_client
        self.generated_abilities = []
    
    def generate_abilities(self, concept: str, ability_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Генерирует набор способностей на основе концепции и конфигураций
        """
        self.generated_abilities = []
        
        for config in ability_configs:
            ability = self._generate_single_ability(concept, config)
            if ability:
                self.generated_abilities.append(ability)
        
        return self.generated_abilities
    
    def _generate_single_ability(self, concept: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует одну способность
        """
        # Генерируем случайные параметры для способности
        parameters = self._generate_random_parameters(config.get('parameters', {}))

        keywords = config.get('keywords', '')
        
        # Получаем описание от LLM
        ability_description = self.llm_client.generate_ability_description(concept, parameters, keywords)
        
        if ability_description:
            return {
                'name': ability_description['name'],
                'description': ability_description['description'],
                'parameters': parameters,
                'keywords': keywords,
                'config': config
            }
        else:
            # Фолбек если LLM недоступен
            return {
                'name': 'Сгенерированная способность',
                'description': f'Способность с параметрами: {parameters}',
                'parameters': parameters,
                'keywords': keywords,
                'config': config
            }
    
    def _generate_random_parameters(self, parameter_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Генерирует случайные значения параметров на основе конфигурации
        
        Args:
            parameter_configs: Словарь с конфигурациями параметров
            
        Returns:
            Словарь со сгенерированными параметрами
        """
        generated_params = {}
        
        for param_name, config in parameter_configs.items():
            
            # --- ИСПРАВЛЕННЫЙ БЛОК ДЛЯ ПРЕОБРАЗОВАНИЯ ТИПОВ ---
            try:
                # 1. Извлекаем и принудительно преобразуем min/max в int
                # Значения из веб-формы (config) всегда приходят как строки.
                min_val = int(config.get('min', 0))
                max_val = int(config.get('max', 100))
                
                # 2. Извлекаем и преобразуем mode
                mode_val_raw = config.get('mode')
                if mode_val_raw is not None:
                    mode_val = int(mode_val_raw)
                else:
                    # Если 'mode' не задан, вычисляем среднее (min_val и max_val теперь гарантированно int)
                    mode_val = (min_val + max_val) // 2
                    
                # Дополнительная защита: mode_val не должен выходить за min/max
                mode_val = max(min_val, min(max_val, mode_val))

            except (ValueError, TypeError) as e:
                # Фолбек на случай, если пользователь ввел нечисловые данные
                print(f"Warning: Invalid number in config for {param_name}. Falling back to default: {e}")
                min_val, max_val, mode_val = 0, 100, 50
            # ----------------------------------------------------
            
            # Получаем описания значений
            descriptions_raw = config.get('descriptions', {})
            descriptions = {}

            for k, v in descriptions_raw.items():
                try:
                    descriptions[int(k)] = v
                except (ValueError, TypeError):
                    print(f"Warning: description key '{k}' is not a number — skipping.")
            
            # Генерируем случайное значение
            # Теперь min_val, mode_val, max_val гарантированно являются int
            random_value = self._generate_weighted_random(min_val, mode_val, max_val)
            
            # Определяем описание на основе сгенерированного значения
            description = self._get_value_description(random_value, descriptions)
            
            generated_params[param_name] = {
                'value': random_value,
                'description': description,
                'raw_config': config
            }
        
        return generated_params
    
    def _generate_weighted_random(self, min_val: int, mode_val: int, max_val: int) -> int:
        """
        Генерирует случайное значение с весами в пользу модального значения
        """
        # Создаем взвешенное распределение
        weights = []
        values = []
        
        # min_val, max_val и mode_val гарантированно int
        # Защита от некорректных границ, хотя это должно быть обработано выше
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        mode_val = max(min_val, min(max_val, mode_val))

        # Добавляем больше веса около модального значения
        for val in range(min_val, max_val + 1):
            # Вес уменьшается по мере удаления от моды
            # val - int, mode_val - int. Ошибка здесь больше не должна возникать.
            distance = abs(val - mode_val) 
            weight = max(1, 10 - distance)  
            weights.append(weight)
            values.append(val)
        
        # ... (Остальная часть метода без изменений)
        total_weight = sum(weights)
        if total_weight == 0:
             return mode_val
             
        random_weight = random.uniform(0, total_weight)
        
        cumulative_weight = 0
        for i, weight in enumerate(weights):
            cumulative_weight += weight
            if random_weight <= cumulative_weight:
                return values[i]
        
        return mode_val
    
    def _get_value_description(self, 
                               value: int, 
                               descriptions: Dict[int, str]) -> str:
        """
        Определяет описание значения на основе сгенерированного числа
        """
        if not descriptions:
            return f"Значение: {value}"
        
        # Находим ближайшее описание
        closest_key = min(descriptions.keys(), key=lambda k: abs(k - value))
        return descriptions[closest_key]
    
    def regenerate_ability_description(self, ability_index: int, concept: str) -> Dict[str, Any]:
        """
        Перегенерирует описание конкретной способности
        """
        if 0 <= ability_index < len(self.generated_abilities):
            ability = self.generated_abilities[ability_index]
            
            # Перегенерируем описание с теми же параметрами

            keywords = ability.get('keywords', '')

            new_description = self.llm_client.generate_ability_description(
                concept, 
                ability['parameters'],
                keywords
            )
            
            if new_description:
                ability['name'] = new_description['name']
                ability['description'] = new_description['description']
                return ability
            
        return {}
    
    def generate_character_summary(self, concept: str) -> str:
        """
        Генерирует общее описание персонажа
        """
        if not self.generated_abilities:
            return "Способности еще не сгенерированы"
        
        summary = self.llm_client.generate_character_summary(concept, self.generated_abilities)
        
        if summary:
            return summary
        else:
            # Фолбек описание
            return f"Персонаж с концепцией '{concept}' обладает {len(self.generated_abilities)} способностями, каждая из которых отражает ключевые аспекты его натуры."
    
    def get_ability_preview(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Показывает предварительный просмотр способности без обращения к LLM
        """
        parameters = self._generate_random_parameters(config.get('parameters', {}))
        
        preview = {
            'parameters': parameters,
            'concept_preview': 'Предварительный просмотр - описание будет сгенерировано при финальной генерации'
        }
        
        return preview