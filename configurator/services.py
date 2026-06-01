import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from django.core.cache import cache
from .models import Component, Category


def get_usd_to_rub_rate():
    """Получает актуальный курс USD -> RUB через ExchangeRate-API."""
    cached_rate = cache.get('usd_rub_rate')
    if cached_rate:
        return cached_rate

    try:
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=2
        )
        data = response.json()
        rate = data['rates']['RUB']
        cache.set('usd_rub_rate', rate, timeout=3600)
        return rate
    except Exception:
        return 90.0


def convert_to_rub(price_usd):
    """Конвертирует цену из USD в RUB."""
    rate = get_usd_to_rub_rate()
    return round(float(price_usd) * rate, 2)


def check_compatibility(build):
    """
    Проверяет совместимость комплектующих в сборке.
    Возвращает список предупреждений.
    """
    from .models import CompatibilityRule

    warnings = []
    components = list(build.components.select_related('category').all())
    rules = CompatibilityRule.objects.select_related('category_a', 'category_b').all()

    for rule in rules:
        components_a = [c for c in components if c.category == rule.category_a]
        components_b = [c for c in components if c.category == rule.category_b]

        if not components_a or not components_b:
            continue

        for comp_a in components_a:
            for comp_b in components_b:
                val_a = comp_a.specs.get(rule.spec_key)
                val_b = comp_b.specs.get(rule.spec_key)

                if val_a and val_b and val_a != val_b:
                    warnings.append({
                        'rule': rule.name,
                        'message': (
                            f'Несовместимость: {comp_a} ({val_a}) '
                            f'и {comp_b} ({val_b}). {rule.description}'
                        ),
                        'component_a': str(comp_a),
                        'component_b': str(comp_b),
                    })

    return warnings


def get_build_price_chart(build):
    """Генерирует круговую диаграмму стоимости компонентов сборки в рублях."""
    rate = get_usd_to_rub_rate()
    components = build.components.select_related('category').all()

    if not components:
        return None

    labels = [str(c) for c in components]
    values = [round(float(c.price_usd) * rate, 2) for c in components]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo='label+percent',
    )])

    fig.update_layout(
        title='Распределение стоимости компонентов (₽)',
        showlegend=True,
        height=400,
        margin=dict(t=50, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def get_analytics_charts():
    """Генерирует графики для страницы аналитики в рублях."""
    rate = get_usd_to_rub_rate()
    components = Component.objects.select_related('category').all()

    if not components:
        return None, None

    data = [
        {
            'category': c.category.name,
            'price_rub': round(float(c.price_usd) * rate, 2),
            'brand': c.brand,
            'name': str(c),
        }
        for c in components
    ]
    df = pd.DataFrame(data)

    avg_by_category = df.groupby('category')['price_rub'].mean().reset_index()
    fig1 = px.bar(
        avg_by_category,
        x='category',
        y='price_rub',
        title='Средняя цена компонентов по категориям (₽)',
        labels={'category': 'Категория', 'price_rub': 'Средняя цена (₽)'},
        color='category',
    )
    fig1.update_layout(
        height=400,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    avg_by_brand = df.groupby('brand')['price_rub'].mean().reset_index()
    avg_by_brand = avg_by_brand.sort_values('price_rub', ascending=False).head(10)
    fig2 = px.bar(
        avg_by_brand,
        x='brand',
        y='price_rub',
        title='Средняя цена по производителям (₽)',
        labels={'brand': 'Производитель', 'price_rub': 'Средняя цена (₽)'},
        color='price_rub',
        color_continuous_scale='Blues',
    )
    fig2.update_layout(
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return (
        fig1.to_html(full_html=False, include_plotlyjs='cdn'),
        fig2.to_html(full_html=False, include_plotlyjs=False),
    )