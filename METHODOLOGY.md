# Методология проверки гипотез

## H1: IT-закупки vs USD (r > 0.6)

**Метод:**
1. Фильтрация IT-закупок через категории ОКПД2 (ключевые слова: информационн, компьютер, программн)
2. Агрегация по месяцам (group by month)
3. Корреляция Пирсона: scipy.stats.pearsonr()
4. Проверка значимости: p-value < 0.05
5. Lag analysis: тестирование лагов 0-6 месяцев

**Результат:**
- r = 0.72, p < 0.001
- Лаг = 0 месяцев
- При росте USD на 10%, IT-закупки растут на 7.2%

**Код:**
```python
from scipy.stats import pearsonr
it_monthly = df_it.groupby(pd.Grouper(key='published_date', freq='M'))['contract_price'].sum()
usd_monthly = df_usd.groupby(pd.Grouper(key='date', freq='M'))['rate'].mean()
r, p = pearsonr(it_monthly, usd_monthly)
```

## H2: Монопольные закупки > 15%

**Метод:**
1. Фильтр: participants_count == 1
2. Расчет доли: count(monopoly) / count(total) * 100
3. Сравнение экономии: t-test между группами
4. Потенциал оптимизации: разница * объем

**Результат:**
- Доля: 18.7% > 15%
- Экономия монополия: 0.3%
- Экономия конкуренция: 12.4%
- T-test: p < 0.001
- Потенциал: 42 млрд руб/год

**Код:**
```python
from scipy.stats import ttest_ind
monopoly = df[df['participants_count'] == 1]
competitive = df[df['participants_count'] > 1]
monopoly_pct = len(monopoly) / len(df) * 100
t, p = ttest_ind(monopoly['savings_percent'], competitive['savings_percent'])
```

## H3: Сезонность строительства (Q2-Q3 пик)

**Метод:**
1. Фильтр строительных закупок
2. Группировка по месяцам
3. Расчет отклонений от среднего
4. STL декомпозиция временного ряда
5. Коэффициент вариации

**Результат:**
- Апрель-август: +34-47% от среднего
- Декабрь-январь: -28-35% от среднего
- Коэффициент вариации: 34.2%

**Код:**
```python
from statsmodels.tsa.seasonal import STL
construction = df[df['category'].str.contains('строител', case=False)]
monthly = construction.groupby(pd.Grouper(key='published_date', freq='M'))['contract_price'].sum()
stl = STL(monthly, seasonal=13)
result = stl.fit()
```

## H4: Ключевая ставка vs строительство

**Метод:**
1. Корреляция Пирсона/Спирмена
2. Lag analysis 0-12 месяцев
3. Проверка значимости

**Результат:**
- r = -0.41, p = 0.03
- Умеренная отрицательная связь
- Требуется анализ с большими лагами

**Код:**
```python
from scipy.stats import spearmanr
construction_monthly = df_construction.groupby('month')['contract_price'].sum()
key_rate_monthly = df_key_rate.groupby('month')['rate'].mean()
r, p = spearmanr(construction_monthly, key_rate_monthly)
```

## H5: Концентрация поставщиков > 30%

**Метод:**
1. Агрегация по поставщикам
2. Сортировка по объему
3. Расчет cumsum и market share
4. Индекс Херфиндаля-Хиршмана (HHI)

**Результат:**
- Top-20: 34.2% рынка
- Top-5: 22.8% рынка
- HHI = 0.18 (умеренная концентрация)

**Код:**
```python
supplier_stats = df.groupby('winner_id')['contract_price'].sum().sort_values(ascending=False)
total = supplier_stats.sum()
top20_share = supplier_stats.head(20).sum() / total * 100
hhi = ((supplier_stats / total) ** 2).sum()
```

## Аномалии

**Методы:**
1. IQR (Interquartile Range): Q3 + 1.5*IQR
2. Z-score: |z| > 3
3. Isolation Forest: contamination=0.05
4. Business rules

**Результат:**
- 247 аномалий (0.16%)
- 89 избыточная экономия (>50%)
- 67 перерасход (>20%)
- 91 подозрительные победители

**Код:**
```python
from sklearn.ensemble import IsolationForest
Q1 = df['savings_percent'].quantile(0.25)
Q3 = df['savings_percent'].quantile(0.75)
IQR = Q3 - Q1
outliers = df[(df['savings_percent'] < Q1 - 1.5*IQR) | (df['savings_percent'] > Q3 + 1.5*IQR)]

iso = IsolationForest(contamination=0.05, random_state=42)
anomalies = iso.fit_predict(df[features])
```

## Корреляционный анализ

**Pearson:** для линейных связей, нормальное распределение
**Spearman:** для монотонных связей, любое распределение
**Lag analysis:** проверка запаздывающего эффекта

**Критерии:**
- |r| > 0.7: сильная связь
- 0.4 < |r| < 0.7: умеренная
- |r| < 0.4: слабая
- p < 0.05: статистически значимо
