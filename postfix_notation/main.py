import sys


def parse_number(token):
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return None


def calculate(expression):
    tokens = expression.strip().split()
    if not tokens:
        raise ValueError("Вы передали пустое выражение.")

    stack = []
    supported_operators = {"+", "-", "*", "/", "~", "!"}

    for token in tokens:
        num = parse_number(token)
        if num is not None:
            stack.append(num)
        elif token in supported_operators:
            if len(stack) < 2:
                raise ValueError(
                    f"Для выполнения операции '{token}' в стеке должно быть хотя бы два числа. "
                    f"Сейчас в стеке: {stack}"
                )

            y = stack.pop()
            x = stack.pop()

            if token == "+":
                stack.append(x + y)
            elif token == "-":
                stack.append(x - y)
            elif token == "*":
                stack.append(x * y)
            elif token == "/":
                if y == 0:
                    raise ZeroDivisionError("Попытка деления на ноль.")
                res = x / y
                if res.is_integer():
                    res = int(res)
                stack.append(res)
            elif token == "~":
                if x != 0 and y != 0:
                    res = abs(x - y)
                    stack.append(res)
                else:
                    total_sum = sum(stack) + x + y
                    res = total_sum ** 2
                    stack.clear()
                    stack.append(res)
            elif token == "!":
                    stack.append(x**y)
        else:
            raise ValueError(f"Неизвестный токен '{token}'.")

        print(f"Токен: {token:<3} | Стек: {stack}")

    if len(stack) != 1:
        raise ValueError(
            f"После вычисления в стеке осталось несколько значений: {stack}. "
            "Проверьте правильность выражения."
        )

    return stack[0]


def main():
    if len(sys.argv) < 2:
        print("Ошибка: не передано выражение для вычисления.")
        print('Пример запуска: python main.py "3 0 4 ~ 2 ~"')
        sys.exit(1)

    if len(sys.argv) > 2:
        print("Ошибка: передано некорректное выражение для вычисления.")
        print("Похоже, вы забыли взять выражение в кавычки.")
        print('Пример запуска: python main.py "3 0 4 ~ 2 ~"')
        sys.exit(1)

    expression = sys.argv[1]

    try:
        result = calculate(expression)
        print(f"{expression} = {result}")
    except ZeroDivisionError as err:
        print(f"Математическая ошибка: {err}")
        sys.exit(1)
    except ValueError as err:
        print(f"Ошибка вычисления: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"Непредвиденная ошибка: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
