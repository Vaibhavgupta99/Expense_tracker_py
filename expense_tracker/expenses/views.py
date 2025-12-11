import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from collections import defaultdict
from django.conf import settings
import os
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Expense
from .forms import ExpenseForm, ProfileUpdateForm
from django.db.models import Sum, Max, Avg
from datetime import date, timedelta



@login_required
def dashboard(request):
    # --- Handle Monthly Budget Form Submission ---
    if request.method == "POST" and 'budget' in request.POST:
        try:
            new_budget = float(request.POST['budget'])
            request.user.monthly_budget = new_budget
            request.user.save()
        except ValueError:
            pass  # silently fail or add logging/validation

        return redirect('dashboard')

    # --- Fetch Expenses ---
    expenses = Expense.objects.filter(user=request.user)

    # --- Filtering ---
    category = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    sort_by = request.GET.get('sort_by')

    if category:
        expenses = expenses.filter(category__icontains=category)

    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])

    # --- Sorting ---
    if sort_by in ['amount', '-amount', 'date', '-date']:
        expenses = expenses.order_by(sort_by)
    else:
        expenses = expenses.order_by('-date')

    # --- Statistics ---
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    highest_expense = expenses.aggregate(Max('amount'))['amount__max'] or 0
    last_30_days = date.today() - timedelta(days=30)
    avg_daily_expense = (
        expenses.filter(date__gte=last_30_days)
        .aggregate(Avg('amount'))['amount__avg'] or 0
    )

    # --- Monthly Budget ---
    monthly_budget = request.user.monthly_budget or 0
    remaining_budget = monthly_budget - total_expense

    # --- Charts Directory ---
    charts_dir = os.path.join(settings.STATICFILES_DIRS[0], 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    # --- Weekly Spending Chart ---
    today = timezone.now().date()
    week_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    week_days_str = [d.strftime('%a') for d in week_days]
    daily_totals = defaultdict(float)

    for e in expenses:
        if e.date in week_days:
            daily_totals[e.date.strftime('%a')] += float(e.amount)

    plt.figure(figsize=(6, 6))
    plt.plot(week_days_str, [daily_totals.get(day, 0) for day in week_days_str], marker='o')
    plt.title("Weekly Spending Trend")
    plt.tight_layout()
    weekly_chart_path = os.path.join(charts_dir, 'weekly.png')
    plt.savefig(weekly_chart_path)
    plt.close()

    # --- Category Chart ---
    category_totals = defaultdict(float)
    for e in expenses:
        category_totals[e.category] += float(e.amount)

    if category_totals:
        plt.figure(figsize=(4, 4))
        plt.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%',
                startangle=90, wedgeprops={'width': 0.4})
        plt.title("Expenses by Category")
        plt.tight_layout()
        category_chart_path = os.path.join(charts_dir, 'category.png')
        plt.savefig(category_chart_path)
        plt.close()
    else:
        category_chart_path = None
        weekly_chart_path = None

    # --- Render Context ---
    context = {
        'expenses': expenses,
        'total_expense': total_expense,
        'highest_expense': highest_expense,
        'avg_daily_expense': round(avg_daily_expense, 2),
        'weekly_chart': 'charts/weekly.png' if weekly_chart_path else None,
        'category_chart': 'charts/category.png' if category_chart_path else None,        
        'remaining_budget': remaining_budget,
        'monthly_budget': monthly_budget,
        'today': date.today().strftime('%b. %d, %Y'),
    }
    return render(request, 'expenses/dashboard.html', context)


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'expenses/add_expense.html', {'form': form})

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/edit_expense.html', {'form': form})

# @login_required
# def delete_expense(request, expense_id):
#     expense = get_object_or_404(Expense, id=expense_id, user=request.user)
#     if request.method == 'POST':
#         expense.delete()
#         return redirect('dashboard')
#     return render(request, 'expenses/confirm_delete.html', {'expense': expense})

#@require_POST
@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    expense.delete()
    return redirect('dashboard')
