import sys
import pytest
from main import parse_number, calculate, main


# Тестирование парсинга чисел 

@pytest.mark.parametrize("token, expected", [
    ("42", 42),
    ("-15", -15),
    ("3.14", 3.14),
    ("-0.5", -0.5),
    ("abc", None),
    ("+", None),
])
def test_parse_number(token, expected):
    assert parse_number(token) == expected


# Тестирование вычислений и базовых операций 

@pytest.mark.parametrize("expression, expected", [
    ("2 3 +", 5),
    ("10 4 -", 6),
    ("5 12 -", -7),
    ("3 4 *", 12),
    ("8 2 /", 4),
    ("7 2 /", 3.5),
    ("-6 2 /", -3),
])
def test_calculate_basic_operations(expression, expected):
    assert calculate(expression) == expected


# Тестирование оператора

def test_tilde_without_zero():
    # Модуль разницы: |49 - 2| = 47
    assert calculate("49 2 ~") == 47
    # Модуль разницы с отрицательным числом: |-7 - 4| = 11
    assert calculate("2 9 - 4 ~") == 11
    # Проверка, что дно стека не затронуто
    assert calculate("100 2 9 - 4 ~ +") == 111


def test_tilde_with_zero():
    # Сумма 3 + 0 + 4 = 7, в квадрате = 49
    assert calculate("3 0 4 ~") == 49
    # Оба операнда нули: (0 + 0)^2 = 0
    assert calculate("0 0 ~") == 0


def test_task_examples():
    # Примеры строго из условия задачи
    assert calculate("3 0 4 ~ 2 ~") == 47
    assert calculate("2 2 + 4 - 4 ~ 2 3 * +") == 22


# Тестирование ошибок вычисления 

def test_calculate_empty_expression():
    with pytest.raises(ValueError, match="пустое выражение"):
        calculate("   ")


def test_calculate_not_enough_operands():
    with pytest.raises(ValueError, match="должно быть хотя бы два числа"):
        calculate("5 +")


def test_calculate_unknown_token():
    with pytest.raises(ValueError, match="Неизвестный токен"):
        calculate("2 3 foo +")


def test_calculate_division_by_zero():
    with pytest.raises(ZeroDivisionError, match="деления на ноль"):
        calculate("10 0 /")


def test_calculate_leftover_elements():
    with pytest.raises(ValueError, match="осталось несколько значений"):
        calculate("2 3 4 +")


# Тестирование интерфейса 

def test_main_success(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "3 0 4 ~ 2 ~"])
    main()
    captured = capsys.readouterr()
    assert "3 0 4 ~ 2 ~ = 47" in captured.out


def test_main_no_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "не передано выражение" in captured.out


def test_main_too_many_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "3", "0", "4"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "забыли взять выражение в кавычки" in captured.out


def test_main_handles_division_by_zero(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "5 0 /"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Математическая ошибка" in captured.out


def test_main_handles_value_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "bad_token"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Ошибка вычисления" in captured.out


def test_main_handles_unexpected_exception(monkeypatch, capsys):
    # Симулируем непредвиденную ошибку
    def mock_broken_calc(expr):
        raise RuntimeError("Что-то пошло не так внутри системы")

    monkeypatch.setattr("main.calculate", mock_broken_calc)
    monkeypatch.setattr(sys, "argv", ["main.py", "1 1 +"])

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Непредвиденная ошибка" in captured.out