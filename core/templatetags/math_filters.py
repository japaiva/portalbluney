# core/templatetags/math_filters.py

from django import template
from decimal import Decimal, DivisionByZero

register = template.Library()

@register.filter
def div(value, arg):
    """
    Divide o valor pelo argumento
    Uso: {{ total_valor|div:vendas.count }}
    """
    try:
        # Converter para Decimal para maior precisão
        dividend = Decimal(str(value)) if value is not None else Decimal('0')
        divisor = Decimal(str(arg)) if arg is not None else Decimal('0')
        
        # Evitar divisão por zero
        if divisor == 0:
            return 0
            
        result = dividend / divisor
        # Retornar como float para compatibilidade com floatformat
        return float(result)
        
    except (ValueError, TypeError, DivisionByZero):
        return 0

@register.filter  
def multiply(value, arg):
    """
    Multiplica o valor pelo argumento
    Uso: {{ quantidade|multiply:preco }}
    """
    try:
        factor1 = Decimal(str(value)) if value is not None else Decimal('0')
        factor2 = Decimal(str(arg)) if arg is not None else Decimal('0')
        
        result = factor1 * factor2
        return float(result)
        
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """
    Subtrai o argumento do valor
    Uso: {{ total|subtract:desconto }}
    """
    try:
        minuend = Decimal(str(value)) if value is not None else Decimal('0')
        subtrahend = Decimal(str(arg)) if arg is not None else Decimal('0')
        
        result = minuend - subtrahend
        return float(result)
        
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Calcula a porcentagem
    Uso: {{ vendas_mes|percentage:vendas_total }}
    """
    try:
        part = Decimal(str(value)) if value is not None else Decimal('0')
        whole = Decimal(str(total)) if total is not None else Decimal('0')
        
        if whole == 0:
            return 0
            
        result = (part / whole) * 100
        return float(result)
        
    except (ValueError, TypeError, DivisionByZero):
        return 0

@register.filter
def format_currency(value):
    """
    Formata valor como moeda brasileira
    Uso: {{ valor|format_currency }}
    """
    try:
        num_value = float(value) if value is not None else 0
        return f"R$ {num_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"

@register.filter
def safe_divide(value, arg):
    """
    Divisão segura que retorna 0 se divisor for 0
    Uso: {{ total|safe_divide:count }}
    """
    try:
        dividend = float(value) if value is not None else 0
        divisor = float(arg) if arg is not None else 0
        
        if divisor == 0:
            return 0
            
        return dividend / divisor
        
    except (ValueError, TypeError):
        return 0