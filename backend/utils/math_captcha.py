"""
数学验证码生成器
用于创作者身份验证
"""
import random


def generate_math_question():
    """
    生成简单的数学题
    返回: (问题字符串, 答案整数)
    """
    operators = ['+', '-', '*']
    operator = random.choice(operators)

    if operator == '+':
        a = random.randint(1, 50)
        b = random.randint(1, 50)
        answer = a + b
        question = f"{a} + {b} = ?"
    elif operator == '-':
        a = random.randint(20, 100)
        b = random.randint(1, 19)
        answer = a - b
        question = f"{a} - {b} = ?"
    else:  # *
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        answer = a * b
        question = f"{a} × {b} = ?"

    return question, answer
