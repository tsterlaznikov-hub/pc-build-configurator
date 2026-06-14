import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from django.core.cache import cache
from .models import Component, Category


def get_usd_to_rub_rate():
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
    rate = get_usd_to_rub_rate()
    return round(float(price_usd) * rate, 2)


def check_compatibility(build):
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
    rate = get_usd_to_rub_rate()
    components = build.components.select_related('category').all()

    if not components:
        return None

    grouped = {}
    for c in components:
        name = str(c)
        price = round(float(c.price_usd) * rate, 2)
        if name in grouped:
            grouped[name]['value'] += price
            grouped[name]['count'] += 1
        else:
            grouped[name] = {'value': price, 'count': 1}

    labels = []
    values = []
    for name, data in grouped.items():
        if data['count'] > 1:
            labels.append(f"{name} (x{data['count']})")
        else:
            labels.append(name)
        values.append(data['value'])

    if len(labels) > 8:
        top_8_values = values[:8]
        top_8_labels = labels[:8]
        other_value = sum(values[8:])
        top_8_values.append(other_value)
        top_8_labels.append(f"Другие ({len(labels) - 8} шт.)")
        values = top_8_values
        labels = top_8_labels

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.35,
        textinfo='label+percent',
        textposition='auto',
        insidetextorientation='horizontal',
    )])

    fig.update_traces(
        textfont_size=11,
        automargin=True,
        sort=False
    )

    fig.update_layout(
        title='Распределение стоимости компонентов (₽)',
        showlegend=False,
        height=450,
        margin=dict(t=50, b=20, l=20, r=20),
        annotations=[dict(
            text=f'Всего: {components.count()} комп.',
            x=0.5, y=0.5, font_size=12, showarrow=False
        )]
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')


def get_analytics_charts():
    cache_key = 'analytics_charts'
    cached_charts = cache.get(cache_key)
    if cached_charts:
        return cached_charts

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

    result = (
        fig1.to_html(full_html=False, include_plotlyjs='cdn'),
        fig2.to_html(full_html=False, include_plotlyjs=False),
    )

    cache.set(cache_key, result, 3600)
    return result