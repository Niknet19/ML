import requests
from bs4 import BeautifulSoup
import json
import time
import random

class NewsParser:
    def __init__(self):
        # Создаем сессию для сохранения состояния и заголовков
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self.articles = []
        
    def fetch_page(self, url, max_retries=1):
        """Загружает страницу с повторными попытками"""
        for attempt in range(max_retries):
            try:
                # Раздельные таймауты: 5 сек на подключение, 10 на получение данных
                response = self.session.get(url, timeout=(5, 10))
                response.raise_for_status()  # Проверка на HTTP ошибки (4xx, 5xx)
                return response
            except requests.exceptions.RequestException as e:
                print(f"    Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                if attempt < max_retries - 1:
                    # Увеличиваем паузу с каждой неудачной попыткой
                    sleep_time = random.uniform(2, 4) * (attempt + 1)
                    print(f"    Жду {sleep_time:.1f} сек перед повторной попыткой...")
                    time.sleep(sleep_time)
        return None

    def parse_techcrunch(self, keyword, max_pages=3):
        """Парсит TechCrunch по шаблону: https://techcrunch.com/page/3/?s=Ai+in+marketing"""
        print(f"\n=== Парсим TechCrunch по ключевому слову: '{keyword}' ===")
        
        base_url = "https://techcrunch.com"
        articles_found = 0
        
        for page in range(1, max_pages + 1):
            # Формируем URL с учетом страницы и ключевого слова
            search_url = f"{base_url}/page/{page}/?s={keyword.replace(' ', '+')}"
            print(f"  Страница {page}: {search_url}")
            
            response = self.fetch_page(search_url)
            if not response:
                print(f"  Не удалось загрузить страницу {page}, пропускаем...")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # TechCrunch: ищем заголовки статей
            # Основной селектор для заголовков на странице поиска
            title_selectors = [
                'h2.post-block__title a',  # Основной селектор для новостей
                'a.post-block__title__link',  # Альтернативный селектор
                'h3 a',  # Общий селектор на случай изменений
            ]
            
            page_articles = 0
            for selector in title_selectors:
                articles_elements = soup.select(selector)
                if articles_elements:
                    for element in articles_elements:
                        title = element.get_text(strip=True)
                        url = element.get('href', '')
                        
                        if title and url:
                            # Если ссылка относительная, делаем её абсолютной
                            if url.startswith('/'):
                                url = base_url + url
                            
                            self.articles.append({
                                'source': 'TechCrunch',
                                'title': title,
                                'url': url,
                                'keyword': keyword,
                                'page': page
                            })
                            page_articles += 1
                    break  # Выходим после успешного использования селектора
            
            print(f"  Найдено статей на странице: {page_articles}")
            articles_found += page_articles
            
            # Пауза между страницами, чтобы не перегружать сервер
            if page < max_pages:
                sleep_time = random.uniform(1, 3)
                time.sleep(sleep_time)
        
        print(f"Всего найдено статей в TechCrunch: {articles_found}")
        return articles_found

    def run(self, keywords, pages_per_site=3):
        """Основной метод для запуска парсинга"""
        print("=" * 60)
        print("НАЧИНАЕМ ПАРСИНГ НОВОСТНЫХ САЙТОВ")
        print("=" * 60)
        
        total_articles = 0
        
        for keyword in keywords:
            print(f"\n>>> Обрабатываем ключевое слово: '{keyword}'")
            
            # Парсим TechCrunch
            tc_count = self.parse_techcrunch(keyword, max_pages=pages_per_site)
            total_articles += tc_count
            
            # Пауза между разными сайтами
            #print("\n  Пауза между сайтами...")
            #time.sleep(random.uniform(3, 5))
            
            # Парсим Forbes
            ##fb_count = self.parse_forbes(keyword, max_pages=pages_per_site)
            ##total_articles += fb_count
            
            # Большая пауза перед следующим ключевым словом
            print("\n  Пауза перед следующим ключевым словом...")
            time.sleep(random.uniform(1, 2))
        
        print(f"\n{'='*60}")
        print(f"ПАРСИНГ ЗАВЕРШЕН!")
        print(f"Всего собрано статей: {total_articles}")
        print(f"{'='*60}")
        
        return self.articles

    def save_to_json(self, filename="news_articles_common.json"):
        """Сохраняет результаты в JSON файл"""
        if not self.articles:
            print("Нет данных для сохранения")
            return
        
        # Создаем структурированные данные
        output_data = {
            "metadata": {
                "total_articles": len(self.articles),
                "keywords_used": list(set([article['keyword'] for article in self.articles])),
                "sources": list(set([article['source'] for article in self.articles])),
                "parsed_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "articles": self.articles
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nРезультаты сохранены в файл: {filename}")
        
        # Выводим статистику
        print("\nСТАТИСТИКА:")
        print(f"  Всего статей: {len(self.articles)}")
        
        sources_count = {}
        for article in self.articles:
            source = article['source']
            sources_count[source] = sources_count.get(source, 0) + 1
        
        for source, count in sources_count.items():
            print(f"  {source}: {count} статей")

def main():
    """Пример использования парсера"""
    

    KEYWORDSCOMMON = [
    "AI", "ai", "LLM", "Gpt", "ChatGpt", "Artificail intelligance",
    ]

    # Настройки парсинга
    KEYWORDS = [
    "AI",
    "Machine Learning",
    "LLM",
    "Chatgpt",
    # Общее и менеджмент
    "AI management",
    "artificial intelligence leadership",
    "AI strategy business",
    "AI decision making",
    # Маркетинг
    "AI marketing",
    "machine learning advertising",
    "AI customer engagement",
    "AI personalization marketing",
    # Поддержка клиентов
    "AI customer service",
    "AI CRM",
    "chatbot customer support",
    "AI helpdesk",
    # Аналитика
    "AI analytics",
    "machine learning data analysis",
    "AI business intelligence",
    "predictive analytics AI",
]
    
    PAGES_PER_SITE = 20  # Количество страниц для парсинга на каждом сайте
    
    # Создаем парсер и запускаем
    parser = NewsParser()
    
    # Запускаем парсинг
    articles = parser.run(KEYWORDSCOMMON, pages_per_site=PAGES_PER_SITE)
    
    # Сохраняем результаты
    parser.save_to_json()
    
    # Показываем примеры найденных статей
    if articles:
        print(f"\n{'='*60}")
        print("ПЕРВЫЕ 5 НАЙДЕННЫХ СТАТЕЙ:")
        print('='*60)
        for i, article in enumerate(articles[:5], 1):
            print(f"\n{i}. [{article['source']}]")
            print(f"   Заголовок: {article['title']}")
            print(f"   Ключ. слово: {article['keyword']}")
            print(f"   Страница: {article['page']}")

if __name__ == "__main__":
    main()