import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Загружаем словари VADER
nltk.download('vader_lexicon')
from textblob import TextBlob

# -----------------------------
# 1. Загрузка данных
# -----------------------------
with open("news_articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Берём массив articles
articles = data["articles"]
df = pd.DataFrame(articles)

# Объединяем title + keyword для анализа текста
df["text"] = df["title"] + " " + df["keyword"]

sia = SentimentIntensityAnalyzer()

# -----------------------------
# 2. Определение бизнес-сферы
# -----------------------------

INDUSTRY_KEYWORDS = {
    "Менеджмент": ["management", "leadership", "strategy", "planning", "decision"],
    "Маркетинг": ["marketing", "ads", "promotion", "brand", "customer acquisition", "personalization"],
    "Поддержка клиентов": ["support", "customer service", "chatbot", "helpdesk", "CRM"],
    "Аналитика": ["analytics", "data", "insights", "forecasting", "analysis", "business intelligence", "predictive"]
}

def detect_industry(text):
    text = text.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                return industry
    return "Другое"

df["industry"] = df["text"].apply(detect_industry)

# -----------------------------
# 3. Анализ тональности
# -----------------------------
def get_sentiment(text):
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.0:
        return "Позитивный"
    elif compound <= 0.0:
        return "Негативный"

df["sentiment"] = df["text"].apply(get_sentiment)

# -----------------------------
# 4. TF-IDF анализ
# -----------------------------
tfidf = TfidfVectorizer(
    stop_words="english",
    max_features=1000,
    ngram_range=(1, 2)
)

tfidf_matrix = tfidf.fit_transform(df["text"])
feature_names = tfidf.get_feature_names_out()

tfidf_scores = tfidf_matrix.mean(axis=0).A1
tfidf_df = pd.DataFrame({
    "term": feature_names,
    "score": tfidf_scores
}).sort_values(by="score", ascending=False)

print("\nТоп-20 TF-IDF терминов:")
print(tfidf_df.head(20))

# -----------------------------
# 5. Классификация (Naive Bayes)
# -----------------------------
label_encoder = LabelEncoder()
df["industry_label"] = label_encoder.fit_transform(df["industry"])

X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["industry_label"], test_size=0.2, random_state=42
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(stop_words="english")),
    ("nb", MultinomialNB())
])

model.fit(X_train, y_train)
accuracy = model.score(X_test, y_test)
print(f"\nТочность классификации (Naive Bayes): {accuracy:.2f}")

# -----------------------------
# 6. Визуализация
# -----------------------------
sns.set(style="whitegrid")

# Активность по сферам
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x="industry", order=df["industry"].value_counts().index)
plt.title("Активность обсуждения LLM по бизнес-сферам")
plt.xlabel("Бизнес-сфера")
plt.ylabel("Количество публикаций")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# Тональность по сферам
plt.figure(figsize=(8, 5))
sns.countplot(data=df, x="industry", hue="sentiment")
plt.title("Тональность публикаций по бизнес-сферам")
plt.xlabel("Бизнес-сфера")
plt.ylabel("Количество публикаций")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# Общая тональность
plt.figure(figsize=(5, 4))
sns.countplot(data=df, x="sentiment")
plt.title("Общее распределение тональности")
plt.xlabel("Тональность")
plt.ylabel("Количество публикаций")
plt.tight_layout()
plt.show()

sample_texts = [
    # Позитивные тексты
    "AI improves customer support with chatbots and CRM automation",
    "Machine learning helps companies analyze marketing campaigns effectively",
    "LLM can optimize business strategy and decision making",
    "Data analytics and predictive AI are transforming financial analytics",
    "AI-powered personalization boosts customer engagement",

    # Негативные тексты
    "LLM often produces inaccurate responses, causing confusion among users",
    "AI-driven marketing campaigns fail to reach target audience",
    "Customer service chatbots frequently misunderstand client requests",
    "Predictive analytics made wrong forecasts leading to financial losses",
    "AI implementation in business caused more problems than it solved"
]

# Используем обученную модель для предсказания бизнес-сферы
predicted_labels = model.predict(sample_texts)
predicted_industries = label_encoder.inverse_transform(predicted_labels)

# Определяем тональность текстов
sample_sentiments = [get_sentiment(text) for text in sample_texts]

# Вывод результатов
print(f"\n{'Текст':<70} {'Сфера':<20} {'Тональность':<10}")
print("-"*100)
for text, industry, sentiment in zip(sample_texts, predicted_industries, sample_sentiments):
    print(f"{text:<70} {industry:<20} {sentiment:<10}")
