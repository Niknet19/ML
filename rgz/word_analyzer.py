import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.feature_extraction.text import TfidfVectorizer

# -----------------------------
# 1. Загрузка данных
# -----------------------------
with open("news_articles.json", "r", encoding="utf-8") as f:
    data = json.load(f)

articles = data["articles"]
df = pd.DataFrame(articles)

# Объединяем title + keyword для анализа
df["text"] = df["title"] + " " + df["keyword"]

# -----------------------------
# 2. TF-IDF анализ
# -----------------------------
TOP_N = 20  # количество топ-слов/выражений

tfidf = TfidfVectorizer(
    stop_words="english",
    max_features=1000,
    ngram_range=(1, 2)  # учитываем слова и биграммы
)

tfidf_matrix = tfidf.fit_transform(df["text"])
feature_names = tfidf.get_feature_names_out()

# Усреднённый TF-IDF по всем статьям
tfidf_scores = tfidf_matrix.mean(axis=0).A1

tfidf_df = pd.DataFrame({
    "term": feature_names,
    "score": tfidf_scores
}).sort_values(by="score", ascending=False)

# Топ-N терминов
top_terms = tfidf_df.head(TOP_N)
print(f"Топ-{TOP_N} терминов по TF-IDF:")
print(top_terms)

# -----------------------------
# 3. Визуализация популярности слов
# -----------------------------
sns.set(style="whitegrid")
plt.figure(figsize=(10, 6))
sns.barplot(x="score", y="term", data=top_terms, palette="viridis")
plt.title(f"Топ-{TOP_N} популярных слов и выражений на AI тематику")
plt.xlabel("Средний TF-IDF")
plt.ylabel("Слово/Выражение")
plt.tight_layout()
plt.show()
