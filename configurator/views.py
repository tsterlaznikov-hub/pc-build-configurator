from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum

from .models import Category, Component, Build
from .forms import RegisterForm, BuildForm, ComponentFilterForm
from .services import (
    convert_to_rub,
    get_usd_to_rub_rate,
    check_compatibility,
    get_build_price_chart,
    get_analytics_charts,
)


def home(request):
    categories = Category.objects.annotate(component_count=Count('components'))
    public_builds = Build.objects.filter(
        is_public=True
    ).select_related('user').prefetch_related('components')[:6]
    rate = get_usd_to_rub_rate()

    context = {
        'categories': categories,
        'public_builds': public_builds,
        'rate': rate,
    }
    return render(request, 'configurator/index.html', context)


def catalog(request):
    form = ComponentFilterForm(request.GET)
    components = Component.objects.select_related('category').all()

    categories = Category.objects.all()
    category_choices = [('', 'Все категории')] + [
        (c.id, c.name) for c in categories
    ]
    form.fields['category'].choices = category_choices

    if form.is_valid():
        category_id = form.cleaned_data.get('category')
        search = form.cleaned_data.get('search')
        sort = form.cleaned_data.get('sort')

        if category_id:
            components = components.filter(category_id=category_id)
        if search:
            components = components.filter(name__icontains=search) | \
                         components.filter(brand__icontains=search)
        if sort:
            components = components.order_by(sort)

    rate = get_usd_to_rub_rate()

    component_list = []
    for component in components:
        component_list.append({
            'obj': component,
            'price_rub': convert_to_rub(component.price_usd),
        })

    context = {
        'form': form,
        'component_list': component_list,
        'total_count': components.count(),
    }
    return render(request, 'configurator/catalog.html', context)


def component_detail(request, pk):
    component = get_object_or_404(Component, pk=pk)
    price_rub = convert_to_rub(component.price_usd)
    rate = get_usd_to_rub_rate()

    user_builds = []
    if request.user.is_authenticated:
        user_builds = Build.objects.filter(user=request.user)

    context = {
        'component': component,
        'price_rub': price_rub,
        'rate': rate,
        'user_builds': user_builds,
    }
    return render(request, 'configurator/component_detail.html', context)


@login_required
def add_to_build(request, component_pk):
    component = get_object_or_404(Component, pk=component_pk)

    if request.method == 'POST':
        build_id = request.POST.get('build_id')
        if build_id:
            build = get_object_or_404(Build, pk=build_id, user=request.user)
            build.components.add(component)
            messages.success(request, f'{component} добавлен в сборку «{build.name}»!')
        return redirect('component_detail', pk=component_pk)

    return redirect('component_detail', pk=component_pk)


@login_required
def remove_from_build(request, build_pk, component_pk):
    build = get_object_or_404(Build, pk=build_pk, user=request.user)
    component = get_object_or_404(Component, pk=component_pk)
    build.components.remove(component)
    messages.success(request, f'{component} удалён из сборки.')
    return redirect('build_detail', pk=build_pk)


@login_required
def my_builds(request):
    builds = Build.objects.filter(
        user=request.user
    ).prefetch_related('components').annotate(
        component_count=Count('components')
    )

    builds_with_price = []
    rate = get_usd_to_rub_rate()
    for build in builds:
        total_usd = build.total_price_usd()
        builds_with_price.append({
            'obj': build,
            'total_usd': total_usd,
            'total_rub': round(float(total_usd) * rate, 2),
        })

    context = {'builds_with_price': builds_with_price}
    return render(request, 'configurator/my_builds.html', context)


@login_required
def build_create(request):
    if request.method == 'POST':
        form = BuildForm(request.POST)
        if form.is_valid():
            build = form.save(commit=False)
            build.user = request.user
            build.save()
            messages.success(request, 'Сборка успешно создана!')
            return redirect('build_detail', pk=build.pk)
    else:
        form = BuildForm()

    return render(request, 'configurator/build_form.html', {'form': form, 'title': 'Новая сборка'})


@login_required
def build_edit(request, pk):
    build = get_object_or_404(Build, pk=pk, user=request.user)

    if request.method == 'POST':
        form = BuildForm(request.POST, instance=build)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сборка обновлена!')
            return redirect('build_detail', pk=build.pk)
    else:
        form = BuildForm(instance=build)

    return render(request, 'configurator/build_form.html', {'form': form, 'title': 'Редактировать сборку'})


@login_required
def build_delete(request, pk):
    build = get_object_or_404(Build, pk=pk, user=request.user)

    if request.method == 'POST':
        build.delete()
        messages.success(request, 'Сборка удалена.')
        return redirect('my_builds')

    return render(request, 'configurator/build_confirm_delete.html', {'build': build})


def build_detail(request, pk):
    build = get_object_or_404(Build, pk=pk)

    if not build.is_public and build.user != request.user:
        messages.error(request, 'У вас нет доступа к этой сборке.')
        return redirect('home')

    rate = get_usd_to_rub_rate()
    total_usd = build.total_price_usd()
    total_rub = round(float(total_usd) * rate, 2)
    compatibility_warnings = check_compatibility(build)
    chart_html = get_build_price_chart(build)

    context = {
        'build': build,
        'total_usd': total_usd,
        'total_rub': total_rub,
        'compatibility_warnings': compatibility_warnings,
        'chart_html': chart_html,
        'rate': rate,
    }
    return render(request, 'configurator/build_detail.html', context)


def analytics(request):
    chart1_html, chart2_html = get_analytics_charts()

    stats = Component.objects.aggregate(
        total_components=Count('id'),
        avg_price=Avg('price_usd'),
    )

    context = {
        'chart1_html': chart1_html,
        'chart2_html': chart2_html,
        'stats': stats,
        'categories_count': Category.objects.count(),
    }
    return render(request, 'configurator/analytics.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'configurator/register.html', {'form': form})


@login_required
def profile(request):
    builds_count = Build.objects.filter(user=request.user).count()
    public_builds_count = Build.objects.filter(
        user=request.user, is_public=True
    ).count()

    context = {
        'builds_count': builds_count,
        'public_builds_count': public_builds_count,
    }
    return render(request, 'configurator/profile.html', context)